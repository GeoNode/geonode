# -*- coding: utf-8 -*-
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
from geonode.tests.base import GeoNodeBaseTestSupport

import os
import re
import gisdata
from urllib.parse import urljoin

from django.conf import settings

from geonode import geoserver
from geonode.decorators import on_ogc_backend

from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geonode.layers.populate_layers_data import create_layer_data

from geonode.geoserver.views import _response_callback

import logging
logger = logging.getLogger(__name__)


class HelperTest(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super(HelperTest, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_replace_layer(self):
        """
        Ensures the layer_style_manage route returns a 200.
        """
        layer = Layer.objects.all()[0]
        logger.debug(Layer.objects.all())
        self.assertIsNotNone(layer)

        logger.debug("Attempting to replace a vector layer with a raster.")
        filename = filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        vector_layer = file_upload(filename)
        self.assertTrue(vector_layer.is_vector())
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        with self.assertRaisesRegex(Exception, "You are attempting to replace a vector layer with a raster."):
            file_upload(filename, layer=vector_layer, overwrite=True)

        logger.debug("Attempting to replace a raster layer with a vector.")
        raster_layer = file_upload(filename)
        self.assertFalse(raster_layer.is_vector())
        filename = filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        with self.assertRaisesRegex(Exception, "You are attempting to replace a raster layer with a vector."):
            file_upload(filename, layer=raster_layer, overwrite=True)

        logger.debug("Attempting to replace a vector layer.")
        replaced = file_upload(filename, layer=vector_layer, overwrite=True, gtype='LineString')
        self.assertIsNotNone(replaced)
        self.assertTrue(replaced.is_vector())

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
