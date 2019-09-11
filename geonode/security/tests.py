# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from geonode.tests.base import GeoNodeBaseTestSupport

import os
import json
import base64
import urllib2
import logging
import gisdata
import contextlib

from django.conf import settings
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from tastypie.test import ResourceTestCaseMixin
from django.contrib.auth import get_user_model
from guardian.shortcuts import get_anonymous_user, assign_perm, remove_perm
from geonode import geoserver
from geonode.base.populate_test_data import all_public
from geonode.people.models import Profile
from geonode.people.utils import get_valid_user
from geonode.layers.models import Layer
from geonode.groups.models import Group
from geonode.utils import check_ogc_backend
from geonode.tests.utils import check_layer
from geonode.decorators import on_ogc_backend
from geonode.geoserver.helpers import gs_slurp
from geonode.geoserver.upload import geoserver_upload
from geonode.layers.populate_layers_data import create_layer_data

from .utils import (purge_geofence_all,
                    get_users_with_perms,
                    get_geofence_rules_count,
                    get_highest_priority,
                    set_geofence_all,
                    set_geowebcache_invalidate_cache,
                    sync_geofence_with_guardian,
                    sync_resources_with_guardian)


logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.info(msg, *args)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


class SecurityTest(GeoNodeBaseTestSupport):

    type = 'layer'

    """
    Tests for the Geonode security app.
    """

    def setUp(self):
        super(SecurityTest, self).setUp()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware()

        white_list = [
            reverse('account_ajax_login'),
            reverse('account_confirm_email', kwargs=dict(key='test')),
            reverse('account_login'),
            reverse('account_reset_password'),
            reverse('forgot_username'),
            reverse('layer_acls'),
            reverse('layer_resolve_user'),
        ]

        black_list = [
            reverse('account_signup'),
            reverse('document_browse'),
            reverse('maps_browse'),
            reverse('layer_browse'),
            reverse('layer_detail', kwargs=dict(layername='geonode:Test')),
            reverse('layer_remove', kwargs=dict(layername='geonode:Test')),
            reverse('profile_browse'),
        ]

        request = HttpRequest()
        request.user = get_anonymous_user()

        # Requests should be redirected to the the `redirected_to` path when un-authenticated user attempts to visit
        # a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            if response:
                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response.get('Location').startswith(
                        middleware.redirect_to))

        # The middleware should return None when an un-authenticated user
        # attempts to visit a white-listed url.
        for path in white_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(
                response,
                msg="Middleware activated for white listed path: {0}".format(path))

        self.client.login(username='admin', password='admin')
        admin = get_user_model().objects.get(username='admin')
        self.assertTrue(admin.is_authenticated())
        request.user = admin

        # The middleware should return None when an authenticated user attempts
        # to visit a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_session_ctrl_middleware(self):
        """
        Tests the Geonode session control authentication middleware.
        """
        from geonode.security.middleware import SessionControlMiddleware
        middleware = SessionControlMiddleware()

        request = HttpRequest()

        self.client.login(username='admin', password='admin')
        admin = get_user_model().objects.get(username='admin')
        self.assertTrue(admin.is_authenticated())
        request.user = admin
        request.path = reverse('layer_browse')
        middleware.process_request(request)
        response = self.client.get(request.path)
        self.assertEqual(response.status_code, 200)
        # Simulating Token expired (or not set)
        request.session = {}
        request.session['access_token'] = None
        middleware.process_request(request)
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)


class SecurityViewsTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    def setUp(self):
        super(SecurityViewsTests, self).setUp()
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

        self.user = 'admin'
        self.passwd = 'admin'

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_attributes_sats_refresh(self):
        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        test_layer = Layer.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')
        layer_attributes = test_layer.attributes
        self.assertIsNotNone(layer_attributes)
        test_layer.attribute_set.all().delete()
        test_layer.save()

        data = {
            'uuid': test_layer.uuid
        }
        resp = self.client.post(reverse('attributes_sats_refresh'), data)
        self.assertHttpOK(resp)
        self.assertEquals(layer_attributes.count(), test_layer.attributes.count())

        from geonode.geoserver.helpers import set_attributes_from_geoserver
        test_layer.attribute_set.all().delete()
        test_layer.save()

        set_attributes_from_geoserver(test_layer, overwrite=True)
        self.assertEquals(layer_attributes.count(), test_layer.attributes.count())

        # Remove permissions to anonymous users and try to refresh attributes again
        test_layer.set_permissions({'users': {'AnonymousUser': []}})
        test_layer.attribute_set.all().delete()
        test_layer.save()

        set_attributes_from_geoserver(test_layer, overwrite=True)
        self.assertEquals(layer_attributes.count(), test_layer.attributes.count())

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_invalidate_tiledlayer_cache(self):
        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        test_layer = Layer.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')

        data = {
            'uuid': test_layer.uuid
        }
        resp = self.client.post(reverse('invalidate_tiledlayer_cache'), data)
        self.assertHttpOK(resp)


class BulkPermissionsTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    def setUp(self):
        super(BulkPermissionsTests, self).setUp()
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.bulk_perms_url = reverse('bulk_permissions')
        all_public()
        self.perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": {}}

    def test_set_bulk_permissions(self):
        """Test that after restrict view permissions on two layers
        bobby is unable to see them"""

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEquals(geofence_rules_count, 0)

        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        layers_id = map(lambda x: str(x), layers)
        test_perm_layer = Layer.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')
        resp = self.client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)
        data = {
            'permissions': json.dumps(self.perm_spec),
            'resources': layers_id
        }
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertHttpOK(resp)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log("1. geofence_rules_count: %s " % geofence_rules_count)
            self.assertEquals(geofence_rules_count, 4)
            set_geofence_all(test_perm_layer)
            geofence_rules_count = get_geofence_rules_count()
            _log("2. geofence_rules_count: %s " % geofence_rules_count)
            self.assertEquals(geofence_rules_count, 5)

        self.client.logout()

        self.client.login(username='bobby', password='bob')
        resp = self.client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            perms = get_users_with_perms(test_perm_layer)
            _log("3. perms: %s " % perms)
            sync_geofence_with_guardian(test_perm_layer, perms, user='bobby')

            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log("4. geofence_rules_count: %s " % geofence_rules_count)
            self.assertEquals(geofence_rules_count, 5)

            # Validate maximum priority
            geofence_rules_highest_priority = get_highest_priority()
            _log("5. geofence_rules_highest_priority: %s " % geofence_rules_highest_priority)
            self.assertTrue(geofence_rules_highest_priority > 0)

            # Try GWC Invalidation
            # - it should not work here since the layer has not been uploaded to GeoServer
            set_geowebcache_invalidate_cache(test_perm_layer.alternate)
            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']

            import requests
            from requests.auth import HTTPBasicAuth
            r = requests.get(url + 'gwc/rest/seed/%s.json' % test_perm_layer.alternate,
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEquals(r.status_code, 400)

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEquals(geofence_rules_count, 0)

    def test_bobby_cannot_set_all(self):
        """Test that Bobby can set the permissions only only on the ones
        for which he has the right"""

        layer = Layer.objects.all()[0]
        self.client.login(username='admin', password='admin')
        # give bobby the right to change the layer permissions
        assign_perm('change_resourcebase', Profile.objects.get(username='bobby'), layer.get_self_resource())
        self.client.logout()
        self.client.login(username='bobby', password='bob')
        layer2 = Layer.objects.all()[1]
        data = {
            'permissions': json.dumps({"users": {"bobby": ["view_resourcebase"]}, "groups": {}}),
            'resources': [layer.id, layer2.id]
        }
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertTrue(layer2.title in json.loads(resp.content)['not_changed'])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_perm_specs_synchronization(self):
        """Test that Layer is correctly synchronized with guardian:
            1. Set permissions to all users
            2. Set permissions to a single user
            3. Set permissions to a group of users
            4. Try to sync a layer from GeoServer
        """

        layer = Layer.objects.all()[0]
        self.client.login(username='admin', password='admin')

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEquals(geofence_rules_count, 0)

        perm_spec = {'users': {'AnonymousUser': []}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log("1. geofence_rules_count: %s " % geofence_rules_count)
        self.assertEquals(geofence_rules_count, 0)

        perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": {}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log("2. geofence_rules_count: %s " % geofence_rules_count)
        self.assertEquals(geofence_rules_count, 2)

        perm_spec = {'users': {"admin": ['change_layer_data']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log("3. geofence_rules_count: %s " % geofence_rules_count)
        self.assertEquals(geofence_rules_count, 2)

        perm_spec = {'groups': {'bar': ['view_resourcebase']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log("4. geofence_rules_count: %s " % geofence_rules_count)
        self.assertEquals(geofence_rules_count, 2)

        perm_spec = {'groups': {'bar': ['change_resourcebase']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log("5. geofence_rules_count: %s " % geofence_rules_count)
        self.assertEquals(geofence_rules_count, 0)

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEquals(geofence_rules_count, 0)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_upload_with_time(self):
        """ Try uploading a layer and verify that the user can administrate
        his own layer despite not being a site administrator.
        """
        try:
            # user without change_layer_style cannot edit it
            self.assertTrue(self.client.login(username='bobby', password='bob'))

            # grab bobby
            bobby = get_user_model().objects.get(username="bobby")
            anonymous_group, created = Group.objects.get_or_create(name='anonymous')

            # Upload to GeoServer
            saved_layer = geoserver_upload(
                Layer(),
                os.path.join(
                    gisdata.GOOD_DATA,
                    'time/'
                    "boxes_with_date.shp"),
                bobby,
                'boxes_with_date_by_bobby',
                overwrite=True
            )

            # Test that layer owner can wipe GWC Cache
            ignore_errors = False
            skip_unadvertised = False
            skip_geonode_registered = False
            remove_deleted = True
            verbosity = 2
            owner = bobby
            workspace = 'geonode'
            filter = None
            store = None
            permissions = {
                'users': {"bobby": ['view_resourcebase', 'change_layer_data']},
                'groups': {anonymous_group: ['view_resourcebase']},
            }
            gs_slurp(
                ignore_errors,
                verbosity=verbosity,
                owner=owner,
                workspace=workspace,
                store=store,
                filter=filter,
                skip_unadvertised=skip_unadvertised,
                skip_geonode_registered=skip_geonode_registered,
                remove_deleted=remove_deleted,
                permissions=permissions,
                execute_signals=True)

            saved_layer = Layer.objects.get(title='boxes_with_date_by_bobby')
            check_layer(saved_layer)

            from lxml import etree
            from defusedxml import lxml as dlxml
            from geonode.geoserver.helpers import get_store
            from geonode.geoserver.signals import gs_catalog

            self.assertIsNotNone(saved_layer)
            workspace, name = saved_layer.alternate.split(':')
            self.assertIsNotNone(workspace)
            self.assertIsNotNone(name)
            ws = gs_catalog.get_workspace(workspace)
            self.assertIsNotNone(ws)
            store = get_store(gs_catalog, saved_layer.store, workspace=ws)
            self.assertIsNotNone(store)

            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']

            rest_path = 'rest/workspaces/geonode/datastores/{lyr_name}/featuretypes/{lyr_name}.xml'.\
                format(lyr_name=name)
            import requests
            from requests.auth import HTTPBasicAuth
            r = requests.get(url + rest_path,
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEquals(r.status_code, 200)
            _log(r.text)

            featureType = etree.ElementTree(dlxml.fromstring(r.text))
            metadata = featureType.findall('./[metadata]')
            self.assertEquals(len(metadata), 0)

            payload = """<featureType>
            <metadata>
                <entry key="elevation">
                    <dimensionInfo>
                        <enabled>false</enabled>
                    </dimensionInfo>
                </entry>
                <entry key="time">
                    <dimensionInfo>
                        <enabled>true</enabled>
                        <attribute>date</attribute>
                        <presentation>LIST</presentation>
                        <units>ISO8601</units>
                        <defaultValue/>
                        <nearestMatchEnabled>false</nearestMatchEnabled>
                    </dimensionInfo>
                </entry>
            </metadata></featureType>"""

            r = requests.put(url + rest_path,
                             data=payload,
                             headers={
                                 'Content-type': 'application/xml'
                             },
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEquals(r.status_code, 200)

            r = requests.get(url + rest_path,
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEquals(r.status_code, 200)
            _log(r.text)

            featureType = etree.ElementTree(dlxml.fromstring(r.text))
            metadata = featureType.findall('./[metadata]')
            _log(etree.tostring(metadata[0], encoding='utf8', method='xml'))
            self.assertEquals(len(metadata), 1)

            saved_layer.set_default_permissions()

            from geonode.geoserver.views import get_layer_capabilities
            capab = get_layer_capabilities(saved_layer, tolerant=True)
            self.assertIsNotNone(capab)
            wms_capabilities_url = reverse('capabilities_layer', args=[saved_layer.id])
            wms_capabilities_resp = self.client.get(wms_capabilities_url)
            self.assertTrue(wms_capabilities_resp.status_code, 200)

            all_times = None

            if wms_capabilities_resp.status_code >= 200 and wms_capabilities_resp.status_code < 400:
                wms_capabilities = wms_capabilities_resp.getvalue()
                if wms_capabilities:
                    namespaces = {'wms': 'http://www.opengis.net/wms',
                                  'xlink': 'http://www.w3.org/1999/xlink',
                                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

                    e = dlxml.fromstring(wms_capabilities)
                    for atype in e.findall(
                            "./[wms:Name='%s']/wms:Dimension[@name='time']" % (saved_layer.alternate), namespaces):
                        dim_name = atype.get('name')
                        if dim_name:
                            dim_name = str(dim_name).lower()
                            if dim_name == 'time':
                                dim_values = atype.text
                                if dim_values:
                                    all_times = dim_values.split(",")
                                    break

            self.assertIsNotNone(all_times)
            self.assertEquals(all_times,
                              ['2000-03-01T00:00:00.000Z', '2000-03-02T00:00:00.000Z',
                               '2000-03-03T00:00:00.000Z', '2000-03-04T00:00:00.000Z',
                               '2000-03-05T00:00:00.000Z', '2000-03-06T00:00:00.000Z',
                               '2000-03-07T00:00:00.000Z', '2000-03-08T00:00:00.000Z',
                               '2000-03-09T00:00:00.000Z', '2000-03-10T00:00:00.000Z',
                               '2000-03-11T00:00:00.000Z', '2000-03-12T00:00:00.000Z',
                               '2000-03-13T00:00:00.000Z', '2000-03-14T00:00:00.000Z',
                               '2000-03-15T00:00:00.000Z', '2000-03-16T00:00:00.000Z',
                               '2000-03-17T00:00:00.000Z', '2000-03-18T00:00:00.000Z',
                               '2000-03-19T00:00:00.000Z', '2000-03-20T00:00:00.000Z',
                               '2000-03-21T00:00:00.000Z', '2000-03-22T00:00:00.000Z',
                               '2000-03-23T00:00:00.000Z', '2000-03-24T00:00:00.000Z',
                               '2000-03-25T00:00:00.000Z', '2000-03-26T00:00:00.000Z',
                               '2000-03-27T00:00:00.000Z', '2000-03-28T00:00:00.000Z',
                               '2000-03-29T00:00:00.000Z', '2000-03-30T00:00:00.000Z',
                               '2000-03-31T00:00:00.000Z', '2000-04-01T00:00:00.000Z',
                               '2000-04-02T00:00:00.000Z', '2000-04-03T00:00:00.000Z',
                               '2000-04-04T00:00:00.000Z', '2000-04-05T00:00:00.000Z',
                               '2000-04-06T00:00:00.000Z', '2000-04-07T00:00:00.000Z',
                               '2000-04-08T00:00:00.000Z', '2000-04-09T00:00:00.000Z',
                               '2000-04-10T00:00:00.000Z', '2000-04-11T00:00:00.000Z',
                               '2000-04-12T00:00:00.000Z', '2000-04-13T00:00:00.000Z',
                               '2000-04-14T00:00:00.000Z', '2000-04-15T00:00:00.000Z',
                               '2000-04-16T00:00:00.000Z', '2000-04-17T00:00:00.000Z',
                               '2000-04-18T00:00:00.000Z', '2000-04-19T00:00:00.000Z',
                               '2000-04-20T00:00:00.000Z', '2000-04-21T00:00:00.000Z',
                               '2000-04-22T00:00:00.000Z', '2000-04-23T00:00:00.000Z',
                               '2000-04-24T00:00:00.000Z', '2000-04-25T00:00:00.000Z',
                               '2000-04-26T00:00:00.000Z', '2000-04-27T00:00:00.000Z',
                               '2000-04-28T00:00:00.000Z', '2000-04-29T00:00:00.000Z',
                               '2000-04-30T00:00:00.000Z', '2000-05-01T00:00:00.000Z',
                               '2000-05-02T00:00:00.000Z', '2000-05-03T00:00:00.000Z',
                               '2000-05-04T00:00:00.000Z', '2000-05-05T00:00:00.000Z',
                               '2000-05-06T00:00:00.000Z', '2000-05-07T00:00:00.000Z',
                               '2000-05-08T00:00:00.000Z', '2000-05-09T00:00:00.000Z',
                               '2000-05-10T00:00:00.000Z', '2000-05-11T00:00:00.000Z',
                               '2000-05-12T00:00:00.000Z', '2000-05-13T00:00:00.000Z',
                               '2000-05-14T00:00:00.000Z', '2000-05-15T00:00:00.000Z',
                               '2000-05-16T00:00:00.000Z', '2000-05-17T00:00:00.000Z',
                               '2000-05-18T00:00:00.000Z', '2000-05-19T00:00:00.000Z',
                               '2000-05-20T00:00:00.000Z', '2000-05-21T00:00:00.000Z',
                               '2000-05-22T00:00:00.000Z', '2000-05-23T00:00:00.000Z',
                               '2000-05-24T00:00:00.000Z', '2000-05-25T00:00:00.000Z',
                               '2000-05-26T00:00:00.000Z', '2000-05-27T00:00:00.000Z',
                               '2000-05-28T00:00:00.000Z', '2000-05-29T00:00:00.000Z',
                               '2000-05-30T00:00:00.000Z', '2000-05-31T00:00:00.000Z',
                               '2000-06-01T00:00:00.000Z', '2000-06-02T00:00:00.000Z',
                               '2000-06-03T00:00:00.000Z', '2000-06-04T00:00:00.000Z',
                               '2000-06-05T00:00:00.000Z', '2000-06-06T00:00:00.000Z',
                               '2000-06-07T00:00:00.000Z', '2000-06-08T00:00:00.000Z'])

            saved_layer.set_default_permissions()
            url = reverse('layer_metadata', args=[saved_layer.service_typename])
            resp = self.client.get(url)
            self.assertEquals(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layer
            try:
                saved_layer.delete()
                if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                    from geonode.geoserver.helpers import cleanup
                    cleanup(saved_layer.name, saved_layer.uuid)
            except BaseException:
                pass

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_permissions(self):
        try:
            # Test permissions on a layer

            # grab bobby
            bobby = get_user_model().objects.get(username="bobby")

            layers = Layer.objects.all()[:2].values_list('id', flat=True)
            test_perm_layer = Layer.objects.get(id=layers[0])
            thefile = os.path.join(
                gisdata.VECTOR_DATA,
                'san_andres_y_providencia_poi.shp')
            layer = geoserver_upload(
                test_perm_layer,
                thefile,
                bobby,
                'san_andres_y_providencia_poi',
                overwrite=True
            )
            self.assertIsNotNone(layer)

            # Reset GeoFence Rules
            purge_geofence_all()
            geofence_rules_count = get_geofence_rules_count()
            self.assertTrue(geofence_rules_count == 0)

            ignore_errors = False
            skip_unadvertised = False
            skip_geonode_registered = False
            remove_deleted = True
            verbosity = 2
            owner = get_valid_user('admin')
            workspace = 'geonode'
            filter = None
            store = None
            permissions = {'users': {"admin": ['change_layer_data']}}
            gs_slurp(
                ignore_errors,
                verbosity=verbosity,
                owner=owner,
                console=StreamToLogger(logger, logging.INFO),
                workspace=workspace,
                store=store,
                filter=filter,
                skip_unadvertised=skip_unadvertised,
                skip_geonode_registered=skip_geonode_registered,
                remove_deleted=remove_deleted,
                permissions=permissions,
                execute_signals=True)

            layer = Layer.objects.get(title='san_andres_y_providencia_poi')
            check_layer(layer)

            geofence_rules_count = get_geofence_rules_count()
            _log("0. geofence_rules_count: %s " % geofence_rules_count)
            self.assertEquals(geofence_rules_count, 2)

            # Set the layer private for not authenticated users
            layer.set_permissions({'users': {'AnonymousUser': []}})

            url = 'http://localhost:8080/geoserver/geonode/ows?' \
                'LAYERS=geonode%3Asan_andres_y_providencia_poi&STYLES=' \
                '&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap' \
                '&SRS=EPSG%3A4326' \
                '&BBOX=-81.394599749999,13.316009005566,' \
                '-81.370560451855,13.372728455566' \
                '&WIDTH=217&HEIGHT=512'

            # test view_resourcebase permission on anonymous user
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            self.assertTrue(
                response.info().getheader('Content-Type'),
                'application/vnd.ogc.se_xml;charset=UTF-8'
            )

            # test WMS with authenticated user that has not view_resourcebase:
            # the layer must be not accessible (response is xml)
            request = urllib2.Request(url)
            base64string = base64.encodestring(
                '%s:%s' % ('bobby', 'bob')).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)
            response = urllib2.urlopen(request)
            self.assertTrue(
                response.info().getheader('Content-Type'),
                'application/vnd.ogc.se_xml;charset=UTF-8'
            )

            # test WMS with authenticated user that has view_resourcebase: the layer
            # must be accessible (response is image)
            assign_perm('view_resourcebase', bobby, layer.get_self_resource())
            request = urllib2.Request(url)
            base64string = base64.encodestring(
                '%s:%s' % ('bobby', 'bob')).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)
            response = urllib2.urlopen(request)
            self.assertTrue(response.info().getheader('Content-Type'), 'image/png')

            # test change_layer_data
            # would be nice to make a WFS/T request and test results, but this
            # would work only on PostGIS layers

            # test change_layer_style
            url = 'http://localhost:8080/geoserver/rest/workspaces/geonode/styles/san_andres_y_providencia_poi.xml'
            sld = """<?xml version="1.0" encoding="UTF-8"?>
        <sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld"
        xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0"
        xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
        <sld:NamedLayer>
          <sld:Name>geonode:san_andres_y_providencia_poi</sld:Name>
          <sld:UserStyle>
             <sld:Name>san_andres_y_providencia_poi</sld:Name>
             <sld:Title>san_andres_y_providencia_poi</sld:Title>
             <sld:IsDefault>1</sld:IsDefault>
             <sld:FeatureTypeStyle>
                <sld:Rule>
                   <sld:PointSymbolizer>
                      <sld:Graphic>
                         <sld:Mark>
                            <sld:Fill>
                               <sld:CssParameter name="fill">#8A7700
                               </sld:CssParameter>
                            </sld:Fill>
                            <sld:Stroke>
                               <sld:CssParameter name="stroke">#bbffff
                               </sld:CssParameter>
                            </sld:Stroke>
                         </sld:Mark>
                         <sld:Size>10</sld:Size>
                      </sld:Graphic>
                   </sld:PointSymbolizer>
                </sld:Rule>
             </sld:FeatureTypeStyle>
          </sld:UserStyle>
        </sld:NamedLayer>
        </sld:StyledLayerDescriptor>"""

            # user without change_layer_style cannot edit it
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
            self.assertEquals(response.status_code, 404)

            # user with change_layer_style can edit it
            assign_perm('change_layer_style', bobby, layer)
            perm_spec = {
                'users': {
                    'bobby': ['view_resourcebase',
                              'change_resourcebase', ]
                }
            }
            layer.set_permissions(perm_spec)
            response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
        finally:
            try:
                layer.delete()
            except BaseException:
                pass


class PermissionsTest(GeoNodeBaseTestSupport):

    """Tests GeoNode permissions
    """

    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    # Permissions Tests

    # Users
    # - admin (pk=2)
    # - bobby (pk=1)

    def setUp(self):
        super(PermissionsTest, self).setUp()
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()
        self.anonymous_user = get_anonymous_user()

    def test_layer_set_default_permissions(self):
        """Verify that Layer.set_default_permissions is behaving as expected
        """

        # Get a Layer object to work with
        layer = Layer.objects.all()[0]
        # Set the default permissions
        layer.set_default_permissions()

        # Test that the anonymous user can read
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can read
        self.assertTrue(
            layer.owner.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can download it
        self.assertTrue(
            layer.owner.has_perm(
                'download_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can edit metadata
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource()))

        # Test that the owner user can edit data if is vector type
        if layer.storeType == 'dataStore':
            self.assertTrue(
                layer.owner.has_perm(
                    'change_layer_data',
                    layer))

        # Test that the owner user can edit styles
        self.assertTrue(
            layer.owner.has_perm(
                'change_layer_style',
                layer))

        # Test that the owner can manage the layer
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'delete_resourcebase',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase_permissions',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'publish_resourcebase',
                layer.get_self_resource()))

    def test_set_layer_permissions(self):
        """Verify that the set_layer_permissions view is behaving as expected
        """

        # Get a layer to work with
        layer = Layer.objects.all()[0]

        # FIXME Test a comprehensive set of permissions specifications

        # Set the Permissions
        layer.set_permissions(self.perm_spec)

        # Test that the Permissions for anonymous user is are set
        self.assertFalse(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        current_perms = layer.get_all_level_info()
        self.assertEqual(len(current_perms['users'].keys()), 2)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec['users'].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, layer.get_self_resource()))

    def test_ajax_layer_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].id
        invalid_layer_id = 9999999

        # Test that an invalid layer.alternate is handled for properly
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    invalid_layer_id,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(
            reverse(
                'resource_permissions',
                args=(
                    valid_layer_typename,
                )))
        assert('permissions' in response.content)

        # Test that a user is required to have maps.change_layer_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 200)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")

        # Test that the method returns 200
        self.assertEquals(response.status_code, 200)

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in
        # test_set_layer_permissions will handle for that?

    def test_perms_info(self):
        """ Verify that the perms_info view is behaving as expected
        """

        # Test with a Layer object
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # Test that the anonymous user can read
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that layer owner can edit layer
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))

        # Test with a Map object
        # TODO

    # now we test permissions, first on an authenticated user and then on the
    # anonymous user
    # 1. view_resourcebase
    # 2. change_resourcebase
    # 3. delete_resourcebase
    # 4. change_resourcebase_metadata
    # 5. change_resourcebase_permissions
    # 6. change_layer_data
    # 7. change_layer_style

    def test_not_superuser_permissions(self):

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertTrue(geofence_rules_count == 0)

        # grab bobby
        bob = get_user_model().objects.get(username='bobby')

        # grab a layer
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # verify bobby has view/change permissions on it but not manage
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase_permissions',
                layer.get_self_resource()))

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log("1. geofence_rules_count: %s " % geofence_rules_count)
            self.assertTrue(geofence_rules_count == 1)

        self.assertTrue(self.client.login(username='bobby', password='bob'))

        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that bobby can access the layer
        # detail page
        self.assertTrue(
            bob.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        response = self.client.get(reverse('layer_detail', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that bobby can not access the
        # layer detail page
        remove_perm('view_resourcebase', bob, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (401, 403))

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that bobby cannot access the
        # layer replace page
        response = self.client.get(reverse('layer_replace', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)
        # 2.2 has change_resourcebase: verify that bobby can access the layer
        # replace page
        assign_perm('change_resourcebase', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_replace', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)

        # 3. delete_resourcebase
        # 3.1 has not delete_resourcebase: verify that bobby cannot access the
        # layer delete page
        response = self.client.get(reverse('layer_remove', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)
        # 3.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        assign_perm('delete_resourcebase', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'delete_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_remove', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that bobby cannot
        # access the layer metadata page
        response = self.client.get(reverse('layer_metadata', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)
        # 4.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        assign_perm('change_resourcebase_metadata', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_metadata', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            perms = get_users_with_perms(layer)
            _log("2. perms: %s " % perms)
            sync_geofence_with_guardian(layer, perms, user=bob, group=anonymous_group)

            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log("3. geofence_rules_count: %s " % geofence_rules_count)
            self.assertEquals(geofence_rules_count, 1)

        # 5. change_resourcebase_permissions
        # should be impossible for the user without change_resourcebase_permissions
        # to change permissions as the permission form is not available in the
        # layer detail page?

        # 6. change_layer_data
        # must be done in integration test sending a WFS-T request with CURL

        # 7. change_layer_style
        # 7.1 has not change_layer_style: verify that bobby cannot access
        # the layer style page
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            response = self.client.get(reverse('layer_style_manage', args=(layer.alternate,)))
            self.assertEquals(response.status_code, 200)
        # 7.2 has change_layer_style: verify that bobby can access the
        # change layer style page
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            assign_perm('change_layer_style', bob, layer)
            self.assertTrue(
                bob.has_perm(
                    'change_layer_style',
                    layer))
            response = self.client.get(reverse('layer_style_manage', args=(layer.alternate,)))
            self.assertEquals(response.status_code, 200)

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEquals(geofence_rules_count, 0)

    def test_anonymus_permissions(self):

        # grab a layer
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that anonymous user can access
        # the layer detail page
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_detail', args=(layer.alternate,)))
        self.assertEquals(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that anonymous user can not
        # access the layer detail page
        remove_perm('view_resourcebase', self.anonymous_user, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that anonymous user cannot
        # access the layer replace page but redirected to login
        response = self.client.get(reverse('layer_replace', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 3. delete_resourcebase
        # 3.1 has not delete_resourcebase: verify that anonymous user cannot
        # access the layer delete page but redirected to login
        response = self.client.get(reverse('layer_remove', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that anonymous user
        # cannot access the layer metadata page but redirected to login
        response = self.client.get(reverse('layer_metadata', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 5 N\A? 6 is an integration test...

        # 7. change_layer_style
        # 7.1 has not change_layer_style: verify that anonymous user cannot access
        # the layer style page but redirected to login
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            response = self.client.get(reverse('layer_style_manage', args=(layer.alternate,)))
            self.assertTrue(response.status_code in (302, 403))


class GisBackendSignalsTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    def setUp(self):
        super(GisBackendSignalsTests, self).setUp()
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.bulk_perms_url = reverse('bulk_permissions')
        all_public()
        self.perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": {}}

    def test_save_and_delete_signals(self):
        """Test that GeoServer Signals methods work as espected"""

        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        test_perm_layer = Layer.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.geoserver.signals import (geoserver_pre_delete,
                                                   geoserver_post_save,
                                                   geoserver_post_save_local)
            # Handle Layer Save and Upload Signals
            geoserver_post_save(test_perm_layer, sender=Layer, created=True)
            geoserver_post_save_local(test_perm_layer)

            # Check instance bbox and links
            self.assertIsNotNone(test_perm_layer.bbox)
            self.assertIsNotNone(test_perm_layer.srid)
            self.assertIsNotNone(test_perm_layer.link_set)
            self.assertEquals(len(test_perm_layer.link_set.all()), 7)

            # Layer Manipulation
            from geonode.geoserver.upload import geoserver_upload
            from geonode.geoserver.signals import gs_catalog
            from geonode.geoserver.helpers import (check_geoserver_is_up,
                                                   get_sld_for,
                                                   fixup_style,
                                                   set_layer_style,
                                                   get_store,
                                                   set_attributes_from_geoserver,
                                                   set_styles,
                                                   create_gs_thumbnail,
                                                   cleanup)
            check_geoserver_is_up()

            admin_user = get_user_model().objects.get(username="admin")
            saved_layer = geoserver_upload(
                test_perm_layer,
                os.path.join(
                    gisdata.VECTOR_DATA,
                    "san_andres_y_providencia_poi.shp"),
                admin_user,
                test_perm_layer.name,
                overwrite=True
            )

            self.assertIsNotNone(saved_layer)
            _log(saved_layer)
            workspace, name = test_perm_layer.alternate.split(':')
            self.assertIsNotNone(workspace)
            self.assertIsNotNone(name)
            ws = gs_catalog.get_workspace(workspace)
            self.assertIsNotNone(ws)
            store = get_store(gs_catalog, name, workspace=ws)
            _log("1. ------------ %s " % store)
            self.assertIsNotNone(store)

            # Save layer attributes
            set_attributes_from_geoserver(test_perm_layer)

            # Save layer styles
            set_styles(test_perm_layer, gs_catalog)

            # set SLD
            sld = test_perm_layer.default_style.sld_body if test_perm_layer.default_style else None
            if sld:
                _log("2. ------------ %s " % sld)
                set_layer_style(test_perm_layer, test_perm_layer.alternate, sld)

            fixup_style(gs_catalog, test_perm_layer.alternate, None)
            self.assertIsNotNone(get_sld_for(gs_catalog, test_perm_layer))
            _log("3. ------------ %s " % get_sld_for(gs_catalog, test_perm_layer))

            create_gs_thumbnail(test_perm_layer, overwrite=True)
            self.assertIsNotNone(test_perm_layer.get_thumbnail_url())
            self.assertTrue(test_perm_layer.has_thumbnail())

            # Handle Layer Delete Signals
            geoserver_pre_delete(test_perm_layer, sender=Layer)

            # Check instance has been removed from GeoServer also
            from geonode.geoserver.views import get_layer_capabilities
            self.assertIsNone(get_layer_capabilities(test_perm_layer))

            # Cleaning Up
            test_perm_layer.delete()
            cleanup(test_perm_layer.name, test_perm_layer.uuid)


@on_ogc_backend(geoserver.BACKEND_PACKAGE)
class SecurityRulesTest(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    """
    Test resources synchronization with Guardian and dirty states cleaning
    """

    def setUp(self):
        super(SecurityRulesTest, self).setUp()
        # Layer upload
        layer_upload_url = reverse('layer_upload')
        self.client.login(username="admin", password="admin")
        input_paths, suffixes = self._get_input_paths()
        input_files = [open(fp, 'rb') for fp in input_paths]
        files = dict(zip(['{}_file'.format(s) for s in suffixes], input_files))
        files['base_file'] = files.pop('shp_file')
        with contextlib.nested(*input_files):
            files['permissions'] = '{}'
            files['charset'] = 'utf-8'
            files['layer_title'] = 'test layer'
            resp = self.client.post(layer_upload_url, data=files)
        # Check the response is OK
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        lname = data['url'].split(':')[-1]
        self._l = Layer.objects.get(name=lname)

    def _get_input_paths(self):
        base_name = 'single_point'
        suffixes = 'shp shx dbf prj'.split(' ')
        base_path = gisdata.GOOD_DATA
        paths = [os.path.join(base_path, 'vector', '{}.{}'.format(base_name, suffix)) for suffix in suffixes]
        return paths, suffixes,

    def test_sync_resources_with_guardian_delay_false(self):

        with self.settings(DELAYED_SECURITY_SIGNALS=False):
            # Set geofence (and so the dirty state)
            set_geofence_all(self._l)
            # Retrieve the same layer
            dirty_layer = Layer.objects.get(pk=self._l.id)
            # Check dirty state (True)
            self.assertFalse(dirty_layer.dirty_state)
            # Call sync resources
            sync_resources_with_guardian()
            clean_layer = Layer.objects.get(pk=self._l.id)
            # Check dirty state
            self.assertFalse(clean_layer.dirty_state)

    def test_sync_resources_with_guardian_delay_true(self):

        with self.settings(DELAYED_SECURITY_SIGNALS=True):
            # Set geofence (and so the dirty state)
            set_geofence_all(self._l)
            # Retrieve the same layer
            dirty_layer = Layer.objects.get(pk=self._l.id)
            # Check dirty state (True)
            self.assertTrue(dirty_layer.dirty_state)
            # Call sync resources
            sync_resources_with_guardian()
            clean_layer = Layer.objects.get(pk=self._l.id)
            # Check dirty state
            self.assertFalse(clean_layer.dirty_state)
