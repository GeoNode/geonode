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

import itertools
import os
import shutil
import logging

from uuid import uuid4
from unittest.mock import MagicMock, patch, PropertyMock
from collections import namedtuple

from django.urls import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.management import call_command
from django.contrib.gis.geos import Polygon
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from django.conf import settings
from django.test.utils import override_settings
from django.contrib.admin.sites import AdminSite
from geonode.geoserver.createlayer.utils import create_dataset

from geonode.layers import utils
from geonode.layers.utils import clear_dataset_download_handlers
from geonode.base import enumerations
from geonode.layers.apps import DatasetAppConfig
from geonode.layers.admin import DatasetAdmin
from geonode.decorators import on_ogc_backend
from geonode.maps.models import Map, MapLayer
from geonode.utils import DisableDjangoSignals, mkdtemp
from geonode.layers.views import _resolve_dataset
from geonode import GeoNodeException, geoserver
from geonode.people.utils import get_valid_user
from guardian.shortcuts import get_anonymous_user
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import resource_manager
from geonode.tests.utils import NotificationsTestsHelper
from geonode.layers.models import Dataset, Style, Attribute
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.base.models import TopicCategory, Link
from geonode.utils import check_ogc_backend, set_resource_default_links
from geonode.layers.metadata import convert_keyword, set_metadata, parse_metadata
from geonode.groups.models import GroupProfile

from geonode.layers.utils import (
    get_files,
    get_valid_name,
)

from geonode.base.populate_test_data import all_public, create_models, remove_models, create_single_dataset
from geonode.layers.download_handler import DatasetDownloadHandler
from geonode.security.registry import permissions_registry

logger = logging.getLogger(__name__)


class DatasetsTest(GeoNodeBaseTestSupport):
    """Tests geonode.layers app/module"""

    type = "dataset"

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

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
        self.user = "admin"
        self.passwd = "admin"
        self.anonymous_user = get_anonymous_user()
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.sld_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_sld.sld"
        self.maxDiff = None
        self.sut = create_single_dataset("single_point")
        create_dataset_data(self.sut.resourcebase_ptr_id)
        create_dataset_data(Dataset.objects.first().resourcebase_ptr_id)
        self.r = namedtuple("GSCatalogRes", ["resource"])

        site = AdminSite()
        self.admin = DatasetAdmin(Dataset, site)

        self.request_admin = RequestFactory().get("/admin")
        self.request_admin.user = get_user_model().objects.get(username="admin")

    # Admin Tests

    def test_admin_save_model(self):
        obj = Dataset.objects.first()
        self.assertEqual(len(obj.keywords.all()), 2)
        form = self.admin.get_form(self.request_admin, obj=obj, change=True)
        self.admin.save_model(self.request_admin, obj, form, True)

    def test_default_sourcetype(self):
        obj = Dataset.objects.first()
        self.assertEqual(obj.sourcetype, enumerations.SOURCE_TYPE_LOCAL)

    # Dataset Tests

    def test_dataset_name_clash(self):
        _ll_1 = Dataset.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name="states",
            store="geonode_data",
            subtype="vector",
            alternate="geonode:states",
        )
        _ll_2 = Dataset.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name="geonode:states",
            store="httpfooremoteservce",
            subtype="remote",
            alternate="geonode:states",
        )
        _ll_1.set_permissions({"users": {"bobby": ["base.view_resourcebase"]}})
        _ll_2.set_permissions({"users": {"bobby": ["base.view_resourcebase"]}})
        self.client.login(username="bobby", password="bob")
        _request = self.client.request()
        _request.user = get_user_model().objects.get(username="bobby")
        _ll = _resolve_dataset(_request, alternate="geonode:states")
        self.assertIsNotNone(_ll)
        self.assertEqual(_ll.name, _ll_1.name)

    def test_dataset_attributes(self):
        lyr = Dataset.objects.all().first()
        # There should be a total of 3 attributes
        self.assertEqual(len(lyr.attribute_set.all()), 4)
        # 2 out of 3 attributes should be visible
        custom_attributes = lyr.attribute_set.visible()
        self.assertEqual(len(custom_attributes), 3)
        # place_ name should come before description
        self.assertEqual(custom_attributes[0].attribute_label, "Place Name")
        self.assertEqual(custom_attributes[1].attribute_label, "Description")
        self.assertEqual(custom_attributes[2].attribute, "N\xfamero_De_M\xe9dicos")
        # TODO: do test against layer with actual attribute statistics
        self.assertEqual(custom_attributes[1].count, 1)
        self.assertEqual(custom_attributes[1].min, "NA")
        self.assertEqual(custom_attributes[1].max, "NA")
        self.assertEqual(custom_attributes[1].average, "NA")
        self.assertEqual(custom_attributes[1].median, "NA")
        self.assertEqual(custom_attributes[1].stddev, "NA")
        self.assertEqual(custom_attributes[1].sum, "NA")
        self.assertEqual(custom_attributes[1].unique_values, "NA")

    def test_dataset_bbox(self):
        lyr = Dataset.objects.all().first()
        dataset_bbox = lyr.bbox[0:4]
        logger.debug(dataset_bbox)

        def decimal_encode(bbox):
            _bbox = [float(o) for o in bbox]
            # Must be in the form : [x0, x1, y0, y1
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

        from geonode.utils import bbox_to_projection

        projected_bbox = decimal_encode(
            bbox_to_projection(
                [float(coord) for coord in dataset_bbox]
                + [
                    lyr.srid,
                ],
                target_srid=4326,
            )[:4]
        )
        logger.debug(projected_bbox)
        self.assertEqual(projected_bbox, [-180.0, -90.0, 180.0, 90.0])
        logger.debug(lyr.ll_bbox)
        self.assertEqual(lyr.ll_bbox, [-180.0, 180.0, -90.0, 90.0, "EPSG:4326"])
        projected_bbox = decimal_encode(
            bbox_to_projection(
                [float(coord) for coord in dataset_bbox]
                + [
                    lyr.srid,
                ],
                target_srid=3857,
            )[:4]
        )
        solution = [-20037397.023298454, -74299743.40065672, 20037397.02329845, 74299743.40061197]
        logger.debug(projected_bbox)
        for coord, check in zip(projected_bbox, solution):
            self.assertAlmostEqual(coord, check, places=3)

    def test_dataset_attributes_feature_catalogue(self):
        """Test layer feature catalogue functionality"""
        self.assertTrue(self.client.login(username="admin", password="admin"))
        # test a non-existing layer
        url = reverse("dataset_feature_catalogue", args=("bad_dataset",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Get the layer to work with
        layer = Dataset.objects.all()[3]
        url = reverse("dataset_feature_catalogue", args=(layer.alternate,))
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_dataset_attribute_config(self):
        lyr = Dataset.objects.all().first()
        attribute_config = lyr.attribute_config()
        custom_attributes = attribute_config["getFeatureInfo"]
        self.assertEqual(custom_attributes["fields"], ["place_name", "description", "N\xfamero_De_M\xe9dicos"])
        self.assertEqual(custom_attributes["propertyNames"]["description"], "Description")
        self.assertEqual(custom_attributes["propertyNames"]["place_name"], "Place Name")

        attributes = Attribute.objects.filter(dataset=lyr)
        for _att in attributes:
            self.assertEqual(_att.featureinfo_type, "type_property")

        lyr.featureinfo_custom_template = "<h1>Test HTML</h1>"
        lyr.use_featureinfo_custom_template = True
        lyr.save()
        attribute_config = lyr.attribute_config()
        self.assertTrue("ftInfoTemplate" in attribute_config)
        self.assertEqual(attribute_config["ftInfoTemplate"], "<h1>Test HTML</h1>")
        lyr.use_featureinfo_custom_template = False
        lyr.save()
        attribute_config = lyr.attribute_config()
        self.assertTrue("ftInfoTemplate" not in attribute_config)

    def test_dataset_styles(self):
        lyr = Dataset.objects.all().first()
        # There should be a total of 3 styles
        self.assertEqual(len(lyr.styles.all()), 4)
        # One of the style is the default one
        self.assertEqual(lyr.default_style, Style.objects.get(id=lyr.default_style.id))

        try:
            [str(style) for style in lyr.styles.all()]
        except UnicodeEncodeError:
            self.fail("str of the Style model throws a UnicodeEncodeError with special characters.")

    def test_dataset_links(self):
        lyr = Dataset.objects.filter(subtype="vector").first()
        self.assertEqual(lyr.subtype, "vector")

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            _def_link_types = ("data", "image", "original", "html", "OGC:WMS", "OGC:WFS", "OGC:WCS")
            Link.objects.filter(resource=lyr.resourcebase_ptr, link_type__in=_def_link_types).delete()
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            set_resource_default_links(lyr, lyr)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="image")
            self.assertIsNotNone(links)

        lyr = Dataset.objects.filter(subtype="raster").first()
        self.assertEqual(lyr.subtype, "raster")
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            _def_link_types = ("data", "image", "original", "html", "OGC:WMS", "OGC:WFS", "OGC:WCS")
            Link.objects.filter(resource=lyr.resourcebase_ptr, link_type__in=_def_link_types).delete()
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            set_resource_default_links(lyr, lyr)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="image")
            self.assertIsNotNone(links)

    def test_get_valid_user(self):
        # Verify it accepts an admin user
        adminuser = get_user_model().objects.get(is_superuser=True)
        valid_user = get_valid_user(adminuser)
        msg = f'Passed in a valid admin user "{adminuser}" but got "{valid_user}" in return'
        assert valid_user.id == adminuser.id, msg

        # Verify it returns a valid user after receiving None
        valid_user = get_valid_user(None)
        msg = f'Expected valid user after passing None, got "{valid_user}"'
        assert isinstance(valid_user, get_user_model()), msg

        newuser = get_user_model().objects.create(username="arieluser")
        valid_user = get_valid_user(newuser)
        msg = f'Passed in a valid user "{newuser}" but got "{valid_user}" in return'
        assert valid_user.id == newuser.id, msg

        valid_user = get_valid_user("arieluser")
        msg = 'Passed in a valid user by username "arieluser" but got' f' "{valid_user}" in return'
        assert valid_user.username == "arieluser", msg

        nn = get_anonymous_user()
        self.assertRaises(GeoNodeException, get_valid_user, nn)

    def test_get_files(self):
        def generate_files(*extensions):
            if extensions[0].lower() != "shp":
                return
            d = None
            expected_files = None
            try:
                d = mkdtemp()
                fnames = [f"foo.{ext}" for ext in extensions]
                expected_files = {ext.lower(): fname for ext, fname in zip(extensions, fnames)}
                for f in fnames:
                    path = os.path.join(d, f)
                    # open and immediately close to create empty file
                    open(path, "w").close()
            finally:
                return d, expected_files

        # Check that a well-formed Shapefile has its components all picked up
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("shp", "shx", "prj", "dbf")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.shp"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that a Shapefile missing required components raises an
        # exception
        d = None
        try:
            d, expected_files = generate_files("shp", "shx", "prj")
            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        d = None
        _tmpdir = None
        try:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                d, expected_files = generate_files("shp", "shx", "prj", "dbf", "sld")
                gotten_files, _tmpdir = get_files(os.path.join(d, "foo.shp"))
                gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
                self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that capitalized extensions are ok
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.SHP"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that mixed capital and lowercase extensions are ok
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("SHP", "shx", "pRJ", "DBF")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.SHP"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that including both capital and lowercase extensions raises an
        # exception
        d = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "shp", "shx", "prj", "dbf")

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(expected_files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including both capital and lowercase PRJ (this is
        # special-cased in the implementation)
        d = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "prj")

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(expected_files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including both capital and lowercase SLD (this is
        # special-cased in the implementation)
        d = None
        try:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "SLD", "sld")

                # Only run the tests if this is a case sensitive OS
                if len(os.listdir(d)) == len(expected_files):
                    self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                    self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

    def test_get_valid_name(self):
        self.assertEqual(get_valid_name("blug"), "blug")
        self.assertEqual(get_valid_name("<-->"), "_")
        self.assertEqual(get_valid_name("<ab>"), "_ab_")
        self.assertNotEqual(get_valid_name("CA"), "CA_1")
        self.assertNotEqual(get_valid_name("CA"), "CA_1")

    # NOTE: we don't care about file content for many of these tests (the
    # forms under test validate based only on file name, and leave actual
    # content inspection to GeoServer) but Django's form validation will omit
    # any files with empty bodies.
    #
    # That is, this leads to mysterious test failures:
    #     SimpleUploadedFile('foo', ' '.encode("UTF-8"))
    #
    # And this should be used instead to avoid that:
    #     SimpleUploadedFile('foo', ' '.encode("UTF-8"))

    def test_category_counts(self):
        topics = TopicCategory.objects.all()
        topics = topics.annotate(**{"dataset_count": Count("resourcebase__dataset__category")})
        location = topics.get(identifier="location")
        # there are three layers with location category
        self.assertEqual(location.dataset_count, 3)

        # change the category of one layers_count
        layer = Dataset.objects.filter(category=location)[0]
        elevation = topics.get(identifier="elevation")
        layer.category = elevation
        layer.save()

        # reload the categories since it's caching the old count
        topics = topics.annotate(**{"dataset_count": Count("resourcebase__dataset__category")})
        location = topics.get(identifier="location")
        elevation = topics.get(identifier="elevation")
        self.assertEqual(location.dataset_count, 2)
        self.assertEqual(elevation.dataset_count, 4)

        # delete a layer and check the count update
        # use the first since it's the only one which has styles
        layer = Dataset.objects.all().first()
        elevation = topics.get(identifier="elevation")
        self.assertEqual(elevation.dataset_count, 4)
        layer.delete()
        topics = topics.annotate(**{"dataset_count": Count("resourcebase__dataset__category")})
        elevation = topics.get(identifier="elevation")
        self.assertEqual(elevation.dataset_count, 3)

    def test_assign_change_dataset_data_perm(self):
        """
        Ensure set_permissions supports the change_dataset_data permission.
        """
        layer = Dataset.objects.first()
        user = get_anonymous_user()
        layer.set_permissions({"users": {user.username: ["change_dataset_data"]}})
        perms = permissions_registry.get_perms(instance=layer)
        self.assertNotIn(user, perms["users"])
        self.assertNotIn(user.username, perms["users"])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_assign_remove_permissions(self):
        # Assing
        layer = Dataset.objects.all().first()
        perm_spec = permissions_registry.get_perms(instance=layer)
        self.assertNotIn(get_user_model().objects.get(username="norman"), perm_spec["users"])

        utils.set_datasets_permissions(
            "edit", resources_names=[layer.name], users_usernames=["norman"], delete_flag=False, verbose=True
        )
        perm_spec = permissions_registry.get_perms(instance=layer)
        _c = 0
        if "users" in perm_spec:
            for _u in perm_spec["users"]:
                if _u == "norman" or _u == get_user_model().objects.get(username="norman"):
                    _c += 1
        # "norman" has both read & write permissions
        self.assertEqual(_c, 1)

        # Remove
        utils.set_datasets_permissions(
            "read", resources_names=[layer.name], users_usernames=["norman"], delete_flag=True, verbose=True
        )
        perm_spec = permissions_registry.get_perms(instance=layer)
        _c = 0
        if "users" in perm_spec:
            for _u in perm_spec["users"]:
                if _u == "norman" or _u == get_user_model().objects.get(username="norman"):
                    _c += 1
        # "norman" has no permissions
        self.assertEqual(_c, 0)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_assign_remove_permissions_for_groups(self):
        # Assing
        layer = Dataset.objects.all().first()
        perm_spec = permissions_registry.get_perms(instance=layer)
        group_profile = GroupProfile.objects.create(slug="group1", title="group1", access="public")
        self.assertNotIn(group_profile, perm_spec["groups"])

        # giving manage permissions to the group
        utils.set_datasets_permissions(
            "manage", resources_names=[layer.name], groups_names=["group1"], delete_flag=False, verbose=True
        )
        perm_spec = permissions_registry.get_perms(instance=layer)
        expected = {
            "change_dataset_data",
            "change_dataset_style",
            "change_resourcebase",
            "change_resourcebase_metadata",
            "change_resourcebase_permissions",
            "delete_resourcebase",
            "download_resourcebase",
            "publish_resourcebase",
            "view_resourcebase",
        }
        # checking the perms list
        self.assertSetEqual(expected, set(perm_spec["groups"][group_profile.group]))

        # Chaning perms to the group from manage to read
        utils.set_datasets_permissions(
            "view", resources_names=[layer.name], groups_names=["group1"], delete_flag=False, verbose=True
        )
        perm_spec = permissions_registry.get_perms(instance=layer)
        expected = {"view_resourcebase"}
        # checking the perms list
        self.assertSetEqual(expected, set(perm_spec["groups"][group_profile.group]))

        # Chaning perms to the group from manage to read
        utils.set_datasets_permissions(
            "view", resources_names=[layer.name], groups_names=["group1"], delete_flag=True, verbose=True
        )
        perm_spec = permissions_registry.get_perms(instance=layer)
        # checking the perms list
        self.assertTrue(group_profile.group not in perm_spec["groups"])

        if group_profile:
            group_profile.delete()

    def test_dataset_download_not_found_for_non_existing_dataset(self):
        self.client.login(username="admin", password="admin")
        url = reverse("dataset_download", args=["foo-dataset"])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    @override_settings(USE_GEOSERVER=False)
    def test_dataset_download_redirect_to_proxy_url(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse("dataset_download", args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/download/{dataset.id}", response.url)

    def test_dataset_download_invalid_wps_format(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse("dataset_download", args=[dataset.alternate])
        response = self.client.get(f"{url}?export_format=foo")
        self.assertEqual(500, response.status_code)
        self.assertDictEqual({"error": "The format provided is not valid for the selected resource"}, response.json())

    @patch("geonode.layers.download_handler.HttpClient.request")
    def test_dataset_download_call_the_catalog_raise_error_for_no_200(self, mocked_catalog):
        _response = MagicMock(status_code=500, content="foo-bar")
        mocked_catalog.return_value = _response, "foo-bar"
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse("dataset_download", args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(500, response.status_code)
        self.assertDictEqual({"error": "Download dataset exception: error during call with GeoServer"}, response.json())

    def test_dataset_download_call_the_catalog_raise_error_for_error_content(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
                <ows:ExceptionReport xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/ows/1.1 http://localhost:8080/geoserver/schemas/ows/1.1.0/owsAll.xsd">
                    <ows:Exception exceptionCode="InvalidParameterValue" locator="ResponseDocument">
                        <ows:ExceptionText>Foo Bar Exception</ows:ExceptionText>
                    </ows:Exception>
                </ows:ExceptionReport>
                """  # noqa
        _response = MagicMock(status_code=200, text=content, headers={"Content-Type": "text/xml"})
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        with patch("geonode.layers.download_handler.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, content
            url = reverse("dataset_download", args=[dataset.alternate])
            response = self.client.get(url)
            self.assertEqual(500, response.status_code)
            self.assertDictEqual({"error": "InvalidParameterValue: Foo Bar Exception"}, response.json())

    def test_dataset_download_call_the_catalog_works(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(status_code=200, text="", headers={"Content-Type": ""})  # noqa
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        layer = create_dataset(dataset.title, dataset.title, dataset.owner, "Point")
        with patch("geonode.layers.download_handler.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ""
            url = reverse("dataset_download", args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)

    def test_dataset_download_call_the_catalog_not_work_without_download_resurcebase_perm(self):
        dataset = Dataset.objects.first()
        dataset.set_permissions({"users": {"bobby": ["base.view_resourcebase"]}})
        self.client.login(username="bobby", password="bob")
        url = reverse("dataset_download", args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_dataset_download_call_the_catalog_work_anonymous(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(status_code=200, text="", headers={"Content-Type": ""})  # noqa
        dataset = Dataset.objects.first()
        layer = create_dataset(dataset.title, dataset.title, dataset.owner, "Point")
        with patch("geonode.layers.download_handler.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ""
            url = reverse("dataset_download", args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)

    @override_settings(USE_GEOSERVER=True)
    @patch("geonode.layers.download_handler.get_template")
    def test_dataset_download_call_the_catalog_work_for_raster(self, pathed_template):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(status_code=200, text="", headers={"Content-Type": ""})  # noqa
        dataset = Dataset.objects.filter(subtype="raster").first()
        layer = create_dataset(dataset.title, dataset.title, dataset.owner, "Point")
        Dataset.objects.filter(alternate=layer.alternate).update(subtype="raster")
        with patch("geonode.layers.download_handler.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ""
            url = reverse("dataset_download", args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)
        """
        Evaluate that the context used by the template contains the right mimetype for the resource
        """
        self.assertTupleEqual(
            ({"alternate": layer.alternate, "download_format": "image/tiff"},), pathed_template.mock_calls[1].args
        )

    @override_settings(USE_GEOSERVER=True)
    @patch("geonode.layers.download_handler.get_template")
    def test_dataset_download_call_the_catalog_work_for_vector(self, pathed_template):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(status_code=200, text="", headers={"Content-Type": ""})  # noqa
        dataset = Dataset.objects.filter(subtype="vector").first()
        layer = create_dataset(dataset.title, dataset.title, dataset.owner, "Point")
        with patch("geonode.layers.download_handler.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ""
            url = reverse("dataset_download", args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)
        """
        Evaluate that the context used by the template contains the right mimetype for the resource
        """
        self.assertTupleEqual(
            ({"alternate": layer.alternate, "download_format": "application/zip"},), pathed_template.mock_calls[1].args
        )

    @patch.object(Dataset, "get_choices", new_callable=PropertyMock)
    def test_supports_time_with_vector_time_subtype(self, mock_get_choices):

        # set valid attributes
        mock_get_choices.return_value = [(4, "timestamp"), (5, "begin"), (6, "end")]

        mock_dataset = Dataset(subtype="vector")
        self.assertTrue(mock_dataset.supports_time)

    @patch.object(Dataset, "get_choices", new_callable=PropertyMock)
    def test_supports_time_with_non_vector_subtype(self, mock_get_choices):

        # set valid attributes
        mock_get_choices.return_value = [(4, "timestamp"), (5, "begin"), (6, "end")]

        mock_dataset = Dataset(subtype="raster")
        self.assertFalse(mock_dataset.supports_time)

    @patch.object(Dataset, "get_choices", new_callable=PropertyMock)
    def test_supports_time_with_vector_subtype_and_invalid_attributes(self, mock_get_choices):

        # Get an empty list from get_choices method due to invalid attributes
        mock_get_choices.return_value = []

        mock_dataset = Dataset(subtype="vector")
        self.assertFalse(mock_dataset.supports_time)

    @patch.object(Dataset, "get_choices", new_callable=PropertyMock)
    def test_supports_time_with_raster_subtype_and_invalid_attributes(self, mock_get_choices):

        # Get an empty list from get_choices method due to invalid attributes
        mock_get_choices.return_value = []

        mock_dataset = Dataset(subtype="raster")
        self.assertFalse(mock_dataset.supports_time)


class TestLayerDetailMapViewRights(GeoNodeBaseTestSupport):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()
        create_single_dataset("single_point")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create(username="dybala", email="dybala@gmail.com")
        self.user.set_password("very-secret")
        self.admin = get_user_model().objects.get(username="admin")
        self.map = Map.objects.create(uuid=str(uuid4()), owner=self.admin, title="test", is_approved=True)
        self.not_admin = get_user_model().objects.create(username="r-lukaku", is_active=True)
        self.not_admin.set_password("very-secret")
        self.not_admin.save()

        self.layer = Dataset.objects.all().first()
        create_dataset_data(self.layer.resourcebase_ptr_id)
        with DisableDjangoSignals():
            self.map_dataset = MapLayer.objects.create(
                name=self.layer.alternate,
                map=self.map,
            )

    def test_that_only_users_with_permissions_can_view_maps_in_dataset_view(self):
        """
        Test only users with view permissions to a map can view them in layer detail view
        """
        resource_manager.remove_permissions(self.map.uuid, instance=self.map.get_self_resource())
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse("dataset_embed", args=(self.layer.alternate,)))
        self.assertEqual(response.context["resource"].alternate, self.map_dataset.name)

    def test_update_with_a_comma_in_title_is_replaced_by_undescore(self):
        """
        Test that when changing the dataset title, if the entered title has a comma it is replaced by an undescore.
        """
        self.test_dataset = None
        try:
            self.test_dataset = resource_manager.create(
                None, resource_type=Dataset, defaults=dict(owner=self.not_admin, title="test", is_approved=True)
            )
            from geonode.metadata.manager import metadata_manager

            payload = metadata_manager.build_schema_instance(self.test_dataset)
            payload["title"] = "test,comma,2021"

            self.client.login(username=self.not_admin.username, password="very-secret")

            url = reverse("metadata-schema_instance", args=(self.test_dataset.id,))
            response = self.client.put(url, data=payload, content_type="application/json")

            self.test_dataset.refresh_from_db()
            self.assertEqual(self.test_dataset.title, "test_comma_2021")
            self.assertEqual(response.status_code, 200)
        finally:
            if self.test_dataset:
                self.test_dataset.delete()


class LayerNotificationsTestCase(NotificationsTestsHelper):
    type = "dataset"

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
        self.user = "admin"
        self.passwd = "admin"
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = "test@email.com"
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(DatasetAppConfig.NOTIFICATIONS, self.u)
        self.norman = get_user_model().objects.get(username="norman")
        self.norman.email = "norman@email.com"
        self.norman.is_active = True
        self.norman.save()
        self.setup_notifications_for(DatasetAppConfig.NOTIFICATIONS, self.norman)

    def testLayerNotifications(self):
        with self.settings(
            EMAIL_ENABLE=True,
            NOTIFICATION_ENABLED=True,
            NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
            PINAX_NOTIFICATIONS_QUEUE_ALL=False,
        ):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)

            _l = resource_manager.create(
                None,
                resource_type=Dataset,
                defaults=dict(
                    name="test notifications",
                    title="test notifications",
                    bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
                    srid="EPSG:4326",
                    owner=self.norman,
                ),
            )

            self.assertTrue(self.check_notification_out("dataset_created", self.u))
            # Ensure "resource.owner" won't be notified for having uploaded its own resource
            self.assertFalse(self.check_notification_out("dataset_created", self.norman))

            self.clear_notifications_queue()
            _l.name = "test notifications 2"
            _l.save(notify=True)
            self.assertTrue(self.check_notification_out("dataset_updated", self.u))

            self.clear_notifications_queue()


"""
Smoke test to explain how the uuidhandler will override the uuid for the layers
Documentation of the handler is available here:
https://github.com/GeoNode/documentation/blob/703cc6ba92b7b7a83637a874fb449420a9f8b78a/basic/settings/index.rst#uuid-handler
"""


class DummyUUIDHandler:
    def __init__(self, instance):
        self.instance = instance

    def create_uuid(self):
        return f"abc:{self.instance.uuid}"


class TestCustomUUidHandler(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username="test", email="test@test.com")
        self.sut = Dataset.objects.create(
            name="testLayer", owner=self.user, title="test", is_approved=True, uuid="abc-1234-abc"
        )

    def test_dataset_will_maintain_his_uud_if_no_handler_is_definded(self):
        expected = "abc-1234-abc"
        self.assertEqual(expected, self.sut.uuid)

    @override_settings(LAYER_UUID_HANDLER="geonode.layers.tests.DummyUUIDHandler")
    def test_dataset_will_override_the_uuid_if_handler_is_defined(self):
        resource_manager.update(None, instance=self.sut, keywords=["updating", "values"])
        expected = "abc:abc-1234-abc"
        actual = Dataset.objects.get(id=self.sut.id)
        self.assertEqual(expected, actual.uuid)

        self.assertIsNotNone(self.sut.ows_url)
        self.assertIsNotNone(self.sut.ptype)
        self.assertIsNotNone(self.sut.sourcetype)


class TestSetMetadata(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.invalid_xml = "xml"
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.custom = [
            {
                "keywords": ["features", "test_dataset"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            },
            {
                "keywords": ["no conditions to access and use"],
                "thesaurus": {
                    "date": "2020-10-30T16:58:34",
                    "datetype": "publication",
                    "title": "Test for ordering",
                },
                "type": None,
            },
            {
                "keywords": ["ad", "af"],
                "thesaurus": {
                    "date": "2008-06-01",
                    "datetype": "publication",
                    "title": "GEMET - INSPIRE themes, version 1.0",
                },
                "type": None,
            },
            {"keywords": ["Global"], "thesaurus": {"date": None, "datetype": None, "title": None}, "type": "place"},
        ]

    def test_set_metadata_will_rase_an_exception_if_is_not_valid_xml(self):
        with self.assertRaises(GeoNodeException):
            set_metadata(self.invalid_xml)

    def test_set_metadata_return_expected_values_from_xml(self):
        import datetime

        identifier, vals, regions, keywords, _ = set_metadata(open(self.exml_path).read())
        expected_vals = {
            "abstract": "real abstract",
            "constraints_other": "Not Specified: The original author did not specify a license.",
            "data_quality_statement": "Created with GeoNode",
            "date": datetime.datetime(2021, 4, 9, 9, 0, 46),
            "language": "eng",
            "purpose": None,
            "spatial_representation_type": "vector",
            "supplemental_information": "No information provided",
            "temporal_extent_end": None,
            "temporal_extent_start": None,
            "title": "test_dataset",
        }
        expected_keywords = []
        for kw in [kw.get("keywords") for kw in self.custom if kw["type"] != "place"]:
            for _kw in [_kw for _kw in kw]:
                expected_keywords.append(_kw)
        self.assertEqual("7cfbc42c-efa7-431c-8daa-1399dff4cd19", identifier)
        self.assertListEqual(["Global"], regions)
        self.assertDictEqual(expected_vals, vals)
        self.assertListEqual(expected_keywords, keywords)

    def test_convert_keyword_should_empty_list_for_empty_keyword(self):
        actual = convert_keyword([])
        self.assertListEqual([], actual)

    def test_convert_keyword_should_empty_list_for_non_empty_keyword(self):
        expected = [
            {
                "keywords": ["abc"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            }
        ]
        actual = convert_keyword(["abc"])
        self.assertListEqual(expected, actual)


"""
Smoke test to explain how the new function for multiple parsers will work
Is required to define a fuction that takes 1 parameters (the metadata xml) and return 4 parameters.
            Parameters:
                    xml (str): TextIOWrapper read example: open(self.exml_path).read())

            Returns:
                    Tuple (tuple):
                        - (identifier, vals, regions, keywords)

                    identifier(str): default empy,
                    vals(dict): default empty,
                    regions(list): default empty,
                    keywords(list(dict)): default empty
"""


class TestCustomMetadataParser(TestCase):
    def setUp(self):
        import datetime

        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.expected_vals = {
            "abstract": "real abstract",
            "constraints_other": "Not Specified: The original author did not specify a license.",
            "data_quality_statement": "Created with GeoNode",
            "date": datetime.datetime(2021, 4, 9, 9, 0, 46),
            "language": "eng",
            "purpose": None,
            "spatial_representation_type": "vector",
            "supplemental_information": "No information provided",
            "temporal_extent_end": None,
            "temporal_extent_start": None,
            "title": "test_dataset",
        }

        self.keywords = [
            {
                "keywords": ["features", "test_dataset"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            },
            {
                "keywords": ["no conditions to access and use"],
                "thesaurus": {
                    "date": "2020-10-30T16:58:34",
                    "datetype": "publication",
                    "title": "Test for ordering",
                },
                "type": None,
            },
            {
                "keywords": ["ad", "af"],
                "thesaurus": {
                    "date": "2008-06-01",
                    "datetype": "publication",
                    "title": "GEMET - INSPIRE themes, version 1.0",
                },
                "type": None,
            },
            {"keywords": ["Global"], "thesaurus": {"date": None, "datetype": None, "title": None}, "type": "place"},
        ]

    def test_will_use_only_the_default_metadata_parser(self):
        identifier, vals, regions, keywords, _ = parse_metadata(open(self.exml_path).read())
        expected_keywords = []
        for kw in [kw.get("keywords") for kw in self.keywords if kw["type"] != "place"]:
            for _kw in [_kw for _kw in kw]:
                expected_keywords.append(_kw)
        self.assertEqual("7cfbc42c-efa7-431c-8daa-1399dff4cd19", identifier)
        self.assertListEqual(["Global"], regions)
        self.assertListEqual(expected_keywords, keywords)
        self.assertDictEqual(self.expected_vals, vals)

    @override_settings(METADATA_PARSERS=["__DEFAULT__", "geonode.layers.tests.dummy_metadata_parser"])
    def test_will_use_both_parsers_defined(self):
        identifier, vals, regions, keywords, _ = parse_metadata(open(self.exml_path).read())
        self.assertEqual("7cfbc42c-efa7-431c-8daa-1399dff4cd19", identifier)
        self.assertListEqual(["Global", "Europe"], regions)
        self.assertEqual("Passed through new parser", keywords)
        self.assertDictEqual(self.expected_vals, vals)

    def test_convert_keyword_should_empty_list_for_empty_keyword(self):
        actual = convert_keyword([])
        self.assertListEqual([], actual)

    def test_convert_keyword_should_non_empty_list_for_empty_keyword(self):
        expected = [
            {
                "keywords": ["abc"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            }
        ]
        actual = convert_keyword(["abc"])
        self.assertListEqual(expected, actual)


"""
Just a dummy function required for the smoke test above
"""


def dummy_metadata_parser(exml, uuid, vals, regions, keywords, custom):
    keywords = "Passed through new parser"
    regions.append("Europe")
    return uuid, vals, regions, keywords, custom


class SetLayersPermissionsCommand(GeoNodeBaseTestSupport):
    """
    Unittest to ensure that the management command "set_layers_permissions"
    behaves as expected
    """

    def test_user_get_the_download_permissions_for_the_selected_dataset(self):
        """
        Given a user, the compact perms and the resource id, it shoul set the
        permissions for the selected resource
        """
        try:
            expected_perms = {"view_resourcebase", "download_resourcebase"}

            dataset, args, username, opts = self._create_arguments(perms_type="download")
            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username)
        finally:
            if dataset:
                dataset.delete()

    def test_user_get_the_view_permissions_for_the_selected_dataset(self):
        """
        Given a user, the compact perms and the resource id, it shoul set the
        permissions for the selected resource
        """
        try:
            expected_perms = {"view_resourcebase"}
            dataset, args, username, opts = self._create_arguments(perms_type="view")

            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username)

        finally:
            if dataset:
                dataset.delete()

    def test_user_get_the_edit_permissions_for_the_selected_dataset(self):
        """
        Given a user, the compact perms and the resource id, it shoul set the
        permissions for the selected resource
        """
        try:
            expected_perms = {
                "view_resourcebase",
                "change_dataset_style",
                "download_resourcebase",
                "change_resourcebase_metadata",
                "change_dataset_data",
                "change_resourcebase",
            }

            dataset, args, username, opts = self._create_arguments(perms_type="edit")

            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username)
        finally:
            if dataset:
                dataset.delete()

    def test_user_get_the_manage_permissions_for_the_selected_dataset(self):
        """
        Given a user, the compact perms and the resource id, it shoul set the
        permissions for the selected resource
        """
        try:
            expected_perms = {
                "delete_resourcebase",
                "change_resourcebase",
                "view_resourcebase",
                "change_resourcebase_permissions",
                "change_dataset_style",
                "change_resourcebase_metadata",
                "publish_resourcebase",
                "change_dataset_data",
                "download_resourcebase",
            }

            dataset, args, username, opts = self._create_arguments(perms_type="manage")

            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username)
        finally:
            if dataset:
                dataset.delete()

    def test_anonymous_user_cannot_get_edit_permissions(self):
        """
        Given the Anonymous user, we should get an error trying to set "edit" permissions.
        """
        try:
            expected_perms = {}

            dataset, args, username, opts = self._create_arguments(perms_type="edit")
            username = "AnonymousUser"
            opts["users"] = ["AnonymousUser"]

            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username, assertion=False)
        finally:
            if dataset:
                dataset.delete()

    def test_unset_anonymous_view_permissions(self):
        """
        Given the Anonymous user, we should be able to unset any paermission.
        """
        try:
            expected_perms = {}

            dataset, args, username, opts = self._create_arguments(perms_type="view", mode="unset")
            username = "AnonymousUser"
            opts["users"] = ["AnonymousUser"]

            call_command("set_layers_permissions", *args, **opts)

            self._assert_perms(expected_perms, dataset, username, assertion=False)
        finally:
            if dataset:
                dataset.delete()

    def _create_arguments(self, perms_type, mode="set"):
        dataset = create_single_dataset("dataset_for_management_command")
        args = []
        username = get_user_model().objects.exclude(username="admin").exclude(username="AnonymousUser").first().username
        opts = {
            "permission": perms_type,
            "users": [username],
            "resources": str(dataset.id),
            "delete": True if mode == "unset" else False,
        }

        return dataset, args, username, opts

    def _assert_perms(self, expected_perms, dataset, username, assertion=True):
        dataset.refresh_from_db()

        perms = permissions_registry.get_perms(instance=dataset)
        if assertion:
            self.assertTrue(username in [user.username for user in perms["users"]])
            actual = set(
                itertools.chain.from_iterable(
                    [perms for user, perms in perms["users"].items() if user.username == username]
                )
            )
            self.assertSetEqual(expected_perms, actual)
        else:
            self.assertFalse(username in [user.username for user in perms["users"]])


class TestDatasetDownloadHandler(GeoNodeBaseTestSupport):
    def setUp(self):
        user = get_user_model().objects.first()
        request = RequestFactory().get("http://test_url.com")
        request.user = user
        self.dataset = create_single_dataset("test_dataset_for_download")
        self.sut = DatasetDownloadHandler(request, self.dataset.alternate)

    def test_download_url_without_original_link(self):
        expected_url = reverse("dataset_download", args=[self.dataset.alternate])
        self.assertEqual(expected_url, self.sut.download_url)

    def test_download_url_with_original_link(self):
        Link.objects.update_or_create(
            resource=self.dataset.resourcebase_ptr,
            url="https://custom_dowonload_url.com",
            defaults=dict(
                extension="zip",
                name="Original Dataset",
                mime="application/octet-stream",
                link_type="original",
            ),
        )
        expected_url = "https://custom_dowonload_url.com"
        self.assertEqual(expected_url, self.sut.download_url)

    def test_get_resource_exists(self):
        self.assertIsNotNone(self.sut.get_resource())

    def test_process_dowload(self):
        response = self.sut.get_download_response()
        self.assertIsNotNone(response)


class DummyDownloadHandler(DatasetDownloadHandler):
    def get_download_response(self):
        return HttpResponse(content=b"abcsfd2")


class TestCustomDownloadHandler(GeoNodeBaseTestSupport):
    @override_settings(DEFAULT_DATASET_DOWNLOAD_HANDLER="geonode.layers.tests.DummyDownloadHandler")
    def test_download_custom_handler(self):
        clear_dataset_download_handlers()
        dataset = create_single_dataset("test_custom_download_dataset")
        url = reverse("dataset_download", args=[dataset.alternate])
        self.client.login(username="admin", password="admin")
        response = self.client.get(url)
        self.assertTrue(response.status_code == 200)
        self.assertEqual(response.content, b"abcsfd2")
