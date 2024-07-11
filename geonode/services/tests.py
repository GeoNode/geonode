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

from unittest.mock import MagicMock
from uuid import uuid4
import mock
import logging

from flaky import flaky
from selenium import webdriver
from urllib.error import HTTPError
from collections import namedtuple
from arcrest import MapService as ArcMapService
from unittest import TestCase as StandardTestCase
from owslib.wms import WebMapService as OwsWebMapService

from django.test import Client, override_settings
from django.urls import reverse
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from owslib.map.wms111 import ContentMetadata

from geonode.harvesting.models import Harvester
from geonode.layers.models import Dataset
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import resource_manager
from geonode.base import enumerations as base_enumerations
from geonode.harvesting.harvesters.wms import WebMapService
from geonode.services.utils import parse_services_types, test_resource_table_status

from . import enumerations, forms
from .models import Service
from .serviceprocessors import base, wms, arcgis, get_service_handler, get_available_service_types
from .serviceprocessors.arcgis import ArcImageServiceHandler, ArcMapServiceHandler, MapLayer

logger = logging.getLogger(__name__)


class ModuleFunctionsTestCase(StandardTestCase):
    @mock.patch("geonode.services.serviceprocessors.base.catalog", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.settings", autospec=True)
    def test_get_cascading_workspace_returns_existing(self, mock_settings, mock_catalog):
        mock_settings.OGC_SERVER = {
            "default": {
                "LOCATION": "nowhere/",
                "USER": "nouser",
                "PASSWORD": "nopass",
            }
        }
        mock_settings.CASCADE_WORKSPACE = "something"
        phony_workspace = "fake"
        cat = mock_catalog
        cat.get_workspace.return_value = phony_workspace
        result = base.get_geoserver_cascading_workspace(create=False)
        self.assertEqual(result, phony_workspace)
        cat.get_workspace.assert_called_with(mock_settings.CASCADE_WORKSPACE)

    @mock.patch("geonode.services.serviceprocessors.base.catalog", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.settings", autospec=True)
    def test_get_cascading_workspace_creates_new_workspace(self, mock_settings, mock_catalog):
        mock_settings.OGC_SERVER = {
            "default": {
                "LOCATION": "nowhere/",
                "USER": "nouser",
                "PASSWORD": "nopass",
            }
        }
        mock_settings.CASCADE_WORKSPACE = "something"
        phony_workspace = "fake"
        cat = mock_catalog
        cat.get_workspace.return_value = None
        cat.create_workspace.return_value = phony_workspace
        result = base.get_geoserver_cascading_workspace(create=True)
        self.assertEqual(result, phony_workspace)
        cat.get_workspace.assert_called_with(mock_settings.CASCADE_WORKSPACE)
        cat.create_workspace.assert_called_with(
            mock_settings.CASCADE_WORKSPACE, f"http://www.geonode.org/{mock_settings.CASCADE_WORKSPACE}"
        )

    @mock.patch("geonode.services.serviceprocessors.get_available_service_types", autospec=True)
    def test_get_service_handler_wms(self, mock_wms_handler):
        _handler = MagicMock()
        mock_wms_handler.return_value = {
            enumerations.WMS: {"OWS": True, "handler": _handler, "label": "Web Map Service"}
        }
        phony_url = "http://fake"
        get_service_handler(phony_url, service_type=enumerations.WMS)
        _handler.assert_called_with(phony_url, None)

    @mock.patch("arcrest.MapService", autospec=True)
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
                    "maxScale": 0,
                }
            ],
            "tables": [],
            "spatialReference": {"wkid": 4140, "latestWkid": 4617},
            "singleFusedMapCache": False,
            "initialExtent": {
                "xmin": -144.97375000000002,
                "ymin": 58.90551066699999,
                "xmax": -57.55125000000002,
                "ymax": 91.84630866699999,
                "spatialReference": {"wkid": 4140, "latestWkid": 4617},
            },
            "fullExtent": {
                "xmin": -144.97375,
                "ymin": 34.637024667000006,
                "xmax": -57.55125,
                "ymax": 91.84630866699999,
                "spatialReference": {"wkid": 4140, "latestWkid": 4617},
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
                "Keywords": "Droits petroliers et gaziers,Oil and Gas Rights",
            },
            "capabilities": "Map,Query,Data",
            "supportedQueryFormats": "JSON, AMF, geoJSON",
            "exportTilesAllowed": False,
            "supportsDatumTransformation": True,
            "maxRecordCount": 1000,
            "maxImageHeight": 2048,
            "maxImageWidth": 2048,
            "supportedExtensions": "FeatureServer, KmlServer, WFSServer, WMSServer",
        }

        mock_arcgis_service_json_struct = {
            "supportsDynamicLayers": False,
            "initialExtent": {
                "xmin": -144.97375000000002,
                "ymin": 58.90551066699999,
                "ymax": 91.84630866699999,
                "xmax": -57.55125000000002,
                "spatialReference": {"wkid": 4140, "latestWkid": 4617},
            },
            "documentInfo": {
                "Category": "",
                "Author": "",
                "TextAntialiasingMode": "Force",
                "Title": "Droits petroliers et gaziers / Oil and Gas Rights",
                "Comments": "Droits petroliers et gaziers / Oil and Gas Rights",
                "AntialiasingMode": "None",
                "Keywords": "Droits petroliers et gaziers,Oil and Gas Rights",
                "Subject": "Droits petroliers et gaziers / Oil and Gas Rights",
            },
            "spatialReference": {"wkid": 4140, "latestWkid": 4617},
            "description": "",
            "layers": [
                {
                    "name": "Droits pétroliers et gaziers / Oil and Gas Rights",
                    "maxScale": 0,
                    "defaultVisibility": True,
                    "parentLayerId": -1,
                    "id": 0,
                    "minScale": 0,
                    "subLayerIds": None,
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
                "spatialReference": {"wkid": 4140, "latestWkid": 4617},
            },
            "singleFusedMapCache": False,
            "supportsDatumTransformation": True,
            "maxImageWidth": 2048,
            "maxScale": 0,
            "copyrightText": "",
            "minScale": 0,
            "serviceDescription": "Droits petroliers et gaziers / Oil and Gas Rights",
        }

        phony_url = "http://fake"
        mock_parsed_arcgis = mock.MagicMock(ArcMapService).return_value
        (url, mock_parsed_arcgis) = mock.MagicMock(
            ArcMapService, return_value=(phony_url, mock_parsed_arcgis)
        ).return_value
        mock_parsed_arcgis.url = phony_url
        mock_parsed_arcgis._contents = mock_arcgis_service_contents
        mock_parsed_arcgis._json_struct = mock_arcgis_service_json_struct

        mock_map_service.return_value = (phony_url, mock_parsed_arcgis)

        handler = arcgis.ArcImageServiceHandler(phony_url)
        self.assertEqual(handler.url, phony_url)

        LayerESRIExtent = namedtuple("LayerESRIExtent", "spatialReference xmin ymin ymax xmax")
        LayerESRIExtentSpatialReference = namedtuple("LayerESRIExtentSpatialReference", "wkid latestWkid")

        dataset_meta = MapLayer(
            id=0,
            title="Droits pétroliers et gaziers / Oil and Gas Rights",
            abstract="Droits pétroliers et gaziers / Oil and Gas Rights",
            type="Feature Dataset",
            geometryType="esriGeometryPolygon",
            copyrightText="",
            extent=LayerESRIExtent(
                LayerESRIExtentSpatialReference(4140, 4617),
                -144.97375,
                34.637024667000006,
                91.84630866699999,
                -57.55125,
            ),
            fields=[
                {"alias": "OBJECTID", "domain": None, "type": "esriFieldTypeOID", "name": "OBJECTID"},
                {
                    "alias": "Numéro du titre / Title Number",
                    "length": 16,
                    "type": "esriFieldTypeString",
                    "name": "LICENCE_NUMBER",
                    "domain": None,
                },
                {
                    "alias": "Superficie actuelle (ha) / Current Area (ha)",
                    "domain": None,
                    "type": "esriFieldTypeDouble",
                    "name": "CURRENT_AREA_HA",
                },
                {
                    "alias": "Code du type de permis / Licence Type Code",
                    "length": 5,
                    "type": "esriFieldTypeString",
                    "name": "AGRMT_TYPE",
                    "domain": None,
                },
                {"alias": "Datum", "length": 8, "type": "esriFieldTypeString", "name": "DATUM", "domain": None},
                {
                    "alias": "Région (anglais) / Region (English)",
                    "length": 64,
                    "type": "esriFieldTypeString",
                    "name": "REGION_E",
                    "domain": None,
                },
                {
                    "alias": "Région (français) / Region (French)",
                    "length": 64,
                    "type": "esriFieldTypeString",
                    "name": "REGION_F",
                    "domain": None,
                },
                {
                    "alias": "Représentant / Representative",
                    "length": 50,
                    "type": "esriFieldTypeString",
                    "name": "COMPANY_NAME",
                    "domain": None,
                },
                {
                    "alias": "Date d'entrée en vigueur / Effective Date",
                    "length": 8,
                    "type": "esriFieldTypeDate",
                    "name": "LICENCE_ISSUE_DATE",
                    "domain": None,
                },
                {
                    "alias": "Date d'échéance / Expiry Date",
                    "length": 8,
                    "type": "esriFieldTypeDate",
                    "name": "LICENCE_EXPIRY_DATE",
                    "domain": None,
                },
                {
                    "alias": "Type d'accord (anglais) / Agreement Type (English)",
                    "length": 50,
                    "type": "esriFieldTypeString",
                    "name": "AGRMT_TYPE_E",
                    "domain": None,
                },
                {
                    "alias": "Type d'accord (français) / Agreement Type (French)",
                    "length": 50,
                    "type": "esriFieldTypeString",
                    "name": "AGRMT_TYPE_F",
                    "domain": None,
                },
                {"alias": "Shape", "domain": None, "type": "esriFieldTypeGeometry", "name": "SHAPE"},
            ],
            minScale=0,
            maxScale=0,
        )
        resource_fields = handler._get_indexed_dataset_fields(dataset_meta)
        self.assertEqual(resource_fields["alternate"], f"{slugify(phony_url)}:{dataset_meta.id}")

    @mock.patch("arcrest.MapService", autospec=True)
    def test_get_arcgis_alternative_structure(self, mock_map_service):
        LayerESRIExtent = namedtuple("LayerESRIExtent", "spatialReference xmin ymin ymax xmax")
        LayerESRIExtentSpatialReference = namedtuple("LayerESRIExtentSpatialReference", "wkid latestWkid")

        mock_arcgis_service_contents = {
            "copyrightText": "",
            "description": "",
            "documentInfo": {
                "Author": "Administrator",
                "Category": "",
                "Comments": "",
                "Keywords": "",
                "Subject": "",
                "Title": "basemap_ortofoto_AGEA2011",
            },
            "fullExtent": {
                "xmax": 579764.2319999984,
                "xmin": 386130.6820000001,
                "ymax": 4608909.064,
                "ymin": 4418016.7140000025,
            },
            "initialExtent": {
                "xmax": 605420.5635976626,
                "xmin": 349091.7176066373,
                "ymax": 4608197.140968505,
                "ymin": 4418728.637031497,
            },
            "layers": [
                {
                    "copyrightText": "",
                    "definitionExpression": "",
                    "description": "",
                    "displayField": "",
                    "extent": LayerESRIExtent(
                        LayerESRIExtentSpatialReference(None, None),
                        570962.7069999985,
                        4600232.139,
                        394932.207,
                        4426693.639000002,
                    ),
                    "fields": [],
                    "geometryType": "",
                    "id": 1,
                    "maxScale": 0.0,
                    "minScale": 0.0,
                    "name": "Regione_Campania.ecw",
                    "title": "Regione_Campania.ecw",
                    "parentLayer": {"id": -1, "name": "-1"},
                    "subLayers": [],
                    "type": "Raster Dataset",
                }
            ],
            "mapName": "Layers",
            "serviceDescription": "",
            "singleFusedMapCache": True,
            "spatialReference": None,
            "tileInfo": {
                "cols": 512,
                "compressionQuality": 0,
                "dpi": 96,
                "format": "PNG8",
                "lods": [
                    {"level": 0, "resolution": 185.20870375074085, "scale": 700000.0},
                    {"level": 1, "resolution": 66.1459656252646, "scale": 250000.0},
                    {"level": 2, "resolution": 26.458386250105836, "scale": 100000.0},
                    {"level": 3, "resolution": 19.843789687579378, "scale": 75000.0},
                    {"level": 4, "resolution": 13.229193125052918, "scale": 50000.0},
                    {"level": 5, "resolution": 6.614596562526459, "scale": 25000.0},
                    {"level": 6, "resolution": 2.6458386250105836, "scale": 10000.0},
                    {"level": 7, "resolution": 1.3229193125052918, "scale": 5000.0},
                    {"level": 8, "resolution": 0.5291677250021167, "scale": 2000.0},
                ],
                "origin": {"x": 289313.907000001, "y": 4704355.239},
                "rows": 512,
                "spatialReference": None,
            },
            "units": "esriMeters",
        }

        phony_url = "http://sit.cittametropolitana.na.it/arcgis/rest/services/basemap_ortofoto_AGEA2011/MapServer"
        mock_parsed_arcgis = mock.MagicMock(ArcMapService).return_value
        (url, mock_parsed_arcgis) = mock.MagicMock(
            ArcMapService, return_value=(phony_url, mock_parsed_arcgis)
        ).return_value
        mock_parsed_arcgis.url = phony_url
        mock_parsed_arcgis.layers = mock_arcgis_service_contents["layers"]
        mock_parsed_arcgis._contents = mock_arcgis_service_contents
        mock_parsed_arcgis._json_struct = mock_arcgis_service_contents

        mock_map_service.return_value = (phony_url, mock_parsed_arcgis)

        handler = arcgis.ArcImageServiceHandler(phony_url)
        self.assertEqual(handler.url, phony_url)

        dataset_meta = handler._dataset_meta(mock_parsed_arcgis.layers[0])
        self.assertIsNotNone(dataset_meta)
        self.assertEqual(dataset_meta.id, 1)
        resource_fields = handler._get_indexed_dataset_fields(dataset_meta)
        self.assertEqual(resource_fields["alternate"], f"{slugify(phony_url)}:{dataset_meta.id}")

        test_user, created = get_user_model().objects.get_or_create(username="serviceowner")
        if created:
            test_user.set_password("somepassword")
            test_user.save()
        try:
            result = handler.create_geonode_service(test_user)
            geonode_service, created = Service.objects.get_or_create(base_url=result.base_url, owner=test_user)
            for _d in Dataset.objects.filter(remote_service=geonode_service):
                resource_manager.delete(_d.uuid, instance=_d)

            handler._harvest_resource(dataset_meta, geonode_service)
            geonode_dataset = Dataset.objects.filter(remote_service=geonode_service).get()
            self.assertIsNotNone(geonode_dataset)
            self.assertNotEqual(geonode_dataset.srid, "EPSG:4326")
            self.assertEqual(geonode_dataset.sourcetype, base_enumerations.SOURCE_TYPE_REMOTE)
            self.client.login(username="admin", password="admin")
            response = self.client.get(reverse("dataset_embed", args=(geonode_dataset.name,)))
            self.assertEqual(response.status_code, 200)
            for _d in Dataset.objects.filter(remote_service=geonode_service):
                resource_manager.delete(_d.uuid, instance=_d)
        except (Service.DoesNotExist, HTTPError) as e:
            # In the case the Service URL becomes inaccessible for some reason
            logger.error(e)


class WmsServiceHandlerTestCase(GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()

        self.phony_url = "http://a-really-long-and-fake-name-here-so-that-" "we-use-it-in-tests"
        self.phony_title = "a generic title"
        self.phony_version = "s.version"
        self.phony_dataset_name = "phony_name"
        self.phony_keywords = ["first", "second"]
        mock_parsed_wms = mock.MagicMock(OwsWebMapService).return_value
        (url, mock_parsed_wms) = mock.MagicMock(
            WebMapService, return_value=(self.phony_url, mock_parsed_wms)
        ).return_value
        mock_parsed_wms.provider.url = self.phony_url
        mock_parsed_wms.identification.abstract = None
        mock_parsed_wms.identification.title = self.phony_title
        mock_parsed_wms.identification.version = self.phony_version
        mock_parsed_wms.identification.keywords = self.phony_keywords
        mock_parsed_wms_getcapa_operation = {
            "name": "GetCapabilities",
            "methods": [{"type": "Get", "url": self.phony_url}],
        }
        mock_parsed_wms.operations = [
            mock_parsed_wms_getcapa_operation,
        ]
        mock_dataset_meta = mock.MagicMock(ContentMetadata)
        mock_dataset_meta.name = self.phony_dataset_name
        mock_dataset_meta.title = self.phony_dataset_name
        mock_dataset_meta.abstract = ""
        mock_dataset_meta.keywords = []
        mock_dataset_meta.children = []
        mock_dataset_meta.crsOptions = ["EPSG:3857"]
        mock_dataset_meta.boundingBox = [-5000, -5000, 5000, 5000, "EPSG:3857"]
        mock_parsed_wms.contents = {
            mock_dataset_meta.name: mock_dataset_meta,
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

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_has_correct_url(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.url, self.phony_url)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_has_valid_name_when_no_title_exists(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms.return_value[1].identification.title = ""
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.name, slugify(self.phony_url)[:255])

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_has_valid_name_when_title_exists(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertNotEqual(handler.name, slugify(self.phony_title))
        self.assertEqual("a-generic-title", slugify(self.phony_title))

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_has_correct_service_type(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.service_type, enumerations.WMS)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings", autospec=True)
    def test_detects_indexed_service(self, mock_settings, mock_wms_parsed_service, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.indexing_method, enumerations.INDEXED)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings", autospec=True)
    def test_detects_cascaded_service(self, mock_settings, mock_wms_parsed_service, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_dataset_meta = mock.MagicMock(ContentMetadata)
        mock_dataset_meta.name = "phony_name"
        mock_dataset_meta.children = []
        mock_dataset_meta.crsOptions = ["EPSG:4326"]
        self.parsed_wms.contents = {
            mock_dataset_meta.name: mock_dataset_meta,
        }
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        self.assertEqual(handler.indexing_method, enumerations.INDEXED)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch.object(wms.WmsServiceHandler, "parsed_service")
    def test_create_geonode_service(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        mock_wms_parsed_service.provider.url = self.phony_url
        mock_wms_parsed_service.identification.title = self.phony_title
        mock_wms_parsed_service.identification.version = self.phony_version
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.create_geonode_service(self.test_user)
        self.assertEqual(result.base_url, self.phony_url)
        self.assertEqual(result.type, handler.service_type)
        self.assertEqual(result.method, handler.indexing_method)
        self.assertEqual(result.owner, self.test_user)
        self.assertEqual(result.version, self.phony_version)
        self.assertEqual(result.name, handler.name)
        self.assertEqual(result.title, self.phony_title)
        # mata_data_only is set to Try
        self.assertTrue(result.metadata_only)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_geonode_service_uses_given_getmap_params(self, mock_wms_parsed_service, mock_wms):
        phony_url = (
            "https://www.geoportal.hessen.de/mapbender/php/wms.php?"
            "layer_id=36995&PHPSESSID=27jb139lqk29rmul77beuji261&"
            "withChilds=1&"
            "version=1.1.1&"
            "REQUEST=GetCapabilities&"
            "SERVICE=WMS"
        )
        mock_wms.return_value = (phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        mock_wms_parsed_service.provider.url = self.phony_url
        mock_wms_parsed_service.identification.title = self.phony_title
        mock_wms_parsed_service.identification.version = self.phony_version
        handler = wms.WmsServiceHandler(phony_url)
        result = handler.create_geonode_service(self.test_user)
        self.assertEqual(result.base_url, "https://www.geoportal.hessen.de/mapbender/php/wms.php")
        self.assertEqual(
            result.extra_queryparams,
            "layer_id=36995&PHPSESSID=27jb139lqk29rmul77beuji261&withChilds=1&REQUEST=GetCapabilities&SERVICE=WMS",
        )
        self.assertEqual(result.service_url, f"{result.base_url}?{result.extra_queryparams}")
        self.assertEqual(result.type, handler.service_type)
        self.assertEqual(result.method, handler.indexing_method)
        self.assertEqual(result.owner, self.test_user)
        self.assertEqual(result.version, self.phony_version)
        self.assertEqual(result.name, handler.name)
        self.assertEqual(result.title, self.phony_title)
        # mata_data_only is set to Try
        self.assertTrue(result.metadata_only)
        self.assertDictEqual(
            result.operations,
            {
                "GetCapabilities": {
                    "name": "GetCapabilities",
                    "methods": [
                        {"type": "Get", "url": "http://a-really-long-and-fake-name-here-so-that-we-use-it-in-tests"}
                    ],
                    "formatOptions": [],
                }
            },
        )

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch.object(wms.WmsServiceHandler, "parsed_service")
    def test_get_keywords(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        mock_wms_parsed_service.identification.keywords = self.phony_keywords
        mock_wms_parsed_service.identification.title = self.phony_title
        mock_wms_parsed_service.identification.version = self.phony_version
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.get_keywords()
        self.assertEqual(result, self.phony_keywords)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    def test_get_resource(self, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler.get_resource(self.phony_dataset_name)
        self.assertIsNone(result)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.get_resources", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.get_resource", autospec=True)
    def test_get_resources(self, mock_wms_get_resource, mock_wms_get_resources, mock_wms_parsed_service, mock_wms):
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        mock_wms_parsed_service.provider.url = self.phony_url
        mock_wms_parsed_service.identification.title = self.phony_title
        mock_wms_parsed_service.identification.version = self.phony_version
        mock_wms_get_resource.return_value = list(self.parsed_wms.contents.values())[0]
        mock_wms_get_resources.return_value = self.parsed_wms.contents.values()
        handler = wms.WmsServiceHandler(self.phony_url)
        result = list(handler.get_resources())
        self.assertEqual(len(result), 1)
        test_user, created = get_user_model().objects.get_or_create(username="serviceowner")
        if created:
            test_user.set_password("somepassword")
            test_user.save()
        result = handler.create_geonode_service(test_user)
        try:
            geonode_service, created = Service.objects.get_or_create(base_url=result.base_url, owner=test_user)
            for _d in Dataset.objects.filter(remote_service=geonode_service):
                resource_manager.delete(_d.uuid, instance=_d)

            result = list(handler.get_resources())
            dataset_meta = handler.get_resource(result[0].name)
            resource_fields = handler._get_indexed_dataset_fields(dataset_meta)
            keywords = resource_fields.pop("keywords")
            resource_fields["keywords"] = keywords
            resource_fields["is_approved"] = True
            resource_fields["is_published"] = True
        except Service.DoesNotExist as e:
            # In the case the Service URL becomes inaccessible for some reason
            logger.error(e)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings", autospec=True)
    def test_offers_geonode_projection(self, mock_settings, mock_wms_parsed_service, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler._offers_geonode_projection()
        self.assertTrue(result)

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.wms.settings", autospec=True)
    def test_does_not_offer_geonode_projection(self, mock_settings, mock_wms_parsed_service, mock_wms):
        mock_settings.DEFAULT_MAP_CRS = "EPSG:3857"
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        self.parsed_wms.contents[self.phony_dataset_name].crsOptions = ["EPSG:4326"]
        handler = wms.WmsServiceHandler(self.phony_url)
        result = handler._offers_geonode_projection()
        self.assertEqual(result, "EPSG:3857")

    @mock.patch("geonode.harvesting.harvesters.wms.WebMapService")
    @mock.patch("geonode.services.serviceprocessors.wms.WmsServiceHandler.parsed_service", autospec=True)
    @mock.patch("geonode.services.serviceprocessors.base.get_geoserver_" "cascading_workspace", autospec=True)
    def test_get_store(self, mock_get_gs_cascading_store, mock_wms_parsed_service, mock_wms):
        mock_workspace = mock_get_gs_cascading_store.return_value
        mock_catalog = mock_workspace.catalog
        mock_catalog.get_store.return_value = None
        mock_wms.return_value = (self.phony_url, self.parsed_wms)
        mock_wms_parsed_service.return_value = self.parsed_wms
        handler = wms.WmsServiceHandler(self.phony_url)
        handler._get_store(create=True)
        mock_catalog.create_wmsstore.assert_called_with(
            name=handler.name, workspace=mock_workspace, user=mock_catalog.username, password=mock_catalog.password
        )

    @flaky(max_runs=3)
    def test_local_user_cant_delete_service(self):
        self.client.logout()
        response = self.client.get(reverse("register_service"))
        self.assertEqual(response.status_code, 302)
        url = "https://maps.geosolutionsgroup.com/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities"
        # url = "http://fake"
        service_type = enumerations.WMS
        form_data = {"url": url, "type": service_type}
        form = forms.CreateServiceForm(form_data)
        # The service sometimes is not available, therefore the form won't be valid...
        if form.is_valid():
            self.client.login(username="serviceowner", password="somepassword")
            response = self.client.post(reverse("register_service"), data=form_data)

            s = Service.objects.all().first()
            self.assertEqual(len(Service.objects.all()), 1)
            self.assertEqual(s.owner, self.test_user)

            self.client.login(username="serviceuser", password="somepassword")
            response = self.client.post(reverse("edit_service", args=(s.id,)))
            self.assertEqual(response.status_code, 401)
            response = self.client.post(reverse("remove_service", args=(s.id,)))
            self.assertEqual(response.status_code, 401)
            self.assertEqual(len(Service.objects.all()), 1)

            self.client.login(username="serviceowner", password="somepassword")
            form_data = {
                "service-title": "Foo Title",
                "service-description": "Foo Description",
                "service-abstract": "Foo Abstract",
                "service-keywords": "Foo, Service, OWS",
            }
            form = forms.ServiceForm(form_data, instance=s, prefix="service")
            self.assertTrue(form.is_valid())

            response = self.client.post(reverse("edit_service", args=(s.id,)), data=form_data)
            self.assertEqual(s.title, "Foo Title")
            self.assertEqual(s.description, "Foo Description")
            self.assertEqual(s.abstract, "Foo Abstract")
            self.assertSetEqual({"Foo", "OWS", "Service"}, set(list(s.keywords.values_list("name", flat=True))))
            response = self.client.post(reverse("remove_service", args=(s.id,)))
            self.assertEqual(len(Service.objects.all()), 0)

    def test_removing_the_service_delete_also_the_harvester(self):
        """
        If the user delete the service, the corrisponding harvester object should be deleted too
        """
        owner = get_user_model().objects.get(username="admin")
        # creating the service
        dummy_service = Service.objects.create(
            uuid=str(uuid4()), owner=owner, title="test service removing", is_approved=True
        )
        # creating the harvester
        harvester = Harvester.objects.create(
            remote_url="http://fake1.com",
            name="harvester1",
            default_owner=owner,
            harvester_type="geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker",
        )
        dummy_service.harvester = harvester
        dummy_service.save()

        self.client.login(username="admin", password="admin")

        response = self.client.post(reverse("remove_service", args=(dummy_service.id,)))
        self.assertEqual(302, response.status_code)
        self.assertFalse(Service.objects.filter(id=dummy_service.id).exists())
        self.assertFalse(Harvester.objects.filter(id=harvester.id).exists())

    @flaky(max_runs=3)
    def test_add_duplicate_remote_service_url(self):
        form_data = {
            "url": "https://gs-stable.geo-solutions.it/geoserver/wms?service=wms&version=1.3.0&request=GetCapabilities",
            "type": enumerations.WMS,
        }

        self.client.login(username="serviceowner", password="somepassword")

        # Add the first resource
        url = "https://gs-stable.geo-solutions.it/geoserver/wms?service=wms&version=1.3.0&request=GetCapabilities"
        # url = "http://fake"
        service_type = enumerations.WMS
        form_data = {"url": url, "type": service_type}
        form = forms.CreateServiceForm(form_data)
        # The service sometimes is not available, therefore the form won't be valid...
        if form.is_valid():
            self.assertEqual(Service.objects.count(), 0)
            self.client.post(reverse("register_service"), data=form_data)
            self.assertEqual(Service.objects.count(), 1)

            # Try adding the same URL again
            form = forms.CreateServiceForm(form_data)
            self.assertEqual(Service.objects.count(), 1)
            with self.assertRaises(IntegrityError):
                self.client.post(reverse("register_service"), data=form_data)
            self.assertEqual(Service.objects.count(), 1)


class WmsServiceHarvestingTestCase(StaticLiveServerTestCase):
    selenium = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        try:
            cls.client = Client()
            UserModel = get_user_model()
            cls.user = UserModel.objects.create_user(
                username="test",
                password="test@123",
                first_name="ather",
                last_name="ashraf",
                is_staff=True,
                is_active=True,
                is_superuser=False,
            )
            cls.user.save()
            cls.client.login(username="test", password="test@123")
            cls.cookie = cls.client.cookies["sessionid"]
            cls.selenium = webdriver.Firefox()
            cls.selenium.implicitly_wait(10)
            cls.selenium.get(f"{cls.live_server_url}/")
            cls.selenium.add_cookie({"name": "sessionid", "value": cls.cookie.value, "secure": False, "path": "/"})
            cls.selenium.refresh()
            reg_url = reverse("register_service")
            cls.client.get(reg_url)

            url = "https://gs-stable.geo-solutions.it/geoserver/wms"
            service_type = enumerations.WMS
            form_data = {"url": url, "type": service_type}
            forms.CreateServiceForm(form_data)

            response = cls.client.post(reverse("register_service"), data=form_data)
            cls.selenium.get(cls.live_server_url + response.url)
            cls.selenium.refresh()
        except Exception as e:
            msg = str(e)
            print(msg)

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
            super().tearDownClass()

    def test_harvest_resources(self):
        if self.selenium:
            table = self.selenium.find_element_by_id("resource_table")
            if table:
                test_resource_table_status(self, table, False)

                self.selenium.find_element_by_id("id-filter").send_keys("atlantis:roads")
                self.selenium.find_element_by_id("btn-id-filter").click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id("name-filter").send_keys("landmarks")
                self.selenium.find_element_by_id("btn-name-filter").click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id("desc-filter").send_keys("None")
                self.selenium.find_element_by_id("btn-desc-filter").click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id("desc-filter").send_keys("")
                self.selenium.find_element_by_id("btn-desc-filter").click()
                test_resource_table_status(self, table, True)

                self.selenium.find_element_by_id("btnClearFilter").click()
                test_resource_table_status(self, table, False)
                self.selenium.find_element_by_id("id-filter").send_keys("atlantis:tiger_roads_tiger_roads")

                self.selenium.find_element_by_id("btn-id-filter").click()
                # self.selenium.find_element_by_id('option_atlantis:tiger_roads_tiger_roads').click()
                # self.selenium.find_element_by_tag_name('form').submit()


SERVICES_TYPE_MODULES = [
    "geonode.services.tests.dummy_services_type",
    "geonode.services.tests.dummy_services_type2",
]


class TestServiceViews(GeoNodeBaseTestSupport):
    def setUp(self):
        self.user = "admin"
        self.passwd = "admin"
        self.admin = get_user_model().objects.get(username="admin")
        self.sut, _ = Service.objects.get_or_create(
            type=enumerations.WMS,
            name="Bogus",
            title="Pocus",
            owner=self.admin,
            method=enumerations.INDEXED,
            metadata_only=True,
            base_url="http://bogus.pocus.com/ows",
        )
        self.sut.clear_dirty_state()

    def test_user_admin_can_access_to_page(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse("services"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_see_the_services(self):
        response = self.client.get(reverse("services"))
        self.assertEqual(response.status_code, 200)

    @override_settings(SERVICES_TYPE_MODULES=SERVICES_TYPE_MODULES)
    def test_will_use_multiple_service_types_defined(self):
        elems = parse_services_types()
        expected = {
            "test": {
                "OWS": True,
                "handler": "TestHandler",
                "label": "Test Number 1",
                "management_view": "path.to.view1",
            },
            "test2": {
                "OWS": False,
                "handler": "TestHandler2",
                "label": "Test Number 2",
                "management_view": "path.to.view2",
            },
            "test3": {
                "OWS": True,
                "handler": "TestHandler3",
                "label": "Test Number 3",
                "management_view": "path.to.view3",
            },
            "test4": {
                "OWS": False,
                "handler": "TestHandler4",
                "label": "Test Number 4",
                "management_view": "path.to.view4",
            },
        }
        self.assertDictEqual(expected, elems)

    @override_settings(SERVICES_TYPE_MODULES=SERVICES_TYPE_MODULES)
    def test_will_use_multiple_service_types_defined_for_choices(self):
        elems = get_available_service_types()
        expected = {
            "WMS": {"OWS": True, "handler": wms.WmsServiceHandler, "label": "Web Map Service"},
            "GN_WMS": {"OWS": True, "handler": wms.GeoNodeServiceHandler, "label": "GeoNode (Web Map Service)"},
            "REST_MAP": {"OWS": False, "handler": ArcMapServiceHandler, "label": "ArcGIS REST MapServer"},
            "REST_IMG": {"OWS": False, "handler": ArcImageServiceHandler, "label": "ArcGIS REST ImageServer"},
            "test": {
                "OWS": True,
                "handler": "TestHandler",
                "label": "Test Number 1",
                "management_view": "path.to.view1",
            },
            "test2": {
                "OWS": False,
                "handler": "TestHandler2",
                "label": "Test Number 2",
                "management_view": "path.to.view2",
            },
            "test3": {
                "OWS": True,
                "handler": "TestHandler3",
                "label": "Test Number 3",
                "management_view": "path.to.view3",
            },
            "test4": {
                "OWS": False,
                "handler": "TestHandler4",
                "label": "Test Number 4",
                "management_view": "path.to.view4",
            },
        }
        self.assertDictEqual(expected, elems)


"""
Just a dummy function required for the smoke test above
"""


class dummy_services_type:
    services_type = {
        "test": {"OWS": True, "handler": "TestHandler", "label": "Test Number 1", "management_view": "path.to.view1"},
        "test2": {
            "OWS": False,
            "handler": "TestHandler2",
            "label": "Test Number 2",
            "management_view": "path.to.view2",
        },
    }


class dummy_services_type2:
    services_type = {
        "test3": {"OWS": True, "handler": "TestHandler3", "label": "Test Number 3", "management_view": "path.to.view3"},
        "test4": {
            "OWS": False,
            "handler": "TestHandler4",
            "label": "Test Number 4",
            "management_view": "path.to.view4",
        },
    }
