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
import base64
import logging
import requests
import importlib

from requests.auth import HTTPBasicAuth
from tastypie.test import ResourceTestCaseMixin

from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.http import HttpRequest
from django.test.testcases import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from guardian.shortcuts import (
    get_anonymous_user,
    assign_perm,
    remove_perm
)

from geonode import geoserver
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.documents.models import Document
from geonode.compat import ensure_string
from geonode.utils import check_ogc_backend
from geonode.tests.utils import check_dataset
from geonode.decorators import on_ogc_backend
from geonode.geoserver.helpers import gs_slurp
from geonode.resource.manager import resource_manager
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.groups.models import Group, GroupMember, GroupProfile
from geonode.layers.populate_datasets_data import create_dataset_data

from geonode.base.models import (
    Configuration,
    UserGeoLimit,
    GroupGeoLimit
)
from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models,
    create_single_dataset)
from geonode.geoserver.security import (
    _get_gf_services,
    get_user_geolimits,
    get_geofence_rules,
    get_geofence_rules_count,
    get_highest_priority,
    set_geofence_all,
    purge_geofence_all,
    sync_geofence_with_guardian,
    sync_resources_with_guardian,
    _get_gwc_filters_and_formats
)

from .utils import (
    get_users_with_perms,
    get_visible_resources,
)

from .permissions import (
    PermSpec,
    PermSpecCompact)

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


class StreamToLogger:
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


class SecurityTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    """
    Tests for the Geonode security app.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

        self.maxDiff = None
        self.user = 'admin'
        self.passwd = 'admin'
        create_dataset_data()
        self.anonymous_user = get_anonymous_user()
        self.config = Configuration.load()
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'datasets'})
        self.bulk_perms_url = reverse('bulk_permissions')
        self.perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": []}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware(None)

        white_list = [
            reverse('account_ajax_login'),
            reverse('account_confirm_email', kwargs=dict(key='test')),
            reverse('account_login'),
            reverse('account_reset_password'),
            reverse('forgot_username'),
            reverse('dataset_acls'),
            reverse('dataset_resolve_user'),
        ]

        black_list = [
            reverse('account_signup'),
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
                msg=f"Middleware activated for white listed path: {path}")

        self.client.login(username='admin', password='admin')
        admin = get_user_model().objects.get(username='admin')
        self.assertTrue(admin.is_authenticated)
        request.user = admin

        # The middleware should return None when an authenticated user attempts
        # to visit a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware_with_basic_auth(self):
        """
        Tests the Geonode login required authentication middleware with Basic authenticated queries
        """
        from geonode.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware(None)

        black_listed_url = reverse('dataset_upload')
        white_listed_url = reverse('account_login')

        # unauthorized request to black listed URL should be redirected to `redirect_to` URL
        request = HttpRequest()
        request.user = get_anonymous_user()

        request.path = black_listed_url
        response = middleware.process_request(request)
        if response:
            self.assertEqual(response.status_code, 302)
            self.assertTrue(
                response.get('Location').startswith(
                    middleware.redirect_to))

        # unauthorized request to white listed URL should be allowed
        request.path = white_listed_url
        response = middleware.process_request(request)
        self.assertIsNone(
            response,
            msg=f"Middleware activated for white listed path: {black_listed_url}")

        # Basic authorized request to black listed URL should be allowed
        request.path = black_listed_url
        request.META["HTTP_AUTHORIZATION"] = f'Basic {base64.b64encode(b"bobby:bob").decode("utf-8")}'
        response = middleware.process_request(request)
        self.assertIsNone(
            response,
            msg=f"Middleware activated for white listed path: {black_listed_url}")

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware_with_custom_login_url(self):
        """
        Tests the Geonode login required authentication middleware with Basic authenticated queries
        """

        site_url_settings = [f"{settings.SITEURL}login/custom", "/login/custom", "login/custom"]
        black_listed_url = reverse("dataset_upload")

        for setting in site_url_settings:
            with override_settings(LOGIN_URL=setting):

                from geonode.security import middleware as mw

                # reload the middleware module to fetch overridden settings
                importlib.reload(mw)
                middleware = mw.LoginRequiredMiddleware(None)

                # unauthorized request to black listed URL should be redirected to `redirect_to` URL
                request = HttpRequest()
                request.user = get_anonymous_user()
                request.path = black_listed_url

                response = middleware.process_request(request)

                self.assertIsNotNone(response, "Middleware didn't activate for blacklisted URL.")
                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response.get("Location").startswith("/"),
                    msg=f"Returned redirection should be a valid path starting '/'. "
                        f"Instead got: {response.get('Location')}",
                )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_session_ctrl_middleware(self):
        """
        Tests the Geonode session control authentication middleware.
        """
        from geonode.security.middleware import SessionControlMiddleware
        middleware = SessionControlMiddleware(None)

        request = HttpRequest()
        self.client.login(username='admin', password='admin')
        admin = get_user_model().objects.get(username='admin')
        self.assertTrue(admin.is_authenticated)
        request.user = admin
        request.path = reverse('dataset_upload')
        middleware.process_request(request)
        response = self.client.get(request.path)
        self.assertEqual(response.status_code, 200)
        # Simulating Token expired (or not set)
        request.session = {}
        request.session['access_token'] = None
        middleware.process_request(request)
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_attributes_sats_refresh(self):
        layers = Dataset.objects.all()[:2].values_list('id', flat=True)
        test_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')
        dataset_attributes = test_dataset.attributes
        self.assertIsNotNone(dataset_attributes)
        test_dataset.attribute_set.all().delete()
        test_dataset.save()

        data = {
            'uuid': test_dataset.uuid
        }
        resp = self.client.post(reverse('attributes_sats_refresh'), data)
        if resp.status_code == 200:
            self.assertHttpOK(resp)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())

            from geonode.geoserver.helpers import set_attributes_from_geoserver
            test_dataset.attribute_set.all().delete()
            test_dataset.save()

            set_attributes_from_geoserver(test_dataset, overwrite=True)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())

            # Remove permissions to anonymous users and try to refresh attributes again
            test_dataset.set_permissions({'users': {'AnonymousUser': []}, 'groups': []})
            test_dataset.attribute_set.all().delete()
            test_dataset.save()

            set_attributes_from_geoserver(test_dataset, overwrite=True)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())
        else:
            # If GeoServer is unreachable, this view now returns a 302 error
            self.assertEqual(resp.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_invalidate_tileddataset_cache(self):
        layers = Dataset.objects.all()[:2].values_list('id', flat=True)
        test_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')

        data = {
            'uuid': test_dataset.uuid
        }
        resp = self.client.post(reverse('invalidate_tileddataset_cache'), data)
        self.assertHttpOK(resp)

    def test_set_bulk_permissions(self):
        """Test that after restrict view permissions on two layers
        bobby is unable to see them"""
        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEqual(geofence_rules_count, 0)

        layers = Dataset.objects.all()[:2].values_list('id', flat=True)
        layers_id = [str(x) for x in layers]
        test_perm_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username='admin', password='admin')
        resp = self.client.get(self.list_url)
        self.assertEqual(len(self.deserialize(resp)['objects']), 8)
        data = {
            'permissions': json.dumps(self.perm_spec),
            'resources': layers_id
        }
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertHttpOK(resp)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log(f"1. geofence_rules_count: {geofence_rules_count} ")
            self.assertGreaterEqual(geofence_rules_count, 10)
            set_geofence_all(test_perm_dataset)
            geofence_rules_count = get_geofence_rules_count()
            _log(f"2. geofence_rules_count: {geofence_rules_count} ")
            self.assertGreaterEqual(geofence_rules_count, 11)

        self.client.logout()

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            self.client.login(username='bobby', password='bob')
            resp = self.client.get(self.list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 6)

            perms = get_users_with_perms(test_perm_dataset)
            _log(f"3. perms: {perms} ")
            sync_geofence_with_guardian(test_perm_dataset, perms, user='bobby')

            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log(f"4. geofence_rules_count: {geofence_rules_count} ")
            self.assertGreaterEqual(geofence_rules_count, 13)

            # Validate maximum priority
            geofence_rules_highest_priority = get_highest_priority()
            _log(f"5. geofence_rules_highest_priority: {geofence_rules_highest_priority} ")
            self.assertTrue(geofence_rules_highest_priority > 0)

            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']

            r = requests.get(f"{url}gwc/rest/seed/{test_perm_dataset.alternate}.json",
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEqual(r.status_code, 400)

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEqual(geofence_rules_count, 0)

    def test_bobby_cannot_set_all(self):
        """Test that Bobby can set the permissions only only on the ones
        for which he has the right"""
        bobby = get_user_model().objects.get(username='bobby')
        layer = Dataset.objects.all().exclude(owner=bobby)[0]
        self.client.login(username='admin', password='admin')
        # give bobby the right to change the layer permissions
        assign_perm('change_resourcebase_permissions', bobby, layer.get_self_resource())
        self.client.logout()
        self.client.login(username='bobby', password='bob')
        layer2 = Dataset.objects.all().exclude(owner=bobby)[1]
        data = {
            'permissions': json.dumps({"users": {"bobby": ["view_resourcebase"]}, "groups": []}),
            'resources': [layer.id, layer2.id]
        }
        resp = self.client.post(self.bulk_perms_url, data)
        content = resp.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        self.assertNotIn(layer.title, json.loads(content)['not_changed'])
        self.assertIn(layer2.title, json.loads(content)['not_changed'])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_user_can(self):
        bobby = get_user_model().objects.get(username='bobby')
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                    'change_dataset_data',
                    'change_dataset_style'
                ]
            },
            'groups': []
        }
        dataset = Dataset.objects.filter(subtype='vector').first()
        dataset.set_permissions(perm_spec)
        # Test user has permission with read_only=False
        self.assertTrue(dataset.user_can(bobby, 'change_dataset_style'))
        # Test with edit permission and read_only=True
        self.config.read_only = True
        self.config.save()
        self.assertFalse(dataset.user_can(bobby, 'change_dataset_style'))
        # Test with view permission and read_only=True
        self.assertTrue(dataset.user_can(bobby, 'view_resourcebase'))
        # Test on a 'raster' subtype
        self.config.read_only = False
        self.config.save()
        dataset = Dataset.objects.filter(subtype='raster').first()
        dataset.set_permissions(perm_spec)
        # Test user has permission with read_only=False
        self.assertFalse(dataset.user_can(bobby, 'change_dataset_data'))
        self.assertTrue(dataset.user_can(bobby, 'change_dataset_style'))

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_perm_specs_synchronization(self):
        """Test that Dataset is correctly synchronized with guardian:
            1. Set permissions to all users
            2. Set permissions to a single user
            3. Set permissions to a group of users
            4. Try to sync a layer from GeoServer
        """
        bobby = get_user_model().objects.get(username='bobby')
        layer = Dataset.objects.filter(subtype='vector').exclude(owner=bobby).first()
        self.client.login(username='admin', password='admin')

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 0)

        perm_spec = {'users': {'AnonymousUser': []}, 'groups': []}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"1. geofence_rules_count: {geofence_rules_count} ")
        self.assertEqual(geofence_rules_count, 5)

        perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": []}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"2. geofence_rules_count: {geofence_rules_count} ")
        self.assertEqual(geofence_rules_count, 7)

        perm_spec = {'users': {"admin": ['change_dataset_data']}, 'groups': []}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"3. geofence_rules_count: {geofence_rules_count} ")
        self.assertEqual(geofence_rules_count, 7)

        # FULL WFS-T
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                    'change_dataset_style',
                    'change_dataset_data'
                ]
            },
            'groups': []
        }
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 10)

        rules_objs = get_geofence_rules(entries=10)
        _deny_wfst_rule_exists = False
        for rule in rules_objs['rules']:
            if rule['service'] == "WFS" and \
                    rule['userName'] == 'bobby' and \
                    rule['request'] == "TRANSACTION":
                _deny_wfst_rule_exists = rule['access'] == 'DENY'
                break
        self.assertFalse(_deny_wfst_rule_exists)

        # NO WFS-T
        # - order is important
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                ]
            },
            'groups': []
        }
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 13)

        rules_objs = get_geofence_rules(entries=13)
        _deny_wfst_rule_exists = False
        _deny_wfst_rule_position = -1
        _allow_wfs_rule_position = -1
        for cnt, rule in enumerate(rules_objs['rules']):
            if rule['service'] == "WFS" and \
                    rule['userName'] == 'bobby' and \
                    rule['request'] == "TRANSACTION":
                _deny_wfst_rule_exists = rule['access'] == 'DENY'
                _deny_wfst_rule_position = cnt
            elif rule['service'] == "WFS" and \
                    rule['userName'] == 'bobby' and \
                    (rule['request'] is None or rule['request'] == '*'):
                _allow_wfs_rule_position = cnt
        self.assertTrue(_deny_wfst_rule_exists)
        self.assertTrue(_allow_wfs_rule_position > _deny_wfst_rule_position)

        # NO WFS
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                ]
            },
            'groups': []
        }
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 7)

        rules_objs = get_geofence_rules(entries=7)
        _deny_wfst_rule_exists = False
        for rule in rules_objs['rules']:
            if rule['service'] == "WFS" and \
                    rule['userName'] == 'bobby' and \
                    rule['request'] == "TRANSACTION":
                _deny_wfst_rule_exists = rule['access'] == 'DENY'
                break
        self.assertFalse(_deny_wfst_rule_exists)

        perm_spec = {'users': {}, 'groups': {'bar': ['view_resourcebase']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"4. geofence_rules_count: {geofence_rules_count} ")
        self.assertEqual(geofence_rules_count, 7)

        perm_spec = {'users': {}, 'groups': {'bar': ['change_resourcebase']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"5. geofence_rules_count: {geofence_rules_count} ")
        self.assertEqual(geofence_rules_count, 5)

        # Testing GeoLimits
        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 0)
        layer = Dataset.objects.first()
        # grab bobby
        bobby = get_user_model().objects.get(username="bobby")
        gf_services = _get_gf_services(layer, layer.get_all_level_info())
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(layer, None, None, gf_services)
        filters, formats = _get_gwc_filters_and_formats([_disable_dataset_cache])
        self.assertListEqual(filters, [{
            "styleParameterFilter": {
                "STYLES": ""
            }
        }])
        self.assertListEqual(formats, [
            'application/json;type=utfgrid',
            'image/gif',
            'image/jpeg',
            'image/png',
            'image/png8',
            'image/vnd.jpeg-png',
            'image/vnd.jpeg-png8'
        ])

        geo_limit, _ = UserGeoLimit.objects.get_or_create(
            user=bobby,
            resource=layer.get_self_resource()
        )
        geo_limit.wkt = 'SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))'
        geo_limit.save()
        layer.users_geolimits.add(geo_limit)
        self.assertEqual(layer.users_geolimits.all().count(), 1)
        gf_services = _get_gf_services(layer, layer.get_all_level_info())
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(layer, bobby, None, gf_services)
        filters, formats = _get_gwc_filters_and_formats([_disable_dataset_cache])
        self.assertIsNone(filters)
        self.assertIsNone(formats)

        perm_spec = {
            "users": {"bobby": ["view_resourcebase"]}, "groups": []}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 8)

        rules_objs = get_geofence_rules(entries=8)
        self.assertEqual(len(rules_objs['rules']), 8)
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs['rules']):
            if rule['service'] is None and rule['userName'] == 'bobby':
                self.assertEqual(rule['userName'], 'bobby')
                self.assertEqual(rule['workspace'], 'CA')
                self.assertEqual(rule['layer'], 'CA')
                self.assertEqual(rule['access'], 'LIMIT')

                self.assertTrue('limits' in rule)
                rule_limits = rule['limits']
                self.assertEqual(rule_limits['allowedArea'], 'SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))')
                self.assertEqual(rule_limits['catalogMode'], 'MIXED')
                _limit_rule_position = cnt
            elif rule['userName'] == 'bobby':
                # When there's a limit rule, "*" must be the first one
                self.assertTrue(_limit_rule_position < cnt)

        geo_limit, _ = GroupGeoLimit.objects.get_or_create(
            group=GroupProfile.objects.get(group__name='bar'),
            resource=layer.get_self_resource()
        )
        geo_limit.wkt = 'SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))'
        geo_limit.save()
        layer.groups_geolimits.add(geo_limit)
        self.assertEqual(layer.groups_geolimits.all().count(), 1)

        perm_spec = {
            'users': {}, 'groups': {'bar': ['change_resourcebase']}}
        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 6)

        rules_objs = get_geofence_rules(entries=6)
        self.assertEqual(len(rules_objs['rules']), 6)
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs['rules']):
            if rule['roleName'] == 'ROLE_BAR':
                if rule['service'] is None:
                    self.assertEqual(rule['userName'], None)
                    self.assertEqual(rule['workspace'], 'CA')
                    self.assertEqual(rule['layer'], 'CA')
                    self.assertEqual(rule['access'], 'LIMIT')

                    self.assertTrue('limits' in rule)
                    rule_limits = rule['limits']
                    self.assertEqual(rule_limits['allowedArea'], 'SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))')
                    self.assertEqual(rule_limits['catalogMode'], 'MIXED')
                    _limit_rule_position = cnt
                else:
                    # When there's a limit rule, "*" must be the first one
                    self.assertTrue(_limit_rule_position < cnt)

        # Change Dataset Type and SRID in order to force GeoFence allowed-area reprojection
        _original_subtype = layer.subtype
        _original_srid = layer.srid
        layer.subtype = 'raster'
        layer.srid = 'EPSG:3857'
        layer.save()

        layer.set_permissions(perm_spec)
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 6)

        rules_objs = get_geofence_rules(entries=6)
        self.assertEqual(len(rules_objs['rules']), 6)
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs['rules']):
            if rule['roleName'] == 'ROLE_BAR':
                if rule['service'] is None:
                    self.assertEqual(rule['service'], None)
                    self.assertEqual(rule['userName'], None)
                    self.assertEqual(rule['workspace'], 'CA')
                    self.assertEqual(rule['layer'], 'CA')
                    self.assertEqual(rule['access'], 'LIMIT')

                    self.assertTrue('limits' in rule)
                    rule_limits = rule['limits']
                    self.assertEqual(
                        rule_limits['allowedArea'], 'SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, 146.7000276171853 \
-42.53655428642583, 146.7110139453067 -43.07256577359489, 145.9804231249952 \
-43.05651288026286, 145.8046418749977 -42.49606500060302)))')
                    self.assertEqual(rule_limits['catalogMode'], 'MIXED')
                    _limit_rule_position = cnt
                else:
                    # When there's a limit rule, "*" must be the first one
                    self.assertTrue(_limit_rule_position < cnt)

        layer.subtype = _original_subtype
        layer.srid = _original_srid
        layer.save()

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 0)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_dataset_upload_with_time(self):
        """ Try uploading a layer and verify that the user can administrate
        his own layer despite not being a site administrator.
        """

        # user without change_dataset_style cannot edit it
        self.assertTrue(self.client.login(username='bobby', password='bob'))

        # grab bobby
        bobby = get_user_model().objects.get(username="bobby")
        anonymous_group, created = Group.objects.get_or_create(name='anonymous')

        self.assertTrue(self.client.login(username='bobby', password='bob'))

        title = 'boxes_with_date_by_bobby'
        saved_dataset = create_single_dataset('boxes_with_date.shp')
        saved_dataset = resource_manager.update(
            saved_dataset.uuid,
            instance=saved_dataset,
            notify=False,
            vals=dict(
                owner=bobby,
                title=title
            ))

        # Test that layer owner can wipe GWC Cache
        ignore_errors = True
        skip_unadvertised = False
        skip_geonode_registered = False
        remove_deleted = True
        verbosity = 2
        owner = bobby
        workspace = 'geonode'
        filter = None
        store = None
        permissions = {
            'users': {"bobby": ['view_resourcebase', 'change_dataset_data']},
            'groups': {anonymous_group: ['view_resourcebase']},
        }
        gs_slurp(
            ignore_errors=ignore_errors,
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

        saved_dataset = Dataset.objects.get(name='boxes_with_date.shp')
        check_dataset(saved_dataset)

        from lxml import etree
        from owslib.etree import etree as dlxml
        from geonode.geoserver.helpers import get_store
        from geonode.geoserver.signals import gs_catalog

        self.assertIsNotNone(saved_dataset)
        workspace, name = saved_dataset.alternate.split(':')
        self.assertIsNotNone(workspace)
        self.assertIsNotNone(name)
        ws = gs_catalog.get_workspace(workspace)
        self.assertIsNotNone(ws)
        _gs_dataset_store = saved_dataset.store
        if not _gs_dataset_store:
            saved_dataset.alternate = f"{workspace}:boxes_with_date"
            _gs_dataset = gs_catalog.get_layer(saved_dataset.alternate)
            logger.error(f" ----> fetching layer {saved_dataset.alternate} from GeoServer...: '{_gs_dataset}'")
            self.assertIsNotNone(_gs_dataset)
            _gs_dataset_store = saved_dataset.store = _gs_dataset.resource.store.name
            saved_dataset.save()
        store = get_store(gs_catalog, saved_dataset.store, workspace=ws)
        self.assertIsNotNone(store)

        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']

        rest_path = f'rest/workspaces/{workspace}/datastores/{saved_dataset.store}/featuretypes/boxes_with_date.xml'
        r = requests.get(url + rest_path,
                         auth=HTTPBasicAuth(user, passwd))
        self.assertEqual(r.status_code, 200)
        _log(r.text)

        featureType = etree.ElementTree(dlxml.fromstring(r.text))
        metadata = featureType.findall('./[metadata]')
        self.assertEqual(len(metadata), 1)

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
        self.assertEqual(r.status_code, 200)

        r = requests.get(url + rest_path,
                         auth=HTTPBasicAuth(user, passwd))
        self.assertEqual(r.status_code, 200)
        _log(r.text)

        featureType = etree.ElementTree(dlxml.fromstring(r.text))
        metadata = featureType.findall('./[metadata]')
        _log(etree.tostring(metadata[0], encoding='utf8', method='xml'))
        self.assertEqual(len(metadata), 1)

        saved_dataset.set_permissions(permissions)
        wms_capabilities_url = reverse('capabilities_dataset', args=[saved_dataset.id])
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
                        f"./[wms:Name='{saved_dataset.alternate}']/wms:Dimension[@name='time']", namespaces):
                    dim_name = atype.get('name')
                    if dim_name:
                        dim_name = str(dim_name).lower()
                        if dim_name == 'time':
                            dim_values = atype.text
                            if dim_values:
                                all_times = dim_values.split(",")
                                break

        if all_times:
            self.assertEqual(all_times, [
                '2000-03-01T00:00:00.000Z', '2000-03-02T00:00:00.000Z',
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
                '2000-06-07T00:00:00.000Z', '2000-06-08T00:00:00.000Z',
            ])

        saved_dataset.set_default_permissions()
        url = reverse('dataset_metadata', args=[saved_dataset.service_typename])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_dataset_permissions(self):
        # Test permissions on a layer
        bobby = get_user_model().objects.get(username="bobby")
        layer = create_single_dataset('san_andres_y_providencia_poi')
        layer = resource_manager.update(
            layer.uuid,
            instance=layer,
            notify=False,
            vals=dict(
                owner=bobby,
                workspace=settings.DEFAULT_WORKSPACE
            ))

        self.assertIsNotNone(layer)
        self.assertIsNotNone(layer.ows_url)
        self.assertIsNotNone(layer.ptype)
        self.assertIsNotNone(layer.sourcetype)
        self.assertEqual(layer.alternate, 'geonode:san_andres_y_providencia_poi')

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertEqual(geofence_rules_count, 0)

        layer = Dataset.objects.get(name='san_andres_y_providencia_poi')
        layer.set_default_permissions(owner=bobby)
        check_dataset(layer)
        geofence_rules_count = get_geofence_rules_count()
        _log(f"0. geofence_rules_count: {geofence_rules_count} ")
        self.assertGreaterEqual(geofence_rules_count, 4)

        # Set the layer private for not authenticated users
        perm_spec = {'users': {'AnonymousUser': []}, 'groups': []}
        layer.set_permissions(perm_spec)

        url = f'{settings.SITEURL}gs/ows?' \
            'LAYERS=geonode%3Asan_andres_y_providencia_poi&STYLES=' \
            '&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap' \
            '&SRS=EPSG%3A4326' \
            '&BBOX=-81.394599749999,13.316009005566,' \
            '-81.370560451855,13.372728455566' \
            '&WIDTH=217&HEIGHT=512'

        # test view_resourcebase permission on anonymous user
        response = requests.get(url)
        self.assertTrue(response.status_code, 404)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/vnd.ogc.se_xml;charset=UTF-8'
        )

        # test WMS with authenticated user that has access to the Layer
        response = requests.get(url, auth=HTTPBasicAuth(username=settings.OGC_SERVER['default']['USER'], password=settings.OGC_SERVER['default']['PASSWORD']))
        self.assertTrue(response.status_code, 200)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'image/png'
        )

        # test WMS with authenticated user that has no view_resourcebase:
        # the layer should be not accessible
        response = requests.get(url, auth=HTTPBasicAuth(username='norman', password='norman'))
        self.assertTrue(response.status_code, 404)
        self.assertEqual(
            response.headers.get('Content-Type').strip().replace(" ", ""),
            'text/html;charset=utf-8'
        )

        # test change_dataset_style
        url = f'{settings.GEOSERVER_LOCATION}rest/workspaces/geonode/styles/san_andres_y_providencia_poi.xml'
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

        # user without change_dataset_style cannot edit it
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
        self.assertEqual(response.status_code, 404)

        # user with change_dataset_style can edit it
        perm_spec = {
            'users': {
                'bobby': ['view_resourcebase',
                          'change_resourcebase']
            },
            'groups': []
        }
        layer.set_permissions(perm_spec)
        response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
        # _content_type = response.getheader('Content-Type')
        # self.assertEqual(_content_type, 'image/png')

        # Reset GeoFence Rules
        purge_geofence_all()
        geofence_rules_count = get_geofence_rules_count()
        self.assertTrue(geofence_rules_count == 0)

    def test_maplayers_default_permissions(self):
        """Verify that Dataset.set_default_permissions is behaving as expected
        """

        # Get a Dataset object to work with
        layer = Dataset.objects.first()
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
        if layer.subtype == 'vector':
            self.assertTrue(
                layer.owner.has_perm(
                    'change_dataset_data',
                    layer))

        # Test that the owner user can edit styles
        self.assertTrue(
            layer.owner.has_perm(
                'change_dataset_style',
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

    def test_set_dataset_permissions(self):
        """Verify that the set_dataset_permissions view is behaving as expected
        """

        # Get a layer to work with
        layer = Dataset.objects.first()

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
        self.assertGreaterEqual(len(current_perms['users']), 1)

        # Test that there are no duplicates on returned permissions
        for _k, _v in current_perms.items():
            for _kk, _vv in current_perms[_k].items():
                if _vv and isinstance(_vv, list):
                    _vv_1 = _vv.copy()
                    _vv_2 = list(set(_vv.copy()))
                    _vv_1.sort()
                    _vv_2.sort()
                    self.assertListEqual(
                        _vv_1,
                        _vv_2
                    )

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec['users'].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, layer.get_self_resource()))

    def test_ajax_dataset_permissions(self):
        """Verify that the ajax_dataset_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        valid_dataset_typename = Dataset.objects.all().first().id
        invalid_dataset_id = 9999999

        # Test that an invalid layer.alternate is handled for properly
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    invalid_dataset_id,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEqual(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(
            reverse(
                'resource_permissions',
                args=(
                    valid_dataset_typename,
                )))
        assert('permissions' in ensure_string(response.content))

        # Test that a user is required to have maps.change_dataset_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_dataset_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        self.assertTrue(self.client.login(username='norman', password='norman'))
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_dataset_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_dataset_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")

        # Test that the method returns 200
        self.assertEqual(response.status_code, 200)

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in
        # test_set_dataset_permissions will handle for that?

    def test_perms_info(self):
        """ Verify that the perms_info view is behaving as expected
        """

        # Test with a Dataset object
        layer = Dataset.objects.first()
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
        a_map = Map.objects.first()
        a_map.set_default_permissions()
        perms = get_users_with_perms(a_map)
        self.assertIsNotNone(perms)
        self.assertGreaterEqual(len(perms), 1)

    # now we test permissions, first on an authenticated user and then on the
    # anonymous user
    # 1. view_resourcebase
    # 2. change_resourcebase
    # 3. delete_resourcebase
    # 4. change_resourcebase_metadata
    # 5. change_resourcebase_permissions
    # 6. change_dataset_data
    # 7. change_dataset_style

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
        layer = Dataset.objects.filter(owner=bob).first()
        layer.set_default_permissions()
        # verify bobby has view/change permissions on it but not manage
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase_permissions',
                layer.get_self_resource()))

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log(f"1. geofence_rules_count: {geofence_rules_count} ")
            self.assertGreaterEqual(geofence_rules_count, 12)

        self.assertTrue(self.client.login(username='bobby', password='bob'))

        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that bobby can access the layer
        # detail page
        self.assertTrue(
            bob.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        response = self.client.get(reverse('dataset_embed', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that bobby can not access the
        # layer detail page
        remove_perm('view_resourcebase', bob, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('dataset_embed', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (401, 403))

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that bobby cannot access the
        # layer replace page
        response = self.client.get(reverse('dataset_replace', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)
        # 2.2 has change_resourcebase: verify that bobby can access the layer
        # replace page
        assign_perm('change_resourcebase', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('dataset_replace', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that bobby cannot
        # access the layer metadata page
        response = self.client.get(reverse('dataset_metadata', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)
        # 4.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        assign_perm('change_resourcebase_metadata', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource()))
        response = self.client.get(reverse('dataset_metadata', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            perms = get_users_with_perms(layer)
            _log(f"2. perms: {perms} ")
            sync_geofence_with_guardian(layer, perms, user=bob, group=anonymous_group)

            # Check GeoFence Rules have been correctly created
            geofence_rules_count = get_geofence_rules_count()
            _log(f"3. geofence_rules_count: {geofence_rules_count} ")
            self.assertGreaterEqual(geofence_rules_count, 12)

        # 5. change_resourcebase_permissions
        # should be impossible for the user without change_resourcebase_permissions
        # to change permissions as the permission form is not available in the
        # layer detail page?

        # 6. change_dataset_data
        # must be done in integration test sending a WFS-T request with CURL

        # 7. change_dataset_style
        # 7.1 has not change_dataset_style: verify that bobby cannot access
        # the layer style page
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            response = self.client.get(reverse('dataset_style_manage', args=(layer.alternate,)))
            self.assertEqual(response.status_code, 200)
        # 7.2 has change_dataset_style: verify that bobby can access the
        # change layer style page
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            assign_perm('change_dataset_style', bob, layer)
            self.assertTrue(
                bob.has_perm(
                    'change_dataset_style',
                    layer))
            response = self.client.get(reverse('dataset_style_manage', args=(layer.alternate,)))
            self.assertEqual(response.status_code, 200)

        geofence_rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            purge_geofence_all()
            # Reset GeoFence Rules
            geofence_rules_count = get_geofence_rules_count()
            self.assertEqual(geofence_rules_count, 0)

    def test_anonymus_permissions(self):
        # grab a layer
        layer = Dataset.objects.first()
        layer.set_default_permissions()
        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that anonymous user can access
        # the layer detail page
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('dataset_embed', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that anonymous user can not
        # access the layer detail page
        remove_perm('view_resourcebase', self.anonymous_user, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('dataset_embed', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that anonymous user cannot
        # access the layer replace page but redirected to login
        response = self.client.get(reverse('dataset_replace', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that anonymous user
        # cannot access the layer metadata page but redirected to login
        response = self.client.get(reverse('dataset_metadata', args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 5 N\A? 6 is an integration test...

        # 7. change_dataset_style
        # 7.1 has not change_dataset_style: verify that anonymous user cannot access
        # the layer style page but redirected to login
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            response = self.client.get(reverse('dataset_style_manage', args=(layer.alternate,)))
            self.assertTrue(response.status_code in (302, 403))

    def test_get_visible_resources_should_return_resource_with_metadata_only_false(self):
        layers = Dataset.objects.all()
        actual = get_visible_resources(queryset=layers, user=get_user_model().objects.get(username=self.user))
        self.assertEqual(8, len(actual))

    def test_get_visible_resources_should_return_updated_resource_with_metadata_only_false(self):
        # Updating the layer with metadata only True to verify that the filter works
        x = Dataset.objects.get(title='dataset metadata true')
        x.metadata_only = False
        x.save()
        layers = Dataset.objects.all()
        actual = get_visible_resources(queryset=layers, user=get_user_model().objects.get(username=self.user))
        self.assertEqual(layers.filter(dirty_state=False).count(), len(actual))

    @override_settings(
        ADMIN_MODERATE_UPLOADS=True,
        RESOURCE_PUBLISHING=True,
        GROUP_PRIVATE_RESOURCES=True)
    def test_get_visible_resources_advanced_workflow(self):
        admin_user = get_user_model().objects.get(username="admin")
        standard_user = get_user_model().objects.get(username="bobby")

        self.assertIsNotNone(admin_user)
        self.assertIsNotNone(standard_user)
        admin_user.is_superuser = True
        admin_user.save()
        layers = Dataset.objects.all()

        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=admin_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count() - 1, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count() - 1, actual.count())

        # Test 'is_approved=False' 'is_published=False'
        Dataset.objects.filter(
            ~Q(owner=standard_user)).update(
                is_approved=False, is_published=False)

        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=admin_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count() - 1, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count() - 1, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=None,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(1, actual.count())

        # Test private groups
        private_groups = GroupProfile.objects.filter(
            access="private")
        if private_groups.first():
            private_groups.first().leave(standard_user)
            Dataset.objects.filter(
                ~Q(owner=standard_user)).update(
                    group=private_groups.first().group)
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=admin_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count() - 1, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(8, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=None,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(1, actual.count())

    def test_get_visible_resources(self):
        standard_user = get_user_model().objects.get(username="bobby")
        layers = Dataset.objects.all()
        # update user's perm on a layer,
        # this should not return the layer since it will not be in user's allowed resources
        x = Dataset.objects.get(title='common bar')
        remove_perm('view_resourcebase', standard_user, x.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, x.get_self_resource())
        actual = get_visible_resources(
            queryset=layers,
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True)
        self.assertNotIn(x.title, list(actual.values_list('title', flat=True)))
        # get layers as admin, this should return all layers with metadata_only = True
        actual = get_visible_resources(
            queryset=layers,
            user=get_user_model().objects.get(username=self.user))
        self.assertIn(x.title, list(actual.values_list('title', flat=True)))

    def test_perm_spec_conversion(self):
        """
        Perm Spec from extended to cmpact and viceversa
        """
        standard_user = get_user_model().objects.get(username="bobby")
        dataset = Dataset.objects.filter(owner=standard_user).first()

        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                    'change_dataset_style'
                ]
            },
            'groups': {}
        }

        _p = PermSpec(perm_spec, dataset)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users":
                    {
                        "bobby":
                            [
                                "view_resourcebase",
                                "download_resourcebase",
                                "change_dataset_style"
                            ]
                    },
                "groups": {}
            }
        )

        self.assertDictEqual(
            _p.compact,
            {
                'users':
                [
                    {
                        'id': standard_user.id,
                        'username': standard_user.username,
                        'first_name': standard_user.first_name,
                        'last_name': standard_user.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'owner',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'manage',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups':
                [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'none'
                    },
                    {
                        'id': 2,
                        'name': 'registered-members',
                        'permissions': 'none',
                        'title': 'Registered Members'
                    }
                ]
            }
        )

        perm_spec = {
            'users': {
                'AnonymousUser': [
                    'view_resourcebase'
                ],
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                    'change_dataset_style'
                ]
            },
            'groups': {}
        }

        _p = PermSpec(perm_spec, dataset)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users":
                    {
                        "AnonymousUser": ["view_resourcebase"],
                        "bobby":
                            [
                                "view_resourcebase",
                                "download_resourcebase",
                                "change_dataset_style"
                        ]
                    },
                "groups": {}
            }
        )

        self.assertDictEqual(
            _p.compact,
            {
                'users':
                [
                    {
                        'id': standard_user.id,
                        'username': standard_user.username,
                        'first_name': standard_user.first_name,
                        'last_name': standard_user.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'owner',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'manage',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups':
                [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'view'
                    },
                    {
                        'id': 2,
                        'name': 'registered-members',
                        'permissions': 'none',
                        'title': 'Registered Members'
                    }
                ]
            }
        )

        self.assertTrue(PermSpecCompact.validate(_p.compact))
        _pp = PermSpecCompact(_p.compact, dataset)
        self.assertDictEqual(
            _pp.extended,
            {
                'users':
                    {
                        'bobby':
                        [
                            'change_dataset_data',
                            'change_dataset_style',
                            'change_resourcebase_metadata',
                            'delete_resourcebase',
                            'change_resourcebase_permissions',
                            'publish_resourcebase',
                            'change_resourcebase',
                            'view_resourcebase',
                            'download_resourcebase'
                        ],
                        'admin':
                        [
                            'change_dataset_data',
                            'change_dataset_style',
                            'view_resourcebase',
                            'change_resourcebase_metadata',
                            'delete_resourcebase',
                            'change_resourcebase_permissions',
                            'publish_resourcebase',
                            'change_resourcebase',
                            'download_resourcebase'
                        ],
                        'AnonymousUser': ['view_resourcebase']
                    },
                'groups':
                    {
                        'anonymous': ['view_resourcebase'],
                        'registered-members': []
                    }
            }
        )

        _pp2 = PermSpecCompact({
            "users":
                [
                    {
                        'id': standard_user.id,
                        'username': standard_user.username,
                        'first_name': standard_user.first_name,
                        'last_name': standard_user.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'view',
                    }
                ]
        }, dataset)
        _pp.merge(_pp2)
        self.assertDictEqual(
            _pp.extended,
            {
                'users':
                    {
                        'bobby':
                        [
                            'change_dataset_data',
                            'change_dataset_style',
                            'change_resourcebase_metadata',
                            'delete_resourcebase',
                            'change_resourcebase_permissions',
                            'publish_resourcebase',
                            'change_resourcebase',
                            'view_resourcebase',
                            'download_resourcebase'
                        ],
                        'admin':
                        [
                            'change_dataset_data',
                            'change_dataset_style',
                            'view_resourcebase',
                            'change_resourcebase_metadata',
                            'delete_resourcebase',
                            'change_resourcebase_permissions',
                            'publish_resourcebase',
                            'change_resourcebase',
                            'download_resourcebase'
                        ],
                        'AnonymousUser': ['view_resourcebase']
                    },
                'groups':
                    {
                        'anonymous': ['view_resourcebase'],
                        'registered-members': []
                    }
            }
        )

        # Test "download" permissions retention policy
        # 1. "download" permissions are allowed on "Documents"
        test_document = Document.objects.first()
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                ]
            },
            'groups': {}
        }
        _p = PermSpec(perm_spec, test_document)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users":
                    {
                        "bobby":
                            [
                                "view_resourcebase",
                                "download_resourcebase",
                            ]
                    },
                "groups": {}
            }
        )

        self.assertDictEqual(
            _p.compact,
            {
                'users':
                [
                    {
                        'id': standard_user.id,
                        'username': standard_user.username,
                        'first_name': standard_user.first_name,
                        'last_name': standard_user.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'download',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'owner',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups':
                [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'none'
                    },
                    {
                        'id': 2,
                        'name': 'registered-members',
                        'permissions': 'none',
                        'title': 'Registered Members'
                    }
                ]
            }
        )
        # 2. "download" permissions are NOT allowed on "Maps"
        test_map = Map.objects.first()
        perm_spec = {
            'users': {
                'bobby': [
                    'view_resourcebase',
                    'download_resourcebase',
                ]
            },
            'groups': {}
        }
        _p = PermSpec(perm_spec, test_map)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users":
                    {
                        "bobby":
                            [
                                "view_resourcebase",
                                "download_resourcebase",
                            ]
                    },
                "groups": {}
            }
        )

        self.assertDictEqual(
            _p.compact,
            {
                'users':
                [
                    {
                        'id': standard_user.id,
                        'username': standard_user.username,
                        'first_name': standard_user.first_name,
                        'last_name': standard_user.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'view',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'owner',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups':
                [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'none'
                    },
                    {
                        'id': 2,
                        'name': 'registered-members',
                        'permissions': 'none',
                        'title': 'Registered Members'
                    }
                ]
            }
        )


class SecurityRulesTests(TestCase):
    """
    Test resources synchronization with Guardian and dirty states cleaning
    """

    def setUp(self):
        self.maxDiff = None
        self._l = create_single_dataset("test_dataset")

    def test_sync_resources_with_guardian_delay_false(self):
        with self.settings(DELAYED_SECURITY_SIGNALS=False):
            # Set geofence (and so the dirty state)
            set_geofence_all(self._l)
            # Retrieve the same layer
            dirty_dataset = Dataset.objects.get(pk=self._l.id)
            # Check dirty state (True)
            self.assertFalse(dirty_dataset.dirty_state)
            # Call sync resources
            sync_resources_with_guardian()
            clean_dataset = Dataset.objects.get(pk=self._l.id)
            # Check dirty state
            self.assertFalse(clean_dataset.dirty_state)

    # TODO: DELAYED SECURITY MUST BE REVISED
    def test_sync_resources_with_guardian_delay_true(self):
        with self.settings(DELAYED_SECURITY_SIGNALS=True):
            # Set geofence (and so the dirty state)
            set_geofence_all(self._l)
            # Retrieve the same layer
            dirty_dataset = Dataset.objects.get(pk=self._l.id)
            # Check dirty state (True)
            self.assertTrue(dirty_dataset.dirty_state)
            # Call sync resources
            sync_resources_with_guardian()
            # clean_dataset = Dataset.objects.get(pk=self._l.id)
            # Check dirty state
            # TODO: DELAYED SECURITY MUST BE REVISED
            # self.assertFalse(clean_dataset.dirty_state)


class TestGetUserGeolimits(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.layer = create_single_dataset("main-layer")
        self.owner = get_user_model().objects.get(username='admin')
        self.perms = {'*': ''}
        self.gf_services = _get_gf_services(self.layer, self.perms)

    def test_should_not_disable_cache_for_user_without_geolimits(self):
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(self.layer, self.owner, None, self.gf_services)
        self.assertFalse(_disable_dataset_cache)

    def test_should_disable_cache_for_user_with_geolimits(self):
        geo_limit, _ = UserGeoLimit.objects.get_or_create(
            user=self.owner,
            resource=self.layer
        )
        self.layer.users_geolimits.set([geo_limit])
        self.layer.refresh_from_db()
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(self.layer, self.owner, None, self.gf_services)
        self.assertTrue(_disable_dataset_cache)

    def test_should_not_disable_cache_for_anonymous_without_geolimits(self):
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(self.layer, None, None, self.gf_services)
        self.assertFalse(_disable_dataset_cache)

    def test_should_disable_cache_for_anonymous_with_geolimits(self):
        geo_limit, _ = UserGeoLimit.objects.get_or_create(
            user=get_anonymous_user(),
            resource=self.layer
        )
        self.layer.users_geolimits.set([geo_limit])
        self.layer.refresh_from_db()
        _, _, _disable_dataset_cache, _, _, _ = get_user_geolimits(self.layer, None, None, self.gf_services)
        self.assertTrue(_disable_dataset_cache)


class SetPermissionsTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        # Creating groups and asign also to the anonymous_group
        self.author, created = get_user_model().objects.get_or_create(username="author")
        self.group_manager, created = get_user_model().objects.get_or_create(username="group_manager")
        self.group_member, created = get_user_model().objects.get_or_create(username="group_member")
        self.not_group_member, created = get_user_model().objects.get_or_create(username="not_group_member")

        # Defining group profiles and members
        self.group_profile, created = GroupProfile.objects.get_or_create(slug="custom_group")
        self.second_custom_group, created = GroupProfile.objects.get_or_create(slug="second_custom_group")

        # defining group members
        GroupMember.objects.get_or_create(group=self.group_profile, user=self.author, role="member")
        GroupMember.objects.get_or_create(group=self.group_profile, user=self.group_manager, role="manager")
        GroupMember.objects.get_or_create(group=self.group_profile, user=self.group_member, role="member")
        GroupMember.objects.get_or_create(group=self.second_custom_group, user=self.not_group_member, role="member")

        # Creating he default resource
        self.resource = create_single_dataset(name="test_layer", owner=self.author, group=self.group_profile.group)
        self.anonymous_user = get_anonymous_user()

    @override_settings(RESOURCE_PUBLISHING=False)
    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_set_compact_permissions(self):
        use_cases = [
            (
                PermSpec({
                    "users": {},
                    "groups": {}
                }, self.resource).compact,
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: [],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                PermSpec({
                    "users": {"AnonymousUser": ["view_resourcebase"]},
                    "groups": {"second_custom_group": ["change_resourcebase"]}
                }, self.resource).compact,
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: ["view_resourcebase"],
                    self.not_group_member: [
                        "download_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase",
                    ],
                    self.anonymous_user: ["view_resourcebase"],
                },
            ),
        ]
        for counter, item in enumerate(use_cases):
            permissions, expected = item
            self.resource.set_permissions(permissions)
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #{counter} - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_are_set_as_expected_resource_publishing_True(self):
        use_cases = [
            (
                {"users": {}, "groups": {}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase"
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "change_resourcebase_permissions",
                        "view_resourcebase"
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["download_resourcebase", "view_resourcebase"],
                    self.anonymous_user: ["download_resourcebase", "view_resourcebase"],
                },
            ),
            (
                {"users": [], "groups": {"second_custom_group": ["view_resourcebase"]}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase"
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase"
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["download_resourcebase", "view_resourcebase"],
                    self.anonymous_user: ["download_resourcebase", "view_resourcebase"],
                },
            ),
        ]
        for counter, item in enumerate(use_cases):
            permissions, expected = item
            self.resource.set_permissions(permissions)
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #{counter} - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_are_set_as_expected_admin_upload_resource_publishing_True(self):
        use_cases = [
            (
                {"users": {}, "groups": {}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["download_resourcebase", "view_resourcebase"],
                    self.anonymous_user: ["download_resourcebase", "view_resourcebase"],
                },
            ),
            (
                {"users": {}, "groups": {"second_custom_group": ["view_resourcebase"]}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["download_resourcebase", "view_resourcebase"],
                    self.anonymous_user: ["download_resourcebase", "view_resourcebase"],
                },
            ),
        ]
        for counter, item in enumerate(use_cases):
            permissions, expected = item
            self.resource.set_permissions(permissions)
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #{counter} - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=False)
    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_permissions_are_set_as_expected_admin_upload_resource_publishing_False(self):
        use_cases = [
            (
                {"users": {}, "groups": {}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: [],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                {"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": {"second_custom_group": ["change_resourcebase"]}},
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_member: ["view_resourcebase"],
                    self.not_group_member: ["view_resourcebase", "change_resourcebase"],
                    self.anonymous_user: ["view_resourcebase"],
                },
            ),
        ]
        for counter, item in enumerate(use_cases):
            permissions, expected = item
            self.resource.set_permissions(permissions)
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #{counter} - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_on_user_role_promotion_to_manager(self):
        sut = GroupMember.objects.filter(user=self.group_member)\
            .exclude(group__title='Registered Members')\
            .first()
        self.assertEqual(sut.role, "member")
        sut.promote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "manager")
        expected = {
            self.author: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
            ]
        }
        try:
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}")
        finally:
            sut.demote()

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_on_user_role_demote_to_member(self):
        sut = GroupMember.objects.filter(user=self.group_manager)\
            .exclude(group__title='Registered Members')\
            .first()
        self.assertEqual(sut.role, "manager")
        sut.demote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "member")
        expected = {
            self.author: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
            ],
            self.group_manager: ["download_resourcebase", "view_resourcebase"],
            self.group_member: ["download_resourcebase", "view_resourcebase"]
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_on_user_role_demote_to_member_only_RESOURCE_PUBLISHING_active(self):
        sut = GroupMember.objects.filter(user=self.group_manager)\
            .exclude(group__title='Registered Members')\
            .first()
        self.assertEqual(sut.role, "manager")
        sut.demote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "member")
        expected = {
            self.author: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase"
            ],
            self.group_manager: ["download_resourcebase", "view_resourcebase"],
            self.group_member: ["download_resourcebase", "view_resourcebase"],
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}")

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_on_user_role_promote_to_manager_only_RESOURCE_PUBLISHING_active(self):
        sut = GroupMember.objects.filter(user=self.group_member)\
            .exclude(group__title='Registered Members')\
            .first()
        self.assertEqual(sut.role, "member")
        sut.promote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "manager")
        expected = {
            self.author: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase"
            ],
            self.group_manager: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "change_resourcebase_permissions",
                "publish_resourcebase"
            ],
            self.group_member: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "change_resourcebase_permissions",
                "publish_resourcebase"
            ],
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}")
