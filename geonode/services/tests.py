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

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from selenium import webdriver
from unittest import TestCase as StandardTestCase

from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
import mock
from owslib.map.wms111 import ContentMetadata

from geonode.services.utils import test_resource_table_status
from geonode.tests.base import GeoNodeBaseTestSupport
from . import enumerations, forms
from .models import Service
from .serviceprocessors import (base,
                                handler,
                                wms,
                                arcgis)
from .serviceprocessors.arcgis import MapLayer
from .serviceprocessors.wms import WebMapService

from arcrest import MapService as ArcMapService
from owslib.wms import WebMapService as OwsWebMapService
from collections import namedtuple


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

    @mock.patch("arcrest.MapService",
                autospec=True)
    def test_get_service_handler_arcgis(self, mock_map_service):
        mock_arcgis_service_contents = {
            "currentVersion": 10.51,
            "serviceDescription": "Droits petroliers et gaziers / Oil and Gas Rights",
            "mapName": "Droits_petroliers_et_gaziers_Oil_and_Gas_Rights",
            "description": "",
            "copyrightText": "",
            "supportsDynamicLayers": False,
            "layers": [
                {
                    "id": 0,
                    "name": "Droits pétroliers et gaziers / Oil and Gas Rights",
                    "parentLayerId": -1,
                    "defaultVisibility": True,
                    "subLayerIds": None,
                    "minScale": 0,
                    "maxScale": 0
                }
            ],
            "tables": [],
            "spatialReference": {
                "wkid": 4140,
                "latestWkid": 4617
            },
            "singleFusedMapCache": False,
            "initialExtent": {
                "xmin": -144.97375000000002,
                "ymin": 58.90551066699999,
                "xmax": -57.55125000000002,
                "ymax": 91.84630866699999,
                "spatialReference": {
                    "wkid": 4140,
                    "latestWkid": 4617
                }
            },
            "fullExtent": {
                "xmin": -144.97375,
                "ymin": 34.637024667000006,
                "xmax": -57.55125,
                "ymax": 91.84630866699999,
                "spatialReference": {
                    "wkid": 4140,
                    "latestWkid": 4617
                }
            },
            "minScale": 0,
            "maxScale": 0,
            "units": "esriDecimalDegrees",
            "supportedImageFormatTypes": "PNG32,PNG24,PNG,JPG,DIB,TIFF,EMF,PS,PDF,GIF,SVG,SVGZ,BMP",
            "documentInfo": {
                "Title": "Droits petroliers et gaziers / Oil and Gas Rights",
                "Author": "",
                "Comments": "Droits petroliers et gaziers / Oil and Gas Rights",
                "Subject": "Droits petroliers et gaziers / Oil and Gas Rights",
                "Category": "",
                "AntialiasingMode": "None",
                "TextAntialiasingMode": "Force",
                "Keywords": "Droits petroliers et gaziers,Oil and Gas Rights"
            },
            "capabilities": "Map,Query,Data",
            "supportedQueryFormats": "JSON, AMF, geoJSON",
            "exportTilesAllowed": False,
            "supportsDatumTransformation": True,
            "maxRecordCount": 1000,
            "maxImageHeight": 2048,
            "maxImageWidth": 2048,
            "supportedExtensions": "FeatureServer, KmlServer, WFSServer, WMSServer"
        }

        mock_arcgis_service_json_struct = {
            "supportsDynamicLayers": False,
            "initialExtent": {
                "xmin": -144.97375000000002,
                "ymin": 58.90551066699999,
                "ymax": 91.84630866699999,
                "xmax": -57.55125000000002,
                "spatialReference": {
                    "wkid": 4140,
                    "latestWkid": 4617
                }
            },
            "documentInfo": {
                "Category": "",
                "Author": "",
                "TextAntialiasingMode": "Force",
                "Title": "Droits petroliers et gaziers / Oil and Gas Rights",
                "Comments": "Droits petroliers et gaziers / Oil and Gas Rights",
                "AntialiasingMode": "None",
                "Keywords": "Droits petroliers et gaziers,Oil and Gas Rights",
                "Subject": "Droits petroliers et gaziers / Oil and Gas Rights"
            },
            "spatialReference": {
                "wkid": 4140,
                "latestWkid": 4617
            },
            "description": "",
            "layers": [
                {
                    "name": "Droits pétroliers et gaziers / Oil and Gas Rights",
                    "maxScale": 0,
                    "defaultVisibility": True,
                    "parentLayerId": -1,
                    "id": 0,
                    "minScale": 0,
                    "subLayerIds": None
                }
            ],
            "tables": [],
            "supportedImageFormatTypes": "PNG32,PNG24,PNG,JPG,DIB,TIFF,EMF,PS,PDF,GIF,SVG,SVGZ,BMP",
            "capabilities": "Map,Query,Data",
            "mapName": "Droits_petroliers_et_gaziers_Oil_and_Gas_Rights",
            "currentVersion": 10.51,
            "units": "esriDecimalDegrees",
            "supportedQueryFormats": "JSON, AMF, geoJSON",
            "maxRecordCount": 1000,
            "exportTilesAllowed": False,
            "maxImageHeight": 2048,
            "supportedExtensions": "FeatureServer, KmlServer, WFSServer, WMSServer",
            "fullExtent": {
                "xmin": -144.97375,
                "ymin": 34.637024667000006,
                "ymax": 91.84630866699999,
                "xmax": -57.55125,
                "spatialReference": {
                    "wkid": 4140,
                    "latestWkid": 4617
                }
            },
            "singleFusedMapCache": False,
            "supportsDatumTransformation": True,
            "maxImageWidth": 2048,
            "maxScale": 0,
            "copyrightText": "",
            "minScale": 0,
            "serviceDescription": "Droits petroliers et gaziers / Oil and Gas Rights"
        }

        phony_url = "http://fake"
        mock_parsed_arcgis = mock.MagicMock(ArcMapService).return_value
        (url, mock_parsed_arcgis) = mock.MagicMock(ArcMapService,
                                                   return_value=(phony_url,
                                                                 mock_parsed_arcgis)).return_value
        mock_parsed_arcgis.url = phony_url
        mock_parsed_arcgis._contents = mock_arcgis_service_contents
        mock_parsed_arcgis._json_struct = mock_arcgis_service_json_struct

        mock_map_service.return_value = (phony_url, mock_parsed_arcgis)

        handler = arcgis.ArcImageServiceHandler(phony_url)
        self.assertEquals(handler.url, phony_url)

        LayerESRIExtent = namedtuple('LayerESRIExtent', 'spatialReference xmin ymin ymax xmax')
        LayerESRIExtentSpatialReference = namedtuple('LayerESRIExtentSpatialReference', 'wkid latestWkid')

        layer_meta = MapLayer(
            id=0,
            title=u'Droits pétroliers et gaziers / Oil and Gas Rights',
            abstract=u'Droits pétroliers et gaziers / Oil and Gas Rights',
            type=u'Feature Layer',
            geometryType=u'esriGeometryPolygon',
            copyrightText=u'',
            extent=LayerESRIExtent(
                LayerESRIExtentSpatialReference(4140, 4617),
                -144.97375,
                34.637024667000006,
                91.84630866699999,
                -57.55125),
            fields=[
                {
                    u'alias': u'OBJECTID',
                    u'domain': None,
                    u'type': u'esriFieldTypeOID',
                    u'name': u'OBJECTID'
                },
                {
                    u'alias': u'Numéro du titre / Title Number',
                    u'length': 16,
                    u'type': u'esriFieldTypeString',
                    u'name': u'LICENCE_NUMBER',
                    u'domain': None
                },
                {
                    u'alias': u'Superficie actuelle (ha) / Current Area (ha)',
                    u'domain': None,
                    u'type': u'esriFieldTypeDouble',
                    u'name': u'CURRENT_AREA_HA'
                },
                {
                    u'alias': u'Code du type de permis / Licence Type Code',
                    u'length': 5,
                    u'type': u'esriFieldTypeString',
                    u'name': u'AGRMT_TYPE',
                    u'domain': None
                },
                {
                    u'alias': u'Datum',
                    u'length': 8,
                    u'type': u'esriFieldTypeString',
                    u'name': u'DATUM',
                    u'domain': None
                },
                {
                    u'alias': u'Région (anglais) / Region (English)',
                    u'length': 64,
                    u'type': u'esriFieldTypeString',
                    u'name': u'REGION_E',
                    u'domain': None
                },
                {
                    u'alias': u'Région (français) / Region (French)',
                    u'length': 64,
                    u'type': u'esriFieldTypeString',
                    u'name': u'REGION_F',
                    u'domain': None
                },
                {
                    u'alias': u'Représentant / Representative',
                    u'length': 50,
                    u'type': u'esriFieldTypeString',
                    u'name': u'COMPANY_NAME',
                    u'domain': None
                },
                {
                    u'alias': u"Date d'entrée en vigueur / Effective Date",
                    u'length': 8,
                    u'type': u'esriFieldTypeDate',
                    u'name': u'LICENCE_ISSUE_DATE',
                    u'domain': None
                },
                {
                    u'alias': u"Date d'échéance / Expiry Date",
                    u'length': 8,
                    u'type': u'esriFieldTypeDate',
                    u'name': u'LICENCE_EXPIRY_DATE',
                    u'domain': None
                },
                {
                    u'alias': u"Type d'accord (anglais) / Agreement Type (English)",
                    u'length': 50,
                    u'type': u'esriFieldTypeString',
                    u'name': u'AGRMT_TYPE_E',
                    u'domain': None
                },
                {
                    u'alias': u"Type d'accord (français) / Agreement Type (French)",
                    u'length': 50,
                    u'type': u'esriFieldTypeString',
                    u'name': u'AGRMT_TYPE_F',
                    u'domain': None
                },
                {
                    u'alias': u'Shape',
                    u'domain': None,
                    u'type': u'esriFieldTypeGeometry',
                    u'name': u'SHAPE'
                }
            ],
            minScale=0,
            maxScale=0
        )
        resource_fields = handler._get_indexed_layer_fields(layer_meta)
        self.assertEquals(resource_fields['alternate'], '0-droits-ptroliers-et-gaziers-oil-and-gas-rights')


class WmsServiceHandlerTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(WmsServiceHandlerTestCase, self).setUp()

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

        self.test_user, created = get_user_model().objects.get_or_create(username="serviceowner")
        if created:
            self.test_user.set_password("somepassword")
            self.test_user.save()

        self.local_user, created = get_user_model().objects.get_or_create(username="serviceuser")
        if created:
            self.local_user.set_password("somepassword")
            self.local_user.save()

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
            handler.name, slugify(self.phony_url)[:255])

    @mock.patch("geonode.services.serviceprocessors.wms.WebMapService",
                autospec=True)
    def test_has_valid_name_when_title_exists(self, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertNotEqual(handler.name, slugify(self.phony_title))
        self.assertEqual("a-generic-title", slugify(self.phony_title))

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

    def test_local_user_cant_delete_service(self):
        self.client.logout()
        response = self.client.get(reverse('register_service'))
        self.failUnlessEqual(response.status_code, 302)
        url = 'https://demo.geo-solutions.it/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities'
        # url = "http://fake"
        service_type = enumerations.WMS
        form_data = {
            'url': url,
            'type': service_type
        }
        form = forms.CreateServiceForm(form_data)
        self.assertTrue(form.is_valid())

        self.client.login(username='serviceowner', password='somepassword')
        response = self.client.post(reverse('register_service'), data=form_data)

        s = Service.objects.all().first()
        self.failUnlessEqual(len(Service.objects.all()), 1)
        self.assertEqual(s.owner, self.test_user)

        self.client.login(username='serviceuser', password='somepassword')
        response = self.client.post(reverse('edit_service', args=(s.id,)))
        self.failUnlessEqual(response.status_code, 401)
        response = self.client.post(reverse('remove_service', args=(s.id,)))
        self.failUnlessEqual(response.status_code, 401)
        self.failUnlessEqual(len(Service.objects.all()), 1)

        self.client.login(username='serviceowner', password='somepassword')
        form_data = {
            'service-title': 'Foo Title',
            'service-description': 'Foo Description',
            'service-abstract': 'Foo Abstract',
            'service-keywords': 'Foo, Service, OWS'
        }
        form = forms.ServiceForm(form_data, instance=s, prefix="service")
        self.assertTrue(form.is_valid())

        response = self.client.post(reverse('edit_service', args=(s.id,)), data=form_data)
        self.assertEqual(s.title, 'Foo Title')
        self.assertEqual(s.description, 'Foo Description')
        self.assertEqual(s.abstract, 'Foo Abstract')
        self.assertEqual([u'Foo', u'OWS', u'Service'],
                         list(s.keywords.all().values_list('name', flat=True)))
        response = self.client.post(reverse('remove_service', args=(s.id,)))
        self.failUnlessEqual(len(Service.objects.all()), 0)


class WmsServiceHarvestingTestCase(StaticLiveServerTestCase):
    selenium = None

    @classmethod
    def setUpClass(cls):
        super(WmsServiceHarvestingTestCase, cls).setUpClass()

        try:
            cls.client = Client()
            UserModel = get_user_model()
            cls.user = UserModel.objects.create_user(username='test', password='test@123', first_name='ather',
                                                     last_name='ashraf', is_staff=True,
                                                     is_active=True, is_superuser=False)
            cls.user.save()
            cls.client.login(username='test', password='test@123')
            cls.cookie = cls.client.cookies['sessionid']
            cls.selenium = webdriver.Firefox()
            cls.selenium.implicitly_wait(10)
            cls.selenium.get(cls.live_server_url + '/')
            cls.selenium.add_cookie({'name': 'sessionid', 'value': cls.cookie.value, 'secure': False, 'path': '/'})
            cls.selenium.refresh()
            reg_url = reverse('register_service')
            cls.client.get(reg_url)

            url = 'https://demo.geo-solutions.it/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities'
            service_type = enumerations.WMS
            form_data = {
                'url': url,
                'type': service_type
            }
            forms.CreateServiceForm(form_data)

            response = cls.client.post(reverse('register_service'), data=form_data)
            cls.selenium.get(cls.live_server_url + response.url)
            cls.selenium.refresh()
        except Exception as e:
            msg = str(e)
            print msg

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
            super(WmsServiceHarvestingTestCase, cls).tearDownClass()

    def test_harvest_resources(self):
        if self.selenium:
            table = self.selenium.find_element_by_id('resource_table')
            if table:
                test_resource_table_status(self, table, False)

                self.selenium.find_element_by_id('id-filter').send_keys('atlantis:roads')
                self.selenium.find_element_by_id('btn-id-filter').click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id('name-filter').send_keys('landmarks')
                self.selenium.find_element_by_id('btn-name-filter').click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id('desc-filter').send_keys('None')
                self.selenium.find_element_by_id('btn-desc-filter').click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id('desc-filter').send_keys('')
                self.selenium.find_element_by_id('btn-desc-filter').click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id('btnClearFilter').click()
                test_resource_table_status(self, table, False)
                self.selenium.find_element_by_id('id-filter').send_keys('atlantis:tiger_roads_tiger_roads')

                self.selenium.find_element_by_id('btn-id-filter').click()
                # self.selenium.find_element_by_id('option_atlantis:tiger_roads_tiger_roads').click()
                # self.selenium.find_element_by_tag_name('form').submit()
