#########################################################################
#
# Copyright (C) 2019 OSGeo
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
import re
import logging

from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse

from geonode import geoserver
from geonode.decorators import on_ogc_backend
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.geoserver.views import _response_callback
from geonode.geoserver.helpers import get_dataset_storetype
from geonode.layers.populate_datasets_data import create_dataset_data

from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models)

logger = logging.getLogger(__name__)


class HelperTest(GeoNodeBaseTestSupport):

    type = 'dataset'

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

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
        self.user = 'admin'
        self.passwd = 'admin'
        create_dataset_data()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_replace_callback(self):
        content = f"""<Layer>
      <Title>GeoNode Local GeoServer</Title>
      <Abstract>This is a description of your Web Map Server.</Abstract>
      <!--Limited list of EPSG projections:-->
      <CRS>EPSG:4326</CRS>
      <CRS>EPSG:3785</CRS>
      <CRS>EPSG:3857</CRS>
      <CRS>EPSG:900913</CRS>
      <CRS>EPSG:32647</CRS>
      <CRS>EPSG:32736</CRS>
      <CRS>CRS:84</CRS>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>-124.731422</westBoundLongitude>
        <eastBoundLongitude>12.512771464573753</eastBoundLongitude>
        <southBoundLatitude>12.4801497</southBoundLatitude>
        <northBoundLatitude>49.371735</northBoundLatitude>
      </EX_GeographicBoundingBox>
      <BoundingBox CRS="CRS:84" ..../>
      <BoundingBox CRS="EPSG:4326" ..../>
      <BoundingBox CRS="EPSG:3785" ..../>
      <BoundingBox CRS="EPSG:3857" ..../>
      <BoundingBox CRS="EPSG:900913" ..../>
      <BoundingBox CRS="EPSG:32647" ..../>
      <BoundingBox CRS="EPSG:32736" ..../>
      <Layer queryable="1" opaque="0">
        <Name>geonode:DE_USNG_UTM18</Name>
        <Title>DE_USNG_UTM18</Title>
        <Abstract>No abstract provided</Abstract>
        <KeywordList>
          <Keyword>DE_USNG_UTM18</Keyword>
          <Keyword>features</Keyword>
        </KeywordList>
        <CRS>EPSG:26918</CRS>
        <CRS>CRS:84</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>-75.93570725669369</westBoundLongitude>
          <eastBoundLongitude>-75.00000000000001</eastBoundLongitude>
          <southBoundLatitude>38.3856300861002</southBoundLatitude>
          <northBoundLatitude>39.89406880610797</northBoundLatitude>
        </EX_GeographicBoundingBox>
        <BoundingBox CRS="CRS:84" .01" maxy="39.89406880610797"/>
        <BoundingBox CRS="EPSG:26918" ..../>
        <BoundingBox CRS="EPSG:4326" ..../>
        <BoundingBox CRS="EPSG:3785" ..../>
        <BoundingBox CRS="EPSG:3857" ..../>
        <BoundingBox CRS="EPSG:900913" ..../>
        <BoundingBox CRS="EPSG:32647" ..../>
        <BoundingBox CRS="EPSG:32736" ..../>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="FGDC">
          <Format>text/xml</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}catalogue/csw?outputschema=...."/>
        </MetadataURL>
        <MetadataURL type="other">
          <Format>other</Format>
          <OnlineResource xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}showmetadata/xsl/584"/>
        </MetadataURL>
        <Style>
          <Name>geonode:DE_USNG_UTM18</Name>
          <Title>Default Polygon</Title>
          <Abstract>A sample style that draws a polygon</Abstract>
          <LegendURL width="20" height="20">
            <Format>image/png</Format>
            <OnlineResource
xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple"
xlink:href="{settings.GEOSERVER_LOCATION}ows?service=WMS&amp;request=GetLegendGraphic&...."/>
          </LegendURL>
        </Style>
      </Layer>"""
        kwargs = {
            'content': content,
            'status': 200,
            'content_type': 'application/xml'
        }
        _content = _response_callback(**kwargs).content
        self.assertTrue(re.findall(f'{urljoin(settings.SITEURL, "/gs/")}ows', str(_content)))

        kwargs = {
            'content': content,
            'status': 200,
            'content_type': 'text/xml; charset=UTF-8'
        }
        _content = _response_callback(**kwargs).content
        self.assertTrue(re.findall(f'{urljoin(settings.SITEURL, "/gs/")}ows', str(_content)))

    def test_return_element_if_not_exists_in_the_subtypes(self):
        el = get_dataset_storetype('not-existing-type')
        self.assertEqual('not-existing-type', el)

    def test_datastore_should_return_vector(self):
        el = get_dataset_storetype('dataStore')
        self.assertEqual('vector', el)

    def test_coverageStore_should_return_raster(self):
        el = get_dataset_storetype('coverageStore')
        self.assertEqual('raster', el)

    def test_remoteStore_should_return_remote(self):
        el = get_dataset_storetype('remoteStore')
        self.assertEqual('remote', el)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_geoserver_proxy_strip_paths(self):
        response = self.client.get(f"{reverse('gs_layers')}?service=WFS&version=1.1.0&request=DescribeFeatureType&typeName=geonode:tipi_forestali&outputFormat=application/json&access_token=something")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"{reverse('ows_endpoint')}?service=WFS&version=1.1.0&request=DescribeFeatureType&typeName=geonode:tipi_forestali&outputFormat=image/png&access_token=something")
        self.assertEqual(response.status_code, 200)
