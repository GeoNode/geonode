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
import uuid
import os
import requests
import importlib
import mock
import gisdata

from requests.auth import HTTPBasicAuth
from tastypie.test import ResourceTestCaseMixin
from avatar.templatetags.avatar_tags import avatar_url

from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.http import HttpRequest
from django.test.testcases import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from guardian.shortcuts import assign_perm, get_anonymous_user

from geonode import geoserver
from geonode.geoserver.helpers import geofence, gf_utils, gs_catalog
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.layers.utils import get_files
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.documents.models import Document
from geonode.compat import ensure_string
from geonode.utils import check_ogc_backend, build_absolute_uri
from geonode.tests.utils import check_dataset
from geonode.decorators import on_ogc_backend
from geonode.resource.manager import resource_manager
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.groups.models import Group, GroupMember, GroupProfile
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.base.auth import create_auth_token, get_or_create_token

from geonode.base.models import Configuration, UserGeoLimit, GroupGeoLimit
from geonode.base.populate_test_data import (
    all_public,
    create_models,
    create_single_doc,
    create_single_map,
    remove_models,
    create_single_dataset,
)
from geonode.geoserver.security import (
    _get_gf_services,
    allow_layer_to_all,
    delete_all_geofence_rules,
    sync_resources_with_guardian,
    _get_gwc_filters_and_formats,
    has_geolimits,
    create_geofence_rules,
    delete_geofence_rules_for_layer,
)


from .utils import (
    get_users_with_perms,
    get_visible_resources,
)

from .permissions import PermSpec, PermSpecCompact

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
        self.linebuf = ""

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
            settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"] = True

        self.maxDiff = None
        self.user = "admin"
        self.passwd = "admin"
        create_dataset_data()
        self.anonymous_user = get_anonymous_user()
        self.config = Configuration.load()
        self.list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})
        self.bulk_perms_url = reverse("bulk_permissions")
        self.perm_spec = {"users": {"admin": ["view_resourcebase"]}, "groups": []}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.security.middleware import LoginRequiredMiddleware

        middleware = LoginRequiredMiddleware(None)

        white_list = [
            reverse("account_ajax_login"),
            reverse("account_confirm_email", kwargs=dict(key="test")),
            reverse("account_login"),
            reverse("account_reset_password"),
            reverse("forgot_username"),
            reverse("dataset_acls"),
        ]

        black_list = [
            reverse("account_signup"),
            reverse("profile_browse"),
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
                self.assertTrue(response.get("Location").startswith(middleware.redirect_to))

        # The middleware should return None when an un-authenticated user
        # attempts to visit a white-listed url.
        for path in white_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response, msg=f"Middleware activated for white listed path: {path}")

        self.client.login(username="admin", password="admin")
        admin = get_user_model().objects.get(username="admin")
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

        black_listed_url = reverse("load_dataset_data")
        white_listed_url = reverse("account_login")

        # unauthorized request to black listed URL should be redirected to `redirect_to` URL
        request = HttpRequest()
        request.user = get_anonymous_user()

        request.path = black_listed_url
        response = middleware.process_request(request)
        if response:
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.get("Location").startswith(middleware.redirect_to))

        # unauthorized request to white listed URL should be allowed
        request.path = white_listed_url
        response = middleware.process_request(request)
        self.assertIsNone(response, msg=f"Middleware activated for white listed path: {black_listed_url}")

        # Basic authorized request to black listed URL should be allowed
        request.path = black_listed_url
        request.META["HTTP_AUTHORIZATION"] = f'Basic {base64.b64encode(b"bobby:bob").decode("utf-8")}'
        response = middleware.process_request(request)
        self.assertIsNone(response, msg=f"Middleware activated for white listed path: {black_listed_url}")

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_login_middleware_with_custom_login_url(self):
        """
        Tests the Geonode login required authentication middleware with Basic authenticated queries
        """

        site_url_settings = [f"{settings.SITEURL}login/custom", "/login/custom", "login/custom"]
        black_listed_url = reverse("load_dataset_data")

        for setting in site_url_settings:
            with override_settings(LOGIN_URL=setting):
                from geonode.security import middleware as mw

                # reload the middleware module to fetch overridden settings
                importlib.reload(mw)
                middleware = mw.LoginRequiredMiddleware(None)

                # unauthorized request to black listed URL should be redirected to `redirect_to` URL
                request = HttpRequest()
                request.user = AnonymousUser()
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
        from importlib import import_module

        engine = import_module(settings.SESSION_ENGINE)
        middleware = SessionControlMiddleware(None)

        admin = get_user_model().objects.filter(is_superuser=True).first()
        request = HttpRequest()
        request.user = admin
        request.session = engine.SessionStore()
        request.session["access_token"] = get_or_create_token(admin)
        request.session.save()
        middleware.process_request(request)
        self.assertFalse(request.session.is_empty())

        request.session["access_token"] = None
        request.session.save()
        middleware.process_request(request)
        self.assertTrue(request.session.is_empty())

        # Test the full cycle through the client
        path = reverse("account_email")
        self.client.login(username="admin", password="admin")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

        # Simulating Token expired (or not set)
        session_id = self.client.cookies.get(settings.SESSION_COOKIE_NAME)
        session = engine.SessionStore(session_id.value)
        session["access_token"] = None
        session.save()
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_attributes_sats_refresh(self):
        layers = Dataset.objects.all()[:2].values_list("id", flat=True)
        test_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username="admin", password="admin")
        dataset_attributes = test_dataset.attributes
        self.assertIsNotNone(dataset_attributes)
        test_dataset.attribute_set.all().delete()
        test_dataset.save()

        data = {"uuid": test_dataset.uuid}
        resp = self.client.post(reverse("attributes_sats_refresh"), data)
        if resp.status_code == 200:
            self.assertHttpOK(resp)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())

            from geonode.geoserver.helpers import set_attributes_from_geoserver

            test_dataset.attribute_set.all().delete()
            test_dataset.save()

            set_attributes_from_geoserver(test_dataset, overwrite=True)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())

            # Remove permissions to anonymous users and try to refresh attributes again
            test_dataset.set_permissions({"users": {"AnonymousUser": []}, "groups": []})
            test_dataset.attribute_set.all().delete()
            test_dataset.save()

            set_attributes_from_geoserver(test_dataset, overwrite=True)
            self.assertEqual(dataset_attributes.count(), test_dataset.attributes.count())
        else:
            # If GeoServer is unreachable, this view now returns a 302 error
            self.assertEqual(resp.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_invalidate_tileddataset_cache(self):
        layers = Dataset.objects.all()[:2].values_list("id", flat=True)
        test_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username="admin", password="admin")

        data = {"uuid": test_dataset.uuid}
        resp = self.client.post(reverse("invalidate_tileddataset_cache"), data)
        self.assertHttpOK(resp)

    def test_set_bulk_permissions(self):
        """Test that after restrict view permissions on two layers
        bobby is unable to see them"""

        rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            delete_all_geofence_rules()
            # Reset GeoFence Rules
            rules_count = geofence.get_rules_count()
            self.assertEqual(rules_count, 0)

        layers = Dataset.objects.all()[:2].values_list("id", flat=True)
        layers_id = [str(x) for x in layers]
        test_perm_dataset = Dataset.objects.get(id=layers[0])

        self.client.login(username="admin", password="admin")
        resp = self.client.get(self.list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)
        data = {"permissions": json.dumps(self.perm_spec), "resources": layers_id}
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertHttpOK(resp)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            rules_count = geofence.get_rules_count()
            _log(f"1. rules_count: {rules_count} ")
            self.assertGreaterEqual(rules_count, 10)
            allow_layer_to_all(test_perm_dataset)
            rules_count = geofence.get_rules_count()
            _log(f"2. rules_count: {rules_count} ")
            self.assertGreaterEqual(rules_count, 11)

        self.client.logout()

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            self.client.login(username="bobby", password="bob")
            resp = self.client.get(self.list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 6)

            # perms = get_users_with_perms(test_perm_dataset)
            # _log(f"3. perms: {perms} ")
            # batch = AutoPriorityBatch(get_first_available_priority(), f'test batch for {test_perm_dataset}')
            # for u, p in perms.items():
            #     create_geofence_rules(test_perm_dataset, p, user=u, batch=batch)
            # geofence.run_batch(batch)

            # Check GeoFence Rules have been correctly created
            rules_count = geofence.get_rules_count()
            _log(f"4. rules_count: {rules_count} ")
            self.assertGreaterEqual(rules_count, 13)

            # Validate maximum priority
            available_priority = gf_utils.get_first_available_priority()
            _log(f"5. available_priority: {available_priority} ")
            self.assertTrue(available_priority > 0)

            url = settings.OGC_SERVER["default"]["LOCATION"]
            user = settings.OGC_SERVER["default"]["USER"]
            passwd = settings.OGC_SERVER["default"]["PASSWORD"]

            test_url = f"{url}gwc/rest/seed/{test_perm_dataset.alternate}.json"
            r = requests.get(test_url, auth=HTTPBasicAuth(user, passwd))
            self.assertEqual(r.status_code, 400, f"GWC error for user: {user} URL: {test_url}\n{r.text}")

        rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            delete_all_geofence_rules()
            # Reset GeoFence Rules
            rules_count = geofence.get_rules_count()
            self.assertEqual(rules_count, 0)

    def test_bobby_cannot_set_all(self):
        """Test that Bobby can set the permissions only on the ones
        for which he has the right"""
        bobby = get_user_model().objects.get(username="bobby")
        layer = Dataset.objects.all().exclude(owner=bobby)[0]
        self.client.login(username="admin", password="admin")
        # give bobby the right to change the layer permissions
        assign_perm("change_resourcebase_permissions", bobby, layer.get_self_resource())
        self.client.logout()
        self.client.login(username="bobby", password="bob")
        layer2 = Dataset.objects.all().exclude(owner=bobby)[1]
        data = {
            "permissions": json.dumps({"users": {"bobby": ["view_resourcebase"]}, "groups": []}),
            "resources": [layer.id, layer2.id],
        }
        resp = self.client.post(self.bulk_perms_url, data)
        content = resp.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        self.assertNotIn(layer.title, json.loads(content)["not_changed"])
        self.assertIn(layer2.title, json.loads(content)["not_changed"])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_user_can(self):
        bobby = get_user_model().objects.get(username="bobby")
        perm_spec = {
            "users": {
                "bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_data", "change_dataset_style"]
            },
            "groups": [],
        }
        dataset = Dataset.objects.filter(subtype="vector").first()
        dataset.set_permissions(perm_spec)
        # Test user has permission with read_only=False
        self.assertTrue(dataset.user_can(bobby, "change_dataset_style"))
        # Test with edit permission and read_only=True
        self.config.read_only = True
        self.config.save()
        self.assertFalse(dataset.user_can(bobby, "change_dataset_style"))
        # Test with view permission and read_only=True
        self.assertTrue(dataset.user_can(bobby, "view_resourcebase"))
        # Test on a 'raster' subtype
        self.config.read_only = False
        self.config.save()
        dataset = Dataset.objects.filter(subtype="raster").first()
        dataset.set_permissions(perm_spec)
        # Test user has permission with read_only=False
        self.assertFalse(dataset.user_can(bobby, "change_dataset_data"))
        self.assertTrue(dataset.user_can(bobby, "change_dataset_style"))

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_perm_specs_synchronization(self):
        """Test that Dataset is correctly synchronized with guardian:
        1. Set permissions to all users
        2. Set permissions to a single user
        3. Set permissions to a group of users
        4. Try to sync a layer from GeoServer
        """
        bobby = get_user_model().objects.get(username="bobby")
        layer = Dataset.objects.filter(subtype="vector").exclude(owner=bobby).first()
        self.client.login(username="admin", password="admin")

        # Reset GeoFence Rules
        delete_all_geofence_rules()
        self.assertEqual(geofence.get_rules_count(), 0)

        perm_spec = {"users": {"AnonymousUser": []}, "groups": []}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        _log(f"1. rules_count: {rules_count} ")
        self.assertEqual(rules_count, 5)

        perm_spec = {"users": {"admin": ["view_resourcebase"]}, "groups": []}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        _log(f"2. rules_count: {rules_count} ")
        self.assertEqual(rules_count, 9, f"Bad rules count. Got rules: {geofence.get_rules()}")

        perm_spec = {"users": {"admin": ["change_dataset_data"]}, "groups": []}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        _log(f"3. rules_count: {rules_count} ")
        self.assertEqual(rules_count, 8, f"Bad rules count. Got rules: {geofence.get_rules()}")

        rules_objs = geofence.get_rules()
        wps_subfield_found = False
        for rule in rules_objs["rules"]:
            if rule["service"] == "WPS" and rule["subfield"] == "GS:DOWNLOAD":
                wps_subfield_found = rule["access"] == "DENY"
                break
        self.assertTrue(wps_subfield_found, f"WPS download not blocked. Got rules: {geofence.get_rules()}")

        # FULL WFS-T
        perm_spec = {
            "users": {
                "bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_style", "change_dataset_data"]
            },
            "groups": [],
        }
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 10)

        rules_objs = geofence.get_rules()
        _deny_wfst_rule_exists = False
        for rule in rules_objs["rules"]:
            if rule["service"] == "WFS" and rule["userName"] == "bobby" and rule["request"] == "TRANSACTION":
                _deny_wfst_rule_exists = rule["access"] == "DENY"
                break
        self.assertFalse(_deny_wfst_rule_exists)

        # NO WFS-T
        # - order is important
        perm_spec = {
            "users": {
                "bobby": [
                    "view_resourcebase",
                    "download_resourcebase",
                ]
            },
            "groups": [],
        }
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 13)

        rules_objs = geofence.get_rules()
        _deny_wfst_rule_exists = False
        _deny_wfst_rule_position = -1
        _allow_wfs_rule_position = -1
        for cnt, rule in enumerate(rules_objs["rules"]):
            if rule["service"] == "WFS" and rule["userName"] == "bobby" and rule["request"] == "TRANSACTION":
                _deny_wfst_rule_exists = rule["access"] == "DENY"
                _deny_wfst_rule_position = cnt
            elif (
                rule["service"] == "WFS"
                and rule["userName"] == "bobby"
                and (rule["request"] is None or rule["request"] == "*")
            ):
                _allow_wfs_rule_position = cnt
        self.assertTrue(_deny_wfst_rule_exists)
        self.assertTrue(_allow_wfs_rule_position > _deny_wfst_rule_position)

        # NO WFS
        perm_spec = {
            "users": {
                "bobby": [
                    "view_resourcebase",
                ]
            },
            "groups": [],
        }
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 9)

        rules_objs = geofence.get_rules()
        _deny_wfst_rule_exists = False
        for rule in rules_objs["rules"]:
            if rule["service"] == "WFS" and rule["userName"] == "bobby" and rule["request"] == "TRANSACTION":
                _deny_wfst_rule_exists = rule["access"] == "DENY"
                break
        self.assertFalse(_deny_wfst_rule_exists)

        perm_spec = {"users": {}, "groups": {"bar": ["view_resourcebase"]}}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        _log(f"4. rules_count: {rules_count} ")
        self.assertEqual(rules_count, 9, f"Bad rule count, got rules {geofence.get_rules()}")

        perm_spec = {"users": {}, "groups": {"bar": ["change_resourcebase"]}}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        _log(f"5. rules_count: {rules_count} ")
        self.assertEqual(rules_count, 5)

        # Testing GeoLimits
        # Reset GeoFence Rules
        delete_all_geofence_rules()
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 0)
        layer = Dataset.objects.first()
        # grab bobby
        bobby = get_user_model().objects.get(username="bobby")
        _disable_dataset_cache = has_geolimits(layer, None, None)
        filters, formats = _get_gwc_filters_and_formats(_disable_dataset_cache)
        self.assertListEqual(filters, [{"styleParameterFilter": {"STYLES": ""}}])
        self.assertListEqual(
            formats,
            [
                "application/json;type=utfgrid",
                "image/gif",
                "image/jpeg",
                "image/png",
                "image/png8",
                "image/vnd.jpeg-png",
                "image/vnd.jpeg-png8",
            ],
        )

        geo_limit, _ = UserGeoLimit.objects.get_or_create(user=bobby, resource=layer.get_self_resource())
        geo_limit.wkt = "SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))"
        geo_limit.save()
        layer.users_geolimits.add(geo_limit)
        self.assertEqual(layer.users_geolimits.all().count(), 1)
        _disable_dataset_cache = has_geolimits(layer, bobby, None)
        filters, formats = _get_gwc_filters_and_formats([_disable_dataset_cache])
        self.assertIsNone(filters)
        self.assertIsNone(formats)

        perm_spec = {"users": {"bobby": ["view_resourcebase"]}, "groups": []}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 10)

        rules_objs = geofence.get_rules()
        self.assertEqual(len(rules_objs["rules"]), 10)
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs["rules"]):
            if rule["service"] is None and rule["userName"] == "bobby":
                self.assertEqual(rule["userName"], "bobby")
                self.assertEqual(rule["workspace"], "geonode")
                self.assertEqual(rule["layer"], "CA")
                self.assertEqual(rule["access"], "LIMIT")

                self.assertTrue("limits" in rule)
                rule_limits = rule["limits"]
                self.assertEqual(
                    rule_limits["allowedArea"],
                    "SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))",
                )
                self.assertEqual(rule_limits["catalogMode"], "MIXED")
                _limit_rule_position = cnt
            elif rule["userName"] == "bobby":
                # When there's a limit rule, "*" must be the first one
                self.assertTrue(_limit_rule_position < cnt)

        geo_limit, _ = GroupGeoLimit.objects.get_or_create(
            group=GroupProfile.objects.get(group__name="bar"), resource=layer.get_self_resource()
        )
        geo_limit.wkt = "SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))"
        geo_limit.save()
        layer.groups_geolimits.add(geo_limit)
        self.assertEqual(layer.groups_geolimits.all().count(), 1)

        perm_spec = {"users": {}, "groups": {"bar": ["change_resourcebase"]}}
        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 6)

        rules_objs = geofence.get_rules()
        self.assertEqual(len(rules_objs["rules"]), 6)
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs["rules"]):
            if rule["roleName"] == "ROLE_BAR":
                if rule["service"] is None:
                    self.assertEqual(rule["userName"], None)
                    self.assertEqual(rule["workspace"], "geonode")
                    self.assertEqual(rule["layer"], "CA")
                    self.assertEqual(rule["access"], "LIMIT")

                    self.assertTrue("limits" in rule)
                    rule_limits = rule["limits"]
                    self.assertEqual(
                        rule_limits["allowedArea"],
                        "SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, \
146.7000276171853 -42.53655428642583, 146.7110139453067 -43.07256577359489, \
145.9804231249952 -43.05651288026286, 145.8046418749977 -42.49606500060302)))",
                    )
                    self.assertEqual(rule_limits["catalogMode"], "MIXED")
                    _limit_rule_position = cnt
                else:
                    # When there's a limit rule, "*" must be the first one
                    self.assertTrue(_limit_rule_position < cnt)

        # Change Dataset Type and SRID in order to force GeoFence allowed-area reprojection
        _original_subtype = layer.subtype
        _original_srid = layer.srid
        layer.subtype = "raster"
        layer.srid = "EPSG:3857"
        layer.save()

        layer.set_permissions(perm_spec)
        rules_count = geofence.get_rules_count()

        rules_objs = geofence.get_rules()
        # Order is important
        _limit_rule_position = -1
        for cnt, rule in enumerate(rules_objs["rules"]):
            if rule["roleName"] == "ROLE_BAR":
                if rule["service"] is None:
                    self.assertEqual(rule["service"], None)
                    self.assertEqual(rule["userName"], None)
                    self.assertEqual(rule["workspace"], "geonode")
                    self.assertEqual(rule["layer"], "CA")
                    self.assertEqual(rule["access"], "LIMIT")

                    self.assertTrue("limits" in rule)
                    rule_limits = rule["limits"]
                    self.assertEqual(
                        rule_limits["allowedArea"],
                        "SRID=4326;MULTIPOLYGON (((145.8046418749977 -42.49606500060302, 146.7000276171853 \
-42.53655428642583, 146.7110139453067 -43.07256577359489, 145.9804231249952 \
-43.05651288026286, 145.8046418749977 -42.49606500060302)))",
                    )
                    self.assertEqual(rule_limits["catalogMode"], "MIXED")
                    _limit_rule_position = cnt
                else:
                    # When there's a limit rule, "*" must be the first one
                    self.assertTrue(_limit_rule_position < cnt)

        layer.subtype = _original_subtype
        layer.srid = _original_srid
        layer.save()

        # Reset GeoFence Rules
        delete_all_geofence_rules()
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 0)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_dataset_permissions(self):
        # Test permissions on a layer
        files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_poi.shp")
        files_as_dict, self.tmpdir = get_files(files)

        bobby = get_user_model().objects.get(username="bobby")
        layer = create_single_dataset(
            "san_andres_y_providencia_poi",
            {
                "owner": self.user,
                "title": "Testing Dataset",
                "data_title": "relief_san_andres",
                "data_type": "tif",
            },
        )
        layer = resource_manager.update(
            layer.uuid, instance=layer, notify=False, vals=dict(owner=bobby, workspace=settings.DEFAULT_WORKSPACE)
        )

        self.assertIsNotNone(layer)
        self.assertIsNotNone(layer.ows_url)
        self.assertIsNotNone(layer.ptype)
        self.assertIsNotNone(layer.sourcetype)
        self.assertEqual(layer.alternate, "geonode:san_andres_y_providencia_poi")

        # Reset GeoFence Rules
        delete_all_geofence_rules()
        rules_count = geofence.get_rules_count()
        self.assertEqual(rules_count, 0)

        layer = Dataset.objects.get(name="san_andres_y_providencia_poi")
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)
        layer.set_default_permissions(owner=bobby)
        check_dataset(layer)
        rules_count = geofence.get_rules_count()
        _log(f"0. rules_count: {rules_count} ")
        self.assertGreaterEqual(rules_count, 4)

        # Set the layer private for not authenticated users
        perm_spec = {"users": {"AnonymousUser": []}, "groups": []}
        layer.set_permissions(perm_spec)

        gs_layer = gs_catalog.get_layer("3Asan_andres_y_providencia_poi")
        if gs_layer is None:
            GeoServerResourceManager()._execute_resource_import(
                layer,
                list(files_as_dict.values()),
                get_user_model().objects.get(username="admin"),
                action_type="create",
            )

        url = (
            f"{settings.GEOSERVER_LOCATION}ows?"
            "LAYERS=geonode%3Asan_andres_y_providencia_poi&STYLES="
            "&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap"
            "&SRS=EPSG%3A4326"
            "&BBOX=-81.394599749999,13.316009005566,"
            "-81.370560451855,13.372728455566"
            "&WIDTH=217&HEIGHT=512"
        )

        # test view_resourcebase permission on anonymous user
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Could not find layer" in response.content)
        self.assertEqual(response.headers.get("Content-Type"), "application/vnd.ogc.se_xml;charset=UTF-8")

        # test WMS with authenticated user that has access to the Dataset
        response = requests.get(
            url,
            auth=HTTPBasicAuth(
                username=settings.OGC_SERVER["default"]["USER"], password=settings.OGC_SERVER["default"]["PASSWORD"]
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "image/png")

        # test WMS with authenticated user that has no view_resourcebase:
        # the layer should be not accessible
        response = requests.get(url, auth=HTTPBasicAuth(username="norman", password="norman"))
        self.assertTrue(response.status_code, 404)
        self.assertEqual(response.headers.get("Content-Type").strip().replace(" ", ""), "text/html;charset=utf-8")

        # test change_dataset_style
        url = f"{settings.GEOSERVER_LOCATION}rest/workspaces/geonode/styles/san_andres_y_providencia_poi.xml"
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
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.put(url, sld, content_type="application/vnd.ogc.sld+xml")
        self.assertEqual(response.status_code, 404)

        # user with change_dataset_style can edit it
        perm_spec = {"users": {"bobby": ["view_resourcebase", "change_resourcebase"]}, "groups": []}
        layer.set_permissions(perm_spec)
        response = self.client.put(url, sld, content_type="application/vnd.ogc.sld+xml")
        # _content_type = response.getheader('Content-Type')
        # self.assertEqual(_content_type, 'image/png')

        # Reset GeoFence Rules
        delete_all_geofence_rules()
        rules_count = geofence.get_rules_count()
        self.assertTrue(rules_count == 0)

    def test_maplayers_default_permissions(self):
        """Verify that Dataset.set_default_permissions is behaving as expected"""

        # Get a Dataset object to work with
        layer = Dataset.objects.first()
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)
        # Set the default permissions
        layer.set_default_permissions()

        # Test that the anonymous user can read
        self.assertTrue(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))

        # Test that the owner user can read
        self.assertTrue(layer.owner.has_perm("view_resourcebase", layer.get_self_resource()))

        # Test that the owner user can download it
        self.assertTrue(layer.owner.has_perm("download_resourcebase", layer.get_self_resource()))

        # Test that the owner user can edit metadata
        self.assertTrue(layer.owner.has_perm("change_resourcebase_metadata", layer.get_self_resource()))

        # Test that the owner user can edit data if is vector type
        if layer.subtype == "vector":
            self.assertTrue(layer.owner.has_perm("change_dataset_data", layer))

        # Test that the owner user can edit styles
        self.assertTrue(layer.owner.has_perm("change_dataset_style", layer))

        # Test that the owner can manage the layer
        self.assertTrue(layer.owner.has_perm("change_resourcebase", layer.get_self_resource()))
        self.assertTrue(layer.owner.has_perm("delete_resourcebase", layer.get_self_resource()))
        self.assertTrue(layer.owner.has_perm("change_resourcebase_permissions", layer.get_self_resource()))
        self.assertTrue(layer.owner.has_perm("publish_resourcebase", layer.get_self_resource()))

    def test_set_dataset_permissions(self):
        """Verify that the set_dataset_permissions view is behaving as expected"""

        # Get a layer to work with
        layer = Dataset.objects.first()
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)

        # FIXME Test a comprehensive set of permissions specifications

        # Set the Default Permissions
        layer.set_default_permissions()

        # Test that the Permissions for anonymous user are set
        self.assertTrue(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))

        # Set the Permissions
        layer.set_permissions(self.perm_spec)

        # Test that the Permissions for anonymous user are un-set
        self.assertFalse(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        current_perms = layer.get_all_level_info()
        self.assertGreaterEqual(len(current_perms["users"]), 1)

        # Test that there are no duplicates on returned permissions
        for _k, _v in current_perms.items():
            for _kk, _vv in current_perms[_k].items():
                if _vv and isinstance(_vv, list):
                    _vv_1 = _vv.copy()
                    _vv_2 = list(set(_vv.copy()))
                    _vv_1.sort()
                    _vv_2.sort()
                    self.assertListEqual(_vv_1, _vv_2)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec["users"].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, layer.get_self_resource()))

    def test_ajax_dataset_permissions(self):
        """Verify that the ajax_dataset_permissions view is behaving as expected"""

        # Setup some layer names to work with
        valid_dataset_typename = Dataset.objects.all().first().id
        invalid_dataset_id = 9999999

        # Test that an invalid layer.alternate is handled for properly
        response = self.client.post(
            reverse("resource_permissions", args=(invalid_dataset_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(reverse("resource_permissions", args=(valid_dataset_typename,)))
        assert "permissions" in ensure_string(response.content)

        # Test that a user is required to have maps.change_dataset_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse("resource_permissions", args=(valid_dataset_typename,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        self.assertTrue(self.client.login(username="norman", password="norman"))
        response = self.client.post(
            reverse("resource_permissions", args=(valid_dataset_typename,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(
            reverse("resource_permissions", args=(valid_dataset_typename,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )

        # Test that the method returns 200
        self.assertEqual(response.status_code, 200)

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in
        # test_set_dataset_permissions will handle for that?

    def test_perms_info(self):
        """Verify that the perms_info view is behaving as expected"""
        # Test with a Dataset object
        layer = Dataset.objects.first()
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)
        layer.set_default_permissions()
        # Test that the anonymous user can read
        self.assertTrue(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))

        # Test that layer owner can edit layer
        self.assertTrue(layer.owner.has_perm("change_resourcebase", layer.get_self_resource()))

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
        rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            delete_all_geofence_rules()
            # Reset GeoFence Rules
            rules_count = geofence.get_rules_count()
            self.assertTrue(rules_count == 0)

        # grab bobby
        bob = get_user_model().objects.get(username="bobby")

        # grab a layer
        layer = Dataset.objects.exclude(owner=bob).first()
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)
        layer.set_default_permissions()
        # verify bobby has view permissions on it
        self.assertTrue(bob.has_perm("view_resourcebase", layer.get_self_resource()))

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Check GeoFence Rules have been correctly created
            rules_count = geofence.get_rules_count()
            _log(f"1. rules_count: {rules_count} ")

        self.assertTrue(self.client.login(username="bobby", password="bob"))

        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that bobby can access the layer
        # detail page
        self.assertTrue(bob.has_perm("view_resourcebase", layer.get_self_resource()))

        response = self.client.get(reverse("dataset_embed", args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200, response.status_code)
        # 1.2 has not view_resourcebase: verify that bobby can not access the
        # layer detail page
        layer.set_permissions({"users": {"AnonymousUser": []}, "groups": []})
        Group.objects.get(name="anonymous")
        response = self.client.get(reverse("dataset_embed", args=(layer.alternate,)))
        self.assertTrue(response.status_code in (401, 403), response.status_code)

        # 3. change_resourcebase_metadata
        # 3.1 has not change_resourcebase_metadata: verify that bobby cannot
        # access the layer metadata page
        response = self.client.get(reverse("dataset_metadata", args=(layer.alternate,)))
        self.assertTrue(response.status_code in (401, 403), response.status_code)
        # 3.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        layer.set_permissions(
            {
                "users": {"bobby": ["change_resourcebase", "change_resourcebase_metadata", "delete_resourcebase"]},
                "groups": [],
            }
        )
        self.assertTrue(bob.has_perm("change_resourcebase_metadata", layer.get_self_resource()))
        response = self.client.get(reverse("dataset_metadata", args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200, response.status_code)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            perms = get_users_with_perms(layer)
            _log(f"2. perms: {perms} ")
            batch = create_geofence_rules(layer, perms, user=bob)
            geofence.run_batch(batch)

            # Check GeoFence Rules have been correctly created
            rules_count = geofence.get_rules_count()
            _log(f"3. rules_count: {rules_count} ")

        # 4. change_resourcebase_permissions
        # should be impossible for the user without change_resourcebase_permissions
        # to change permissions as the permission form is not available in the
        # layer detail page?

        # 5. change_dataset_data
        # must be done in integration test sending a WFS-T request with CURL

        # 6. change_dataset_style
        # 6.1 has not change_dataset_style: verify that bobby cannot access
        # the layer style page
        # 7.2 has change_dataset_style: verify that bobby can access the
        # change layer style page
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # Only for geoserver backend
            layer.set_permissions(
                {
                    "users": {
                        "bobby": [
                            "change_resourcebase",
                            "change_resourcebase_metadata",
                            "delete_resourcebase",
                            "change_dataset_style",
                        ]
                    },
                    "groups": [],
                }
            )
            self.assertTrue(bob.has_perm("change_dataset_style", layer))

        rules_count = 0
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            delete_all_geofence_rules()
            # Reset GeoFence Rules
            rules_count = geofence.get_rules_count()
            self.assertEqual(rules_count, 0, rules_count)

    def test_anonymus_permissions(self):
        # grab a layer
        layer = Dataset.objects.first()
        # removing duplicates
        while Dataset.objects.filter(alternate=layer.alternate).count() > 1:
            Dataset.objects.filter(alternate=layer.alternate).last().delete()
        layer = Dataset.objects.get(alternate=layer.alternate)
        layer.set_default_permissions()
        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that anonymous user can access
        # the layer detail page
        self.assertTrue(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))
        response = self.client.get(reverse("dataset_embed", args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that anonymous user can not
        # access the layer detail page
        layer.set_permissions({"users": {"AnonymousUser": []}, "groups": []})
        response = self.client.get(reverse("dataset_embed", args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

        # 3. change_resourcebase_metadata
        # 3.1 has not change_resourcebase_metadata: verify that anonymous user
        # cannot access the layer metadata page but redirected to login
        response = self.client.get(reverse("dataset_metadata", args=(layer.alternate,)))
        self.assertTrue(response.status_code in (302, 403))

    def test_get_visible_resources_should_return_resource_with_metadata_only_false(self):
        layers = Dataset.objects.all()
        actual = get_visible_resources(queryset=layers, user=get_user_model().objects.get(username=self.user))
        self.assertEqual(8, len(actual))

    def test_get_visible_resources_should_return_updated_resource_with_metadata_only_false(self):
        # Updating the layer with metadata only True to verify that the filter works
        Dataset.objects.filter(title="dataset metadata true").update(metadata_only=False)
        layers = Dataset.objects.all()
        actual = get_visible_resources(queryset=layers, user=get_user_model().objects.get(username=self.user))
        self.assertEqual(layers.filter(dirty_state=False).count(), len(actual))

    def test_get_visible_resources_should_return_resource_with_metadata_only_true(self):
        """
        If metadata only is provided, it should return only the metadata resources
        """
        try:
            dataset = create_single_dataset("dataset_with_metadata_only_True")
            dataset.metadata_only = True
            dataset.save()

            layers = Dataset.objects.all()
            actual = get_visible_resources(
                queryset=layers, metadata_only=True, user=get_user_model().objects.get(username=self.user)
            )
            self.assertEqual(1, actual.count())
        finally:
            if dataset:
                dataset.delete()

    def test_get_visible_resources_should_return_resource_with_metadata_only_none(self):
        """
        If metadata only is provided, it should return only the metadata resources
        """
        try:
            dataset = create_single_dataset("dataset_with_metadata_only_True")
            dataset.metadata_only = True
            dataset.save()

            layers = Dataset.objects.all()
            actual = get_visible_resources(
                queryset=layers, metadata_only=None, user=get_user_model().objects.get(username=self.user)
            )
            self.assertEqual(layers.count(), actual.count())
        finally:
            if dataset:
                dataset.delete()

    @override_settings(ADMIN_MODERATE_UPLOADS=True, RESOURCE_PUBLISHING=True, GROUP_PRIVATE_RESOURCES=True)
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
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count(), actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count(), actual.count())

        # Test 'is_approved=False' 'is_published=False'
        Dataset.objects.filter(~Q(owner=standard_user)).update(is_approved=False, is_published=False)

        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=admin_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count(), actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count(), actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=None,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(1, actual.count())

        # Test private groups
        private_groups = GroupProfile.objects.filter(access="private")
        if private_groups.first():
            private_groups.first().leave(standard_user)
            Dataset.objects.filter(~Q(owner=standard_user)).update(group=private_groups.first().group)
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=admin_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(layers.count(), actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(8, actual.count())
        actual = get_visible_resources(
            queryset=Dataset.objects.all(),
            user=None,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        # The method returns only 'metadata_only=False' resources
        self.assertEqual(1, actual.count())

    def test_get_visible_resources(self):
        standard_user = get_user_model().objects.get(username="bobby")
        layers = Dataset.objects.all()
        # update user's perm on a layer,
        # this should not return the layer since it will not be in user's allowed resources
        _title = "common bar"
        for x in Dataset.objects.filter(title=_title):
            x.set_permissions({"users": {"bobby": []}, "groups": []})
        actual = get_visible_resources(
            queryset=layers,
            user=standard_user,
            admin_approval_required=True,
            unpublished_not_visible=True,
            private_groups_not_visibile=True,
        )
        self.assertNotIn(_title, list(actual.values_list("title", flat=True)))
        # get layers as admin, this should return all layers with metadata_only = True
        actual = get_visible_resources(queryset=layers, user=get_user_model().objects.get(username=self.user))
        self.assertIn(_title, list(actual.values_list("title", flat=True)))

    def test_perm_spec_conversion(self):
        """
        Perm Spec from extended to cmpact and viceversa
        """
        standard_user = get_user_model().objects.get(username="bobby")
        dataset = Dataset.objects.filter(owner=standard_user).first()

        perm_spec = {
            "users": {"bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_style"]},
            "groups": {},
        }

        _p = PermSpec(perm_spec, dataset)
        self.assertDictEqual(
            json.loads(str(_p)),
            {"users": {"bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_style"]}, "groups": {}},
        )

        self.assertDictEqual(
            _p.compact,
            {
                "users": [
                    {
                        "id": standard_user.id,
                        "username": standard_user.username,
                        "first_name": standard_user.first_name,
                        "last_name": standard_user.last_name,
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "permissions": "owner",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "manage",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "none"},
                    {"id": 2, "name": "registered-members", "permissions": "none", "title": "Registered Members"},
                ],
            },
        )

        perm_spec = {
            "users": {
                "AnonymousUser": ["view_resourcebase"],
                "bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_style"],
            },
            "groups": {},
        }

        _p = PermSpec(perm_spec, dataset)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users": {
                    "AnonymousUser": ["view_resourcebase"],
                    "bobby": ["view_resourcebase", "download_resourcebase", "change_dataset_style"],
                },
                "groups": {},
            },
        )

        self.assertDictEqual(
            _p.compact,
            {
                "users": [
                    {
                        "id": standard_user.id,
                        "username": standard_user.username,
                        "first_name": standard_user.first_name,
                        "last_name": standard_user.last_name,
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "permissions": "owner",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "manage",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                    {"id": 2, "name": "registered-members", "permissions": "none", "title": "Registered Members"},
                ],
            },
        )

        self.assertTrue(PermSpecCompact.validate(_p.compact))
        _pp = PermSpecCompact(_p.compact, dataset)
        _pp_e = {
            "users": {
                "bobby": [
                    "change_dataset_style",
                    "publish_resourcebase",
                    "delete_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_permissions",
                    "view_resourcebase",
                    "change_dataset_data",
                ],
                "admin": [
                    "change_dataset_style",
                    "publish_resourcebase",
                    "delete_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_permissions",
                    "view_resourcebase",
                    "change_dataset_data",
                ],
                "AnonymousUser": ["view_resourcebase"],
            },
            "groups": {"anonymous": ["view_resourcebase"], "registered-members": []},
        }
        self.assertListEqual(list(_pp.extended.keys()), list(_pp_e.keys()))
        for _key in _pp.extended.keys():
            self.assertListEqual(list(_pp.extended.get(_key).keys()), list(_pp_e.get(_key).keys()))
            for __key in _pp.extended.get(_key).keys():
                self.assertListEqual(
                    sorted(list(set(_pp.extended.get(_key).get(__key)))), sorted(list(set(_pp_e.get(_key).get(__key))))
                )

        _pp2 = PermSpecCompact(
            {
                "users": [
                    {
                        "id": standard_user.id,
                        "username": standard_user.username,
                        "first_name": standard_user.first_name,
                        "last_name": standard_user.last_name,
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "permissions": "view",
                    }
                ]
            },
            dataset,
        )
        _pp.merge(_pp2)
        _pp_e = {
            "users": {
                "bobby": [
                    "change_resourcebase_permissions",
                    "change_resourcebase_metadata",
                    "change_dataset_data",
                    "change_resourcebase",
                    "delete_resourcebase",
                    "publish_resourcebase",
                    "download_resourcebase",
                    "change_dataset_style",
                    "view_resourcebase",
                ],
                "admin": [
                    "change_resourcebase_permissions",
                    "change_resourcebase_metadata",
                    "change_dataset_data",
                    "change_resourcebase",
                    "delete_resourcebase",
                    "publish_resourcebase",
                    "download_resourcebase",
                    "change_dataset_style",
                    "view_resourcebase",
                ],
                "AnonymousUser": ["view_resourcebase"],
            },
            "groups": {"anonymous": ["view_resourcebase"], "registered-members": []},
        }
        self.assertListEqual(list(_pp.extended.keys()), list(_pp_e.keys()))
        for _key in _pp.extended.keys():
            self.assertListEqual(list(_pp.extended.get(_key).keys()), list(_pp_e.get(_key).keys()))
            for __key in _pp.extended.get(_key).keys():
                self.assertListEqual(
                    sorted(list(set(_pp.extended.get(_key).get(__key)))), sorted(list(set(_pp_e.get(_key).get(__key))))
                )

        # Test "download" permissions retention policy
        # 1. "download" permissions are allowed on "Documents"
        test_document = Document.objects.first()
        perm_spec = {
            "users": {
                "bobby": [
                    "view_resourcebase",
                    "download_resourcebase",
                ]
            },
            "groups": {},
        }
        _p = PermSpec(perm_spec, test_document)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users": {
                    "bobby": [
                        "view_resourcebase",
                        "download_resourcebase",
                    ]
                },
                "groups": {},
            },
            json.loads(str(_p)),
        )

        self.assertDictEqual(
            _p.compact,
            {
                "users": [
                    {
                        "id": standard_user.id,
                        "username": standard_user.username,
                        "first_name": standard_user.first_name,
                        "last_name": standard_user.last_name,
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "permissions": "download",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "owner",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "none"},
                    {"id": 2, "name": "registered-members", "permissions": "none", "title": "Registered Members"},
                ],
            },
            _p.compact,
        )
        # 2. "download" permissions are NOT allowed on "Maps"
        test_map = Map.objects.first()
        perm_spec = {
            "users": {
                "bobby": [
                    "view_resourcebase",
                    "download_resourcebase",
                ]
            },
            "groups": {},
        }
        _p = PermSpec(perm_spec, test_map)
        self.assertDictEqual(
            json.loads(str(_p)),
            {
                "users": {
                    "bobby": [
                        "view_resourcebase",
                        "download_resourcebase",
                    ]
                },
                "groups": {},
            },
            json.loads(str(_p)),
        )

        self.assertDictEqual(
            _p.compact,
            {
                "users": [
                    {
                        "id": standard_user.id,
                        "username": standard_user.username,
                        "first_name": standard_user.first_name,
                        "last_name": standard_user.last_name,
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "permissions": "view",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(standard_user)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "owner",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "none"},
                    {"id": 2, "name": "registered-members", "permissions": "none", "title": "Registered Members"},
                ],
            },
            _p.compact,
        )

    def test_admin_whitelisted_access_backend(self):
        from geonode.security.backends import AdminRestrictedAccessBackend
        from django.core.exceptions import PermissionDenied

        backend = AdminRestrictedAccessBackend()

        with self.settings(ADMIN_IP_WHITELIST=["88.88.88.88"]):
            with self.assertRaises(PermissionDenied):
                backend.authenticate(HttpRequest(), username="admin", password="admin")

        with self.settings(ADMIN_IP_WHITELIST=[]):
            request = HttpRequest()
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            user = backend.authenticate(request, username="admin", password="admin")
            self.assertIsNone(user)

    def test_admin_whitelisted_access_middleware(self):
        from geonode.security.middleware import AdminAllowedMiddleware

        get_response = mock.MagicMock()
        middleware = AdminAllowedMiddleware(get_response)

        admin = get_user_model().objects.filter(is_superuser=True).first()

        # Test invalid IP
        with self.settings(ADMIN_IP_WHITELIST=["88.88.88.88"]):
            request = HttpRequest()
            request.user = admin
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertEqual(request.user, AnonymousUser())

            request = HttpRequest()
            basic_auth = base64.b64encode(b"admin:admin").decode()
            request.META["HTTP_AUTHORIZATION"] = f"Basic {basic_auth}"
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertIsNone(request.META.get("HTTP_AUTHORIZATION"))

            token = create_auth_token(admin)
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
            middleware.process_request(request)
            self.assertIsNone(request.META.get("HTTP_AUTHORIZATION"))

        with self.settings(ADMIN_IP_WHITELIST=[]):
            request = HttpRequest()
            request.user = admin
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertTrue(request.user.is_superuser)

        # Test valid IP
        with self.settings(ADMIN_IP_WHITELIST=["127.0.0.1"]):
            request = HttpRequest()
            request.user = admin
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertTrue(request.user.is_superuser)

        # Test range of whitelisted IPs
        with self.settings(ADMIN_IP_WHITELIST=["127.0.0.0/24"]):
            request = HttpRequest()
            request.user = admin
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertTrue(request.user.is_superuser)

        # Test valid IP in second element
        with self.settings(ADMIN_IP_WHITELIST=["88.88.88.88", "127.0.0.1"]):
            request = HttpRequest()
            request.user = admin
            request.path = reverse("home")
            request.META["REMOTE_ADDR"] = "127.0.0.1"
            middleware.process_request(request)
            self.assertTrue(request.user.is_superuser)


class SecurityRulesTests(TestCase):
    """
    Test resources synchronization with Guardian and dirty states cleaning
    """

    def setUp(self):
        self.maxDiff = None
        self._l = create_single_dataset("test_dataset")

    def test_sync_resources_with_guardian_delay_false(self):
        with self.settings(DELAYED_SECURITY_SIGNALS=False, GEOFENCE_SECURITY_ENABLED=True):
            delete_geofence_rules_for_layer(self._l)
            # Set geofence (and so the dirty state)
            allow_layer_to_all(self._l)
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
        with self.settings(DELAYED_SECURITY_SIGNALS=True, GEOFENCE_SECURITY_ENABLED=True):
            delete_geofence_rules_for_layer(self._l)
            # Set geofence (and so the dirty state)
            allow_layer_to_all(self._l)
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
        self.owner = get_user_model().objects.get(username="admin")
        self.perms = {"*": ""}
        self.gf_services = _get_gf_services(self.layer, self.perms)

    def test_should_not_disable_cache_for_user_without_geolimits(self):
        _disable_dataset_cache = has_geolimits(self.layer, self.owner, None)
        self.assertFalse(_disable_dataset_cache)

    def test_should_disable_cache_for_user_with_geolimits(self):
        geo_limit, _ = UserGeoLimit.objects.get_or_create(user=self.owner, resource=self.layer)
        self.layer.users_geolimits.set([geo_limit])
        self.layer.refresh_from_db()
        _disable_dataset_cache = has_geolimits(self.layer, self.owner, None)
        self.assertTrue(_disable_dataset_cache)

    def test_should_not_disable_cache_for_anonymous_without_geolimits(self):
        _disable_dataset_cache = has_geolimits(self.layer, None, None)
        self.assertFalse(_disable_dataset_cache)

    def test_should_disable_cache_for_anonymous_with_geolimits(self):
        geo_limit, _ = UserGeoLimit.objects.get_or_create(user=get_anonymous_user(), resource=self.layer)
        self.layer.users_geolimits.set([geo_limit])
        self.layer.refresh_from_db()
        _disable_dataset_cache = has_geolimits(self.layer, None, None)
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
        """
        **AUTO PUBLISHING** - test_set_compact_permissions
          - `RESOURCE_PUBLISHING = False`
          - `ADMIN_MODERATE_UPLOADS = False`
        """
        use_cases = [
            (
                PermSpec({"users": {}, "groups": {}}, self.resource).compact,
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: [],
                    self.group_member: [],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                PermSpec(
                    {
                        "users": {"AnonymousUser": ["view_resourcebase"]},
                        "groups": {"second_custom_group": ["change_resourcebase"]},
                    },
                    self.resource,
                ).compact,
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: ["view_resourcebase", "publish_resourcebase", "approve_resourcebase"],
                    self.group_member: ["view_resourcebase"],
                    self.not_group_member: [
                        "change_resourcebase",
                        "view_resourcebase",
                        "download_resourcebase",
                        "change_resourcebase_metadata",
                        "approve_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
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
                self.assertSetEqual(
                    set(expected_perms),
                    set(perms_got),
                    msg=f"use case #{counter} - user: {authorized_subject.username}",
                )

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_are_set_as_expected_resource_publishing_True(self):
        """
        **SIMPLE PUBLISHING** - test_permissions_are_set_as_expected_resource_publishing_True
          - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
          - `ADMIN_MODERATE_UPLOADS = False`
        """
        use_cases = [
            (
                {"users": {}, "groups": {}},
                {
                    self.author: [
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "approve_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "change_resourcebase_permissions",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                {"users": [], "groups": {"second_custom_group": ["view_resourcebase"]}},
                {
                    self.author: [
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "approve_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "change_resourcebase_permissions",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["view_resourcebase"],
                    self.anonymous_user: [],
                },
            ),
        ]
        for counter, item in enumerate(use_cases):
            permissions, expected = item
            self.resource.set_permissions(permissions)
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(
                    set(expected_perms),
                    set(perms_got),
                    msg=f"use case #{counter} - user: {authorized_subject.username}",
                )

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_are_set_as_expected_admin_upload_resource_publishing_True(self):
        """
        **ADVANCED WORKFLOW** - test_permissions_are_set_as_expected_admin_upload_resource_publishing_True
          - `RESOURCE_PUBLISHING = True`
          - `ADMIN_MODERATE_UPLOADS = True`
        """
        use_cases = [
            (
                {"users": {}, "groups": {}},
                {
                    self.author: [
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                {"users": {}, "groups": {"second_custom_group": ["view_resourcebase"]}},
                {
                    self.author: [
                        "download_resourcebase",
                        "view_resourcebase",
                    ],
                    self.group_manager: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_member: ["download_resourcebase", "view_resourcebase"],
                    self.not_group_member: ["view_resourcebase"],
                    self.anonymous_user: [],
                },
            ),
        ]
        try:
            self.resource.is_approved = True
            self.resource.is_published = False
            self.resource.save()
            for counter, item in enumerate(use_cases):
                permissions, expected = item
                self.resource.set_permissions(permissions)
                for authorized_subject, expected_perms in expected.items():
                    perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                    self.assertSetEqual(
                        set(expected_perms),
                        set(perms_got),
                        msg=f"use case #{counter} - user: {authorized_subject.username}",
                    )
        finally:
            self.resource.is_approved = True
            self.resource.is_published = True
            self.resource.save()

    @override_settings(RESOURCE_PUBLISHING=False)
    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_permissions_are_set_as_expected_admin_upload_resource_publishing_False(self):
        """
        **AUTO PUBLISHING** - test_permissions_are_set_as_expected_admin_upload_resource_publishing_False
          - `RESOURCE_PUBLISHING = False`
          - `ADMIN_MODERATE_UPLOADS = False`
        """
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
                        "approve_resourcebase",
                        "publish_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: [],
                    self.group_member: [],
                    self.not_group_member: [],
                    self.anonymous_user: [],
                },
            ),
            (
                {
                    "users": {"AnonymousUser": ["view_resourcebase"]},
                    "groups": {"second_custom_group": ["change_resourcebase"]},
                },
                {
                    self.author: [
                        "change_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase_permissions",
                        "delete_resourcebase",
                        "download_resourcebase",
                        "publish_resourcebase",
                        "view_resourcebase",
                        "approve_resourcebase",
                        "change_dataset_style",
                        "change_dataset_data",
                    ],
                    self.group_manager: ["view_resourcebase", "approve_resourcebase", "publish_resourcebase"],
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
                self.assertSetEqual(
                    set(expected_perms),
                    set(perms_got),
                    msg=f"use case #{counter} - user: {authorized_subject.username}",
                )

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_on_user_role_promotion_to_manager(self):
        """
        **ADVANCED WORKFLOW** - test_permissions_on_user_role_promotion_to_manager
          - `RESOURCE_PUBLISHING = True`
          - `ADMIN_MODERATE_UPLOADS = True`
        """
        sut = GroupMember.objects.filter(user=self.group_member).exclude(group__title="Registered Members").first()
        expected = {
            self.author: [
                "download_resourcebase",
                "view_resourcebase",
            ],
            self.group_manager: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "publish_resourcebase",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
            self.group_member: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "publish_resourcebase",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
        }
        try:
            self.resource.is_approved = True
            self.resource.is_published = False
            self.resource.save()
            self.assertEqual(sut.role, "member")
            sut.promote()
            sut.refresh_from_db()
            self.assertEqual(sut.role, "manager")
            for authorized_subject, expected_perms in expected.items():
                perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
                self.assertSetEqual(
                    set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}"
                )
        finally:
            self.resource.is_approved = True
            self.resource.is_published = True
            self.resource.save()
            sut.demote()

    @override_settings(RESOURCE_PUBLISHING=True)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_permissions_on_user_role_demote_to_member(self):
        """
        **ADVANCED WORKFLOW** - test_permissions_on_user_role_demote_to_member
          - `RESOURCE_PUBLISHING = True`
          - `ADMIN_MODERATE_UPLOADS = True`
        """
        sut = GroupMember.objects.filter(user=self.group_manager).exclude(group__title="Registered Members").first()
        self.assertEqual(sut.role, "manager")
        sut.demote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "member")
        expected = {
            self.author: [
                "download_resourcebase",
                "view_resourcebase",
            ],
            self.group_manager: ["download_resourcebase", "view_resourcebase"],
            self.group_member: ["download_resourcebase", "view_resourcebase"],
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(
                set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}"
            )

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_on_user_role_demote_to_member_only_RESOURCE_PUBLISHING_active(self):
        """
        **SIMPLE PUBLISHING** - test_permissions_on_user_role_demote_to_member_only_RESOURCE_PUBLISHING_active
          - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
          - `ADMIN_MODERATE_UPLOADS = False`
        """
        sut = GroupMember.objects.filter(user=self.group_manager).exclude(group__title="Registered Members").first()
        self.assertEqual(sut.role, "manager")
        sut.demote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "member")
        expected = {
            self.author: [
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "change_resourcebase",
                "change_resourcebase_metadata",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
            self.group_manager: ["download_resourcebase", "view_resourcebase"],
            self.group_member: ["download_resourcebase", "view_resourcebase"],
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(
                set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}"
            )

    @override_settings(RESOURCE_PUBLISHING=True)
    def test_permissions_on_user_role_promote_to_manager_only_RESOURCE_PUBLISHING_active(self):
        """
        **SIMPLE PUBLISHING** - test_permissions_on_user_role_promote_to_manager_only_RESOURCE_PUBLISHING_active
          - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
          - `ADMIN_MODERATE_UPLOADS = False`
        """
        sut = GroupMember.objects.filter(user=self.group_member).exclude(group__title="Registered Members").first()
        self.assertEqual(sut.role, "member")
        sut.promote()
        sut.refresh_from_db()
        self.assertEqual(sut.role, "manager")
        expected = {
            self.author: [
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "change_resourcebase",
                "change_resourcebase_metadata",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
            self.group_manager: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "publish_resourcebase",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "publish_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
            self.group_member: [
                "change_resourcebase",
                "change_resourcebase_metadata",
                "delete_resourcebase",
                "download_resourcebase",
                "view_resourcebase",
                "publish_resourcebase",
                "change_resourcebase_permissions",
                "approve_resourcebase",
                "change_dataset_style",
                "change_dataset_data",
            ],
        }
        for authorized_subject, expected_perms in expected.items():
            perms_got = [x for x in self.resource.get_self_resource().get_user_perms(authorized_subject)]
            self.assertSetEqual(
                set(expected_perms), set(perms_got), msg=f"use case #0 - user: {authorized_subject.username}"
            )

    @override_settings(DEFAULT_ANONYMOUS_VIEW_PERMISSION=False)
    def test_if_anonymoys_default_perms_is_false_should_not_assign_perms_to_user_group(self):
        """
        if DEFAULT_ANONYMOUS_VIEW_PERMISSION is False, the user's group should not get any permission
        """

        resource = resource_manager.create(str(uuid.uuid4), Dataset, defaults={"owner": self.group_member})
        self.assertFalse(self.group_profile.group in resource.get_all_level_info()["groups"].keys())

    @override_settings(DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False)
    def test_if_anonymoys_default_download_perms_is_false_should_not_assign_perms_to_user_group(self):
        """
        if DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION is False, the user's group should not get any permission
        """

        resource = resource_manager.create(str(uuid.uuid4), Dataset, defaults={"owner": self.group_member})
        self.assertFalse(self.group_profile.group in resource.get_all_level_info()["groups"].keys())

    @override_settings(DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False)
    @override_settings(RESOURCE_PUBLISHING=True)
    def test_if_anonymoys_default_perms_is_false_should_assign_perms_to_user_group_if_advanced_workflow_is_on(self):
        """
        if DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION is False and the advanced workflow is activate
         the user's group should get the view and download permission
        """

        resource = resource_manager.create(str(uuid.uuid4), Dataset, defaults={"owner": self.group_member})
        self.assertTrue(self.group_profile.group in resource.get_all_level_info()["groups"].keys())
        group_val = resource.get_all_level_info()["groups"][self.group_profile.group]
        self.assertSetEqual({"view_resourcebase", "download_resourcebase"}, set(group_val))

    @override_settings(DEFAULT_ANONYMOUS_VIEW_PERMISSION=False)
    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_if_anonymoys_default_perms_is_false_should_assign_perms_to_user_group_if_advanced_workflow_is_on_moderate(
        self,
    ):
        """
        if DEFAULT_ANONYMOUS_VIEW_PERMISSION is False and the advanced workflow is activate
         the user's group should get the view and download permission
        """

        resource = resource_manager.create(str(uuid.uuid4), Dataset, defaults={"owner": self.group_member})

        self.assertTrue(self.group_profile.group in resource.get_all_level_info()["groups"].keys())
        group_val = resource.get_all_level_info()["groups"][self.group_profile.group]
        self.assertSetEqual({"view_resourcebase", "download_resourcebase"}, set(group_val))


@override_settings(RESOURCE_PUBLISHING=True)
@override_settings(ADMIN_MODERATE_UPLOADS=True)
class TestPermissionChanges(GeoNodeBaseTestSupport):
    def setUp(self):
        # Creating groups
        self.author, _ = get_user_model().objects.get_or_create(username="author")
        self.group_manager, _ = get_user_model().objects.get_or_create(username="group_manager")
        self.resource_group_manager, _ = get_user_model().objects.get_or_create(username="resource_group_manager")
        self.group_member, _ = get_user_model().objects.get_or_create(username="group_member")
        self.member_with_perms, _ = get_user_model().objects.get_or_create(username="member_with_perms")

        # Defining group profiles and members
        self.owner_group, _ = GroupProfile.objects.get_or_create(slug="owner_group")
        self.resource_group, _ = GroupProfile.objects.get_or_create(slug="resource_group")

        # defining group members
        GroupMember.objects.get_or_create(group=self.owner_group, user=self.author, role="member")
        GroupMember.objects.get_or_create(group=self.owner_group, user=self.group_member, role="member")
        GroupMember.objects.get_or_create(group=self.owner_group, user=self.group_manager, role="manager")
        GroupMember.objects.get_or_create(group=self.resource_group, user=self.resource_group_manager, role="manager")

        # Creating the default resource
        self.resource = create_single_dataset(
            name="test_layer_adv",
            owner=self.author,
            is_approved=False,
            is_published=False,
            was_approved=False,
            was_published=False,
            group=self.resource_group.group,
        )

        self.owner_perms = ["view_resourcebase", "download_resourcebase"]
        self.edit_perms = ["change_resourcebase", "change_resourcebase_metadata"]
        self.dataset_perms = ["change_dataset_style", "change_dataset_data"]
        self.adv_owner_limit = ["delete_resourcebase", "change_resourcebase_permissions", "publish_resourcebase"]
        self.safe_perms = ["download_resourcebase", "view_resourcebase"]
        self.data = {
            "resource-title": self.resource.title,
            "resource-owner": self.author.id,
            "resource-date": "2021-10-27 05:59 am",
            "resource-date_type": "publication",
            "resource-language": self.resource.language,
            "resource-is_approved": "on",
            "resource-group": self.resource_group.group.id,
            "dataset_attribute_set-TOTAL_FORMS": 0,
            "dataset_attribute_set-INITIAL_FORMS": 0,
        }
        self.url = reverse("dataset_metadata", args=(self.resource.alternate,))

        # Assign manage perms to user member_with_perms
        for perm in self.dataset_perms:
            assign_perm(perm, self.member_with_perms, self.resource)
        for perm in self.owner_perms:
            assign_perm(perm, self.member_with_perms, self.resource.get_self_resource())

        # Assert inital assignment of permissions to groups and users
        resource_perm_specs = self.resource.get_all_level_info()
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.author]), set(self.owner_perms + self.edit_perms + self.dataset_perms)
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.member_with_perms]), set(self.owner_perms + self.dataset_perms)
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.resource_group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(set(resource_perm_specs["groups"][self.owner_group.group]), set(self.safe_perms))
        self.assertSetEqual(set(resource_perm_specs["groups"][self.resource_group.group]), set(self.safe_perms))

    def test_permissions_on_approve_and_publish_changes(self):
        # Group manager approves a resource
        self.group_manager.set_password("group_manager")
        self.group_manager.save()
        self.assertTrue(self.client.login(username="group_manager", password="group_manager"))
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertions_for_approved_or_published_is_true()

        # Un approve resource
        self.data.pop("resource-is_approved")
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertions_for_approved_and_published_is_false()

        # Admin publishes and approves resource
        response = self.admin_approve_and_publish_resource()
        self.assertEqual(response.status_code, 200)
        self.assertions_for_approved_or_published_is_true()

        # Admin Un approves and un publishes resource
        response = self.admin_unapprove_and_unpublish_resource()
        self.assertEqual(response.status_code, 200)
        self.assertions_for_approved_and_published_is_false()

    def test_owner_is_group_manager(self):
        try:
            GroupMember.objects.get(group=self.owner_group, user=self.author).promote()
            # Admin publishes and approves the resource
            response = self.admin_approve_and_publish_resource()
            self.assertEqual(response.status_code, 200)
            resource_perm_specs = self.resource.get_all_level_info()

            # Once a resource has been published, the 'publish_resourcebase' permission should be removed anyway
            self.assertSetEqual(
                set(resource_perm_specs["users"][self.author]),
                set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
            )

            # Admin un-approves and un-publishes the resource
            response = self.admin_unapprove_and_unpublish_resource()
            self.assertEqual(response.status_code, 200)
            resource_perm_specs = self.resource.get_all_level_info()

            self.assertSetEqual(
                set(resource_perm_specs["users"][self.author]),
                set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
            )
        finally:
            GroupMember.objects.get(group=self.owner_group, user=self.author).demote()

    def assertions_for_approved_or_published_is_true(self):
        resource_perm_specs = self.resource.get_all_level_info()
        self.assertSetEqual(set(resource_perm_specs["users"][self.author]), set(self.owner_perms))
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.member_with_perms]), set(self.owner_perms + self.dataset_perms)
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.resource_group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(set(resource_perm_specs["groups"][self.owner_group.group]), set(self.safe_perms))
        self.assertSetEqual(set(resource_perm_specs["groups"][self.resource_group.group]), set(self.safe_perms))

    def assertions_for_approved_and_published_is_false(self):
        resource_perm_specs = self.resource.get_all_level_info()
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.author]), set(self.owner_perms + self.edit_perms + self.dataset_perms)
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.member_with_perms]), set(self.owner_perms + self.dataset_perms)
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(
            set(resource_perm_specs["users"][self.resource_group_manager]),
            set(self.owner_perms + self.edit_perms + self.dataset_perms + self.adv_owner_limit),
        )
        self.assertSetEqual(set(resource_perm_specs["groups"][self.owner_group.group]), set(self.safe_perms))
        self.assertSetEqual(set(resource_perm_specs["groups"][self.resource_group.group]), set(self.safe_perms))

    def admin_approve_and_publish_resource(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.data["resource-is_approved"] = "on"
        self.data["resource-is_published"] = "on"
        response = self.client.post(self.url, data=self.data)
        self.resource.refresh_from_db()
        return response

    def admin_unapprove_and_unpublish_resource(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.data.pop("resource-is_approved")
        self.data.pop("resource-is_published")
        response = self.client.post(self.url, data=self.data)
        self.resource.refresh_from_db()
        return response


class TestUserHasPerms(GeoNodeBaseTestSupport):
    """
    Ensure that the Permission classes behaves as expected
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dataset = create_single_dataset(name="test_permission_dataset")
        cls.document = create_single_doc(name="test_permission_doc")
        cls.map = create_single_map(name="test_permission_map")

    @classmethod
    def tearDownClass(self) -> None:
        Dataset.objects.filter(name="test_permission_dataset").delete()
        Document.objects.filter(title="test_permission_doc").delete()
        Map.objects.filter(title="test_permission_map").delete()

    def setUp(self):
        self.marty, _ = get_user_model().objects.get_or_create(username="marty", password="mcfly")

    def test_user_with_view_perms(self):
        use_cases = [
            {"resource": self.dataset, "url": "base-resources-detail"},
            {"resource": self.dataset, "url": "datasets-detail"},
            {"resource": self.document, "url": "documents-detail"},
            {"resource": self.map, "url": "maps-detail"},
        ]
        for _case in use_cases:
            # setting the view permissions
            url = reverse(_case["url"], kwargs={"pk": _case["resource"].pk})

            _case["resource"].set_permissions(
                {"users": {self.marty.username: ["base.view_resourcebase", "base.download_resourcebase"]}}
            )
            # calling the api
            self.client.force_login(self.marty)
            result = self.client.get(url)
            # checking that the user can call the url in get
            self.assertEqual(200, result.status_code, _case)

            # the user cannot patch the resource
            result = self.client.patch(url)
            # checking that the user cannot call the url in patch due the lack of permissions
            self.assertEqual(403, result.status_code, _case)

            # after update the permissions list, the user can modify the resource
            _case["resource"].set_permissions(
                {"users": {self.marty.username: ["base.view_resourcebase", "base.change_resourcebase"]}}
            )
            # the user can patch the resource
            result = self.client.patch(url)
            # checking that the user can call the url in patch since now it has the permissions
            self.assertEqual(200, result.status_code, _case)

    def test_user_with_view_listing(self):
        use_cases = [
            {"resource": self.dataset, "url": "base-resources-list"},
            {"resource": self.dataset, "url": "datasets-list"},
            {"resource": self.document, "url": "documents-list"},
            {"resource": self.map, "url": "maps-list"},
        ]
        for _case in use_cases:
            # setting the view permissions
            url = reverse(_case["url"])

            _case["resource"].set_permissions(
                {"users": {self.marty.username: ["base.view_resourcebase", "base.download_resourcebase"]}}
            )
            # calling the api
            self.client.force_login(self.marty)
            result = self.client.get(url)
            # checking that the user can call the url in get
            self.assertEqual(200, result.status_code, _case)

            # the user cannot patch the resource
            result = self.client.patch(url)
            # checking that the user cannot call the url in patch due the lack of permissions
            self.assertEqual(403, result.status_code, _case)

    def test_anonymous_user_is_stripped_off(self):
        from geonode.base.models import ResourceBase

        perms = ["base.view_resourcebase", "base.download_resourcebase"]
        resource = ResourceBase.objects.get(id=self.dataset.id)
        for perm in perms:
            assign_perm(perm, get_anonymous_user(), resource)
            assign_perm(perm, Group.objects.get(name="anonymous"), resource)

        perm_spec = resource.get_all_level_info()
        anonymous_user_perm = perm_spec["users"].get(get_anonymous_user())
        self.assertEqual(anonymous_user_perm, None, "Anynmous user wasn't removed")


class TestUserCanDo(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dataset = create_single_dataset(name="test_user_can_do")
        cls.admin = get_user_model().objects.filter(is_superuser=True).first()
        cls.non_admin = get_user_model().objects.filter(is_superuser=False).exclude(username="AnonymousUser").first()

    def test_user_can_approve(self):
        try:
            self.assertTrue(self.admin.can_approve(self.dataset))
            self.assertFalse(self.non_admin.can_approve(self.dataset))
            # if non admin is owner should be able to approve
            self.dataset.owner = self.non_admin
            self.dataset.save()
            self.assertTrue(self.non_admin.can_approve(self.dataset))
        finally:
            # setting back the owner to admin
            self.dataset.owner = self.admin
            self.dataset.save()

    def test_user_can_feature(self):
        self.assertTrue(self.admin.can_feature(self.dataset))
        self.assertFalse(self.non_admin.can_feature(self.dataset))

    def test_user_can_publish(self):
        try:
            self.assertTrue(self.admin.can_publish(self.dataset))
            self.assertFalse(self.non_admin.can_publish(self.dataset))
            # if non admin is owner should be able to publish
            self.dataset.owner = self.non_admin
            self.dataset.save()
            self.assertTrue(self.non_admin.can_publish(self.dataset))
        finally:
            # setting back the owner to admin
            self.dataset.owner = self.admin
            self.dataset.save()
