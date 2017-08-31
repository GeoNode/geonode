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
import json
import os
from StringIO import StringIO

import gisdata
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.testcases import LiveServerTestCase

from geonode import geoserver, qgis_server
from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload
from tastypie.test import ResourceTestCase

from geonode.base.populate_test_data import create_models, all_public, \
    reconnect_signals, disconnect_signals
from geonode.layers.models import Layer
from geonode.utils import check_ogc_backend


class PermissionsApiTests(ResourceTestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(PermissionsApiTests, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        create_models(type='layer')
        all_public()
        self.perm_spec = {"users": {}, "groups": {}}

    def test_layer_get_list_unauth_all_public(self):
        """
        Test that the correct number of layers are returned when the
        client is not logged in and all are public
        """

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layers_get_list_unauth_some_public(self):
        """
        Test that if a layer is not public then not all are returned when the
        client is not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

    def test_layers_get_list_auth_some_public(self):
        """
        Test that if a layer is not public then all are returned if the
        client is not logged in
        """
        self.api_client.client.login(username=self.user, password=self.passwd)
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_list_layer_private_to_one_user(self):
        """
        Test that if a layer is only visible by admin, then does not appear
        in the unauthenticated list nor in the list when logged is as bobby
        """
        perm_spec = {"users": {"admin": ['view_resourcebase']}, "groups": {}}
        layer = Layer.objects.all()[0]
        layer.set_permissions(perm_spec)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        self.api_client.client.login(username='bobby', password='bob')
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_detail_unauth_layer_not_public(self):
        """
        Test that layer detail gives 401 when not public and not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)
        self.assertHttpUnauthorized(self.api_client.get(
            self.list_url + str(layer.id) + '/'))

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url + str(layer.id) + '/')
        self.assertValidJSONResponse(resp)

    def test_new_user_has_access_to_old_layers(self):
        """Test that a new user can access the public available layers"""
        from geonode.people.models import Profile
        Profile.objects.create(username='imnew',
                               password='pbkdf2_sha256$12000$UE4gAxckVj4Z$N\
            6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=')
        self.api_client.client.login(username='imnew', password='thepwd')
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)


class SearchApiTests(ResourceTestCase):

    """Test the search"""

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(SearchApiTests, self).setUp()

        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        create_models(type='layer')
        all_public()

    def test_category_filters(self):
        """Test category filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = self.list_url + '?category__identifier=location'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        filter_url = self.list_url + \
            '?category__identifier__in=location&category__identifier__in=biota'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 5)

    def test_tag_filters(self):
        """Test keywords filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different keywords
        filter_url = self.list_url + '?keywords__slug=layertagunique'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + \
            '?keywords__slug__in=layertagunique&keywords__slug__in=populartag'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_owner_filters(self):
        """Test owner filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different owners
        filter_url = self.list_url + '?owner__username=user1'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 2)

        filter_url = self.list_url + \
            '?owner__username__in=user1&owner__username__in=foo'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

    def test_title_filter(self):
        """Test title filtering"""

        # check we get the correct layers number returnered filtering on the
        # title
        filter_url = self.list_url + '?title=layer2'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

    def test_date_filter(self):
        """Test date filtering"""

        # check we get the correct layers number returnered filtering on the
        # title
        filter_url = self.list_url + '?date__exact=1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + '?date__gte=1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        filter_url = self.list_url + '?date__range=1950-01-01,1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 4)


class LayersStylesApiInteractionTests(LiveServerTestCase, ResourceTestCase):

    """Test Layers"""

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(LayersStylesApiInteractionTests, self).setUp()

        # Reconnect Geoserver signals
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            reconnect_signals()

        call_command('loaddata', 'people_data', verbosity=0)

        self.layer_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.style_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'styles'})
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        self.layer = file_upload(filename)
        all_public()

    def tearDown(self):
        Layer.objects.all().delete()

        # Disconnect Geoserver signals
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            disconnect_signals()

    def test_layer_interaction(self):
        """Layer API interaction check."""
        layer_id = self.layer.id

        layer_detail_url = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers',
                'id': layer_id
            }
        )
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Should have links
        self.assertTrue('links' in obj and obj['links'])
        # Should have default style
        self.assertTrue('default_style' in obj and obj['default_style'])
        # Should have styles
        self.assertTrue('styles' in obj and obj['styles'])

        # Test filter layers by id
        filter_url = self.layer_list_url + '?id=' + str(layer_id)
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0]
        # Should have links
        self.assertTrue('links' in obj)
        # Should not have styles
        self.assertTrue('styles' not in obj)
        # Should have default_style
        self.assertTrue('default_style' in obj and obj['default_style'])
        # Should have resource_uri to browse layer detail
        self.assertTrue('resource_uri' in obj and obj['resource_uri'])

        prev_obj = obj
        # Test filter layers by name
        filter_url = self.layer_list_url + '?name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0]

        self.assertEqual(obj, prev_obj)

    def test_style_interaction(self):
        """Style API interaction check."""

        # filter styles by layer id
        filter_url = self.style_list_url + '?layer__id=' + str(self.layer.id)
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 1)

        # filter styles by layer name
        filter_url = self.style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 1)

        # Check necessary list fields
        obj = objects[0]
        field_list = [
            'layer',
            'name',
            'title',
            'style_url',
            'type',
            'resource_uri'
        ]

        # Additional field based on OGC Backend
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            field_list += [
                'version',
                'workspace'
            ]
        elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            field_list += [
                'style_legend_url'
            ]
        for f in field_list:
            self.assertTrue(f in obj)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            self.assertEqual(obj['type'], 'sld')
        elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            self.assertEqual(obj['type'], 'qml')

        # Check style detail
        detail_url = obj['resource_uri']
        resp = self.api_client.get(detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)

        # should include body field
        self.assertTrue('body' in obj and obj['body'])

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_add_delete_styles(self):
        """Style API Add/Delete interaction."""
        # Check styles count
        style_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'styles'
            }
        )
        filter_url = style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 1)

        # Fetch default style
        layer_detail_url = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers',
                'id': self.layer.id
            }
        )
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Take default style url from Layer detail info
        default_style_url = obj['default_style']
        resp = self.api_client.get(default_style_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        style_body = obj['body']

        style_stream = StringIO(style_body)
        # Add virtual filename
        style_stream.name = 'style.qml'
        data = {
            'layer__id': self.layer.id,
            'name': 'new_style',
            'title': 'New Style',
            'style': style_stream
        }
        # Use default client to request
        resp = self.client.post(style_list_url, data=data)

        # Should not be able to add style without authentication
        self.assertEqual(resp.status_code, 403)

        # Login using anonymous user
        self.client.login(username='AnonymousUser')
        style_stream.seek(0)
        resp = self.client.post(style_list_url, data=data)
        # Should not be able to add style without correct permission
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # Use admin credentials
        self.client.login(username='admin', password='admin')
        style_stream.seek(0)
        resp = self.client.post(style_list_url, data=data)
        self.assertEqual(resp.status_code, 201)

        # Check styles count
        filter_url = style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 2)

        # Attempt to set default style
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Get style list and get new default style
        styles = obj['styles']
        new_default_style = None
        for s in styles:
            if not s == obj['default_style']:
                new_default_style = s
                break
        obj['default_style'] = new_default_style
        # Put the new update
        patch_data = {
            'default_style': new_default_style
        }
        resp = self.client.patch(
            layer_detail_url,
            data=json.dumps(patch_data),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # check new default_style
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        self.assertEqual(obj['default_style'], new_default_style)

        # Attempt to delete style
        filter_url = style_list_url + '?layer__id=%d&name=%s' % (
            self.layer.id, data['name'])
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        resource_uri = objects[0]['resource_uri']

        resp = self.client.delete(resource_uri)
        self.assertEqual(resp.status_code, 204)

        resp = self.api_client.get(filter_url)
        meta = self.deserialize(resp)['meta']

        self.assertEqual(meta['total_count'], 0)
