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

from unittest import TestCase as StandardTestCase

from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.test import TestCase
import mock
from owslib.map.wms111 import ContentMetadata

from . import enumerations
from .serviceprocessors import base
from .serviceprocessors import handler
from .serviceprocessors import wms
from .serviceprocessors.wms import WebMapService
from owslib.wms import WebMapService as OwsWebMapService


class ModuleFunctionsTestCase(StandardTestCase):

    @mock.patch("geonode.services.serviceprocessors.base.Catalog",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.settings",
                autospec=True)
    def test_get_cascading_workspace_returns_existing(self, mock_settings,
                                                      mock_catalog):
        mock_settings.OGC_SERVER = {
            "default": {
                "LOCATION": "nowhere/",
                "USER": "nouser",
                "PASSWORD": "nopass",
            }
        }
        mock_settings.CASCADE_WORKSPACE = "something"
        phony_workspace = "fake"
        cat = mock_catalog.return_value
        cat.get_workspace.return_value = phony_workspace
        result = base.get_geoserver_cascading_workspace(
            create=False)
        self.assertEqual(result, phony_workspace)
        mock_catalog.assert_called_with(
            service_url=mock_settings.OGC_SERVER[
                "default"]["LOCATION"] + "rest",
            username=mock_settings.OGC_SERVER["default"]["USER"],
            password=mock_settings.OGC_SERVER["default"]["PASSWORD"]
        )
        cat.get_workspace.assert_called_with(mock_settings.CASCADE_WORKSPACE)

    @mock.patch("geonode.services.serviceprocessors.base.Catalog",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.settings",
                autospec=True)
    def test_get_cascading_workspace_creates_new_workspace(self, mock_settings,
                                                           mock_catalog):
        mock_settings.OGC_SERVER = {
            "default": {
                "LOCATION": "nowhere/",
                "USER": "nouser",
                "PASSWORD": "nopass",
            }
        }
        mock_settings.CASCADE_WORKSPACE = "something"
        phony_workspace = "fake"
        cat = mock_catalog.return_value
        cat.get_workspace.return_value = None
        cat.create_workspace.return_value = phony_workspace
        result = base.get_geoserver_cascading_workspace(
            create=True)
        self.assertEqual(result, phony_workspace)
        mock_catalog.assert_called_with(
            service_url=mock_settings.OGC_SERVER[
                "default"]["LOCATION"] + "rest",
            username=mock_settings.OGC_SERVER["default"]["USER"],
            password=mock_settings.OGC_SERVER["default"]["PASSWORD"]
        )
        cat.get_workspace.assert_called_with(mock_settings.CASCADE_WORKSPACE)
        cat.create_workspace.assert_called_with(
            mock_settings.CASCADE_WORKSPACE,
            "http://www.geonode.org/{}".format(mock_settings.CASCADE_WORKSPACE)
        )

    @mock.patch("geonode.services.serviceprocessors.handler.WmsServiceHandler",
                autospec=True)
    def test_get_service_handler_wms(self, mock_wms_handler):
        phony_url = "http://fake"
        handler.get_service_handler(phony_url, service_type=enumerations.WMS)
        mock_wms_handler.assert_called_with(phony_url)


class WmsServiceHandlerTestCase(TestCase):

    def setUp(self):
        self.phony_url = ("http://a-really-long-and-fake-name-here-so-that-"
                          "we-use-it-in-tests")
        self.phony_title = "a generic title"
        self.phony_version = "some.version"
        self.phony_layer_name = "phony_name"
        self.phony_keywords = ["first", "second"]
        mock_parsed_wms = mock.MagicMock(OwsWebMapService).return_value
        (url, mock_parsed_wms) = mock.MagicMock(WebMapService,
                                                return_value=(self.phony_url,
                                                              mock_parsed_wms)).return_value
        mock_parsed_wms.url = self.phony_url
        mock_parsed_wms.identification.title = self.phony_title
        mock_parsed_wms.identification.version = self.phony_version
        mock_parsed_wms.identification.keywords = self.phony_keywords
        mock_layer_meta = mock.MagicMock(ContentMetadata)
        mock_layer_meta.name = self.phony_layer_name
        mock_layer_meta.children = []
        mock_layer_meta.crsOptions = ["EPSG:3857"]
        mock_parsed_wms.contents = {
            mock_layer_meta.name: mock_layer_meta,
        }
        self.parsed_wms = mock_parsed_wms
        self.test_user = get_user_model().objects.create_user(
            "serviceowner", "usermail@fake.mail", "somepassword")

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_has_correct_url(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.url, self.phony_url)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_has_valid_name_when_no_title_exists(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms.return_value[1].identification.title = ""
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(
            handler.name, self.phony_url.replace("http://", "")[:40])

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_has_valid_name_when_title_exists(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertNotEqual(handler.name, slugify(self.phony_title))

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_has_correct_service_type(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.service_type, enumerations.WMS)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings",
                autospec=True)
    def test_detects_indexed_service(self, mock_settings, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.indexing_method, enumerations.INDEXED)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings",
                autospec=True)
    def test_detects_cascaded_service(self, mock_settings, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_layer_meta = mock.MagicMock(ContentMetadata)
        mock_layer_meta.name = "phony_name"
        mock_layer_meta.children = []
        mock_layer_meta.crsOptions = ["epsg:4326"]
        self.parsed_wms.contents = {
            mock_layer_meta.name: mock_layer_meta,
        }
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.indexing_method, enumerations.CASCADED)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_create_geonode_service(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.create_geonode_service(self.test_user)
        self.assertEqual(result.base_url, self.phony_url)
        self.assertEqual(result.type, handler.service_type)
        self.assertEqual(result.method, handler.indexing_method)
        self.assertEqual(result.owner, self.test_user)
        self.assertEqual(result.version, self.phony_version)
        self.assertEqual(result.name, handler.name)
        self.assertEqual(result.title, self.phony_title)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_get_keywords(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.get_keywords()
        self.assertEqual(result, self.phony_keywords)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_get_resource(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.get_resource(self.phony_layer_name)
        self.assertEqual(result.name, self.phony_layer_name)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_get_resources(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        result = list(handler.get_resources())
        self.assertEqual(result[0].name, self.phony_layer_name)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings",
                autospec=True)
    def test_offers_geonode_projection(self, mock_settings, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler._offers_geonode_projection()
        self.assertTrue(result)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings",
                autospec=True)
    def test_does_not_offer_geonode_projection(self, mock_settings, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        self.parsed_wms.contents[self.phony_layer_name].crsOptions = [
            "EPSG:4326"]
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler._offers_geonode_projection()
        self.assertFalse(result)

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.get_geoserver_"
                "cascading_workspace", autospec=True)
    def test_get_store(self, mock_get_gs_cascading_store, mock_wms):
        mock_workspace = mock_get_gs_cascading_store.return_value
        mock_catalog = mock_workspace.catalog
        mock_catalog.get_store.return_value = None
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        handler._get_store(create=True)
        mock_catalog.create_wmsstore.assert_called_with(
            name=handler.name,
            workspace=mock_workspace,
            user=mock_catalog.username,
            password=mock_catalog.password
        )
