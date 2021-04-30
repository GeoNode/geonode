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
import json
import base64
import shutil
import tempfile

from urllib.parse import urljoin, urlencode
from django.core.management import call_command
from os.path import basename, splitext

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from guardian.shortcuts import assign_perm, remove_perm

from geonode import geoserver
from geonode.base.models import Configuration
from geonode.decorators import on_ogc_backend

from geonode.layers.models import Layer, Style
from geonode.layers.populate_layers_data import create_layer_data
from geonode.geoserver.helpers import (
    gs_catalog,
    get_sld_for,
    OGC_Servers_Handler,
    extract_name_from_sld)

import logging

logger = logging.getLogger(__name__)

san_andres_y_providencia_sld = """<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:gml="http://www.opengis.net/gml"
  version="1.0.0"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <sld:NamedLayer>
    <sld:Name>geonode:san_andres_y_providencia_administrative</sld:Name>
    <sld:UserStyle>
      <sld:Name>san_andres_y_providencia_administrative</sld:Name>
      <sld:Title>San Andres y Providencia Administrative</sld:Title>
      <sld:IsDefault>1</sld:IsDefault>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:LineSymbolizer>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#880000</sld:CssParameter>
              <sld:CssParameter name="stroke-width">3</sld:CssParameter>
              <sld:CssParameter name="stroke-dasharray">4.0 4.0</sld:CssParameter>
            </sld:Stroke>
          </sld:LineSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:LineSymbolizer>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#ffbbbb</sld:CssParameter>
              <sld:CssParameter name="stroke-width">2</sld:CssParameter>
            </sld:Stroke>
          </sld:LineSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
"""

lac_sld = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  version="1.1.0" xmlns:xlink="http://www.w3.org/1999/xlink"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd"
  xmlns:se="http://www.opengis.net/se">
  <NamedLayer>
    <se:Name>LAC_NonIndigenous_Access_to_Sanitation2</se:Name>
    <UserStyle>
      <se:Name>LAC NonIndigenous Access to Sanitation</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name> Low (25 - 40%) </se:Name>
          <se:Description>
            <se:Title> Low (25 - 40%) </se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>24.89999999999999858</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>39.89999999999999858</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#ff8b16</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> Medium Low (40 - 65 %)</se:Name>
          <se:Description>
            <se:Title> Medium Low (40 - 65 %)</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>39.89999999999999858</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>64.90000000000000568</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#fffb0b</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> Medium (65 - 70 %) </se:Name>
          <se:Description>
            <se:Title> Medium (65 - 70 %) </se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>64.90000000000000568</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>69.90000000000000568</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#55d718</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> Medium High (70 - 85 %) </se:Name>
          <se:Description>
            <se:Title> Medium High (70 - 85 %) </se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>69.90000000000000568</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>84.90000000000000568</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#3f7122</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> High (85 - 93 %) </se:Name>
          <se:Description>
            <se:Title> High (85 - 93 %) </se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>84.90000000000000568</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>92.90000000000000568</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#76ffff</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> Very High (93 - 96 %) </se:Name>
          <se:Description>
            <se:Title> Very High (93 - 96 %) </se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>92.90000000000000568</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>96.09999999999999432</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#0a4291</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
        <se:Rule>
          <se:Name> Country not surveyed</se:Name>
          <se:Description>
            <se:Title> Country not surveyed</se:Title>
          </se:Description>
          <ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>-999</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>NonInd</ogc:PropertyName>
                <ogc:Literal>24.89999999999999858</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <se:PolygonSymbolizer>
            <se:Fill>
              <se:SvgParameter name="fill">#d9d9d9</se:SvgParameter>
            </se:Fill>
            <se:Stroke>
              <se:SvgParameter name="stroke">#000001</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.1</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">bevel</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""

freshgwabs2_sld = """<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:gml="http://www.opengis.net/gml"
  version="1.0.0"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <sld:NamedLayer>
    <sld:Name>geonode:freshgwabs2</sld:Name>
    <sld:UserStyle>
      <sld:Name>freshgwabs2</sld:Name>
      <sld:IsDefault>1</sld:IsDefault>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:Name>&lt; 1112 million cubic metres</sld:Name>
          <sld:Title>&lt; 1112 million cubic metres</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>0</ogc:Literal>
              </ogc:PropertyIsGreaterThanOrEqualTo>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>1112</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#ffe9b1</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.1</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name> 1112 - 4794 million cubic metres</sld:Name>
          <sld:Title> 1112 - 4794 million cubic metres</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>1112</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>4794</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#eaad57</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.1</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name> 4794 - 12096 million cubic metres</sld:Name>
          <sld:Title> 4794 - 12096 million cubic metres</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>4794</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>12096</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#ff7f1d</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.1</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name> 12096 - 28937 million cubic metres</sld:Name>
          <sld:Title> 12096 - 28937 million cubic metres</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>12096</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>28937</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#af8a33</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.1</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>&gt; 28937 million cubic metres</sld:Name>
          <sld:Title>&gt; 28937 million cubic metres</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>28937</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>106910</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#5b4b2d</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
              <sld:CssParameter name="stroke-width">0.1</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
        <sld:Rule>
          <sld:Name>No data for 2007</sld:Name>
          <sld:Title>No data for 2007</sld:Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>-99</ogc:Literal>
              </ogc:PropertyIsGreaterThan>
              <ogc:PropertyIsLessThanOrEqualTo>
                <ogc:PropertyName>y2007</ogc:PropertyName>
                <ogc:Literal>0</ogc:Literal>
              </ogc:PropertyIsLessThanOrEqualTo>
            </ogc:And>
          </ogc:Filter>
          <sld:PolygonSymbolizer>
            <sld:Fill>
              <sld:CssParameter name="fill">#d9d9d9</sld:CssParameter>
            </sld:Fill>
            <sld:Stroke>
              <sld:CssParameter name="stroke">#000001</sld:CssParameter>
            </sld:Stroke>
          </sld:PolygonSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
"""

raster_sld = """<?xml version="1.0" ?>
<sld:StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld"
xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc"
xmlns:sld="http://www.opengis.net/sld">
    <sld:UserLayer>
        <sld:LayerFeatureConstraints>
            <sld:FeatureTypeConstraint/>
        </sld:LayerFeatureConstraints>
        <sld:UserStyle>
            <sld:Name>geonode-geonode_gwpollriskafriotest</sld:Name>
            <sld:Title/>
            <sld:FeatureTypeStyle>
                <sld:Name/>
                <sld:Rule>
                    <sld:RasterSymbolizer>
                        <sld:Geometry>
                            <ogc:PropertyName>grid</ogc:PropertyName>
                        </sld:Geometry>
                        <sld:Opacity>1</sld:Opacity>
                        <sld:ColorMap>
                            <sld:ColorMapEntry color="#000000" opacity="1.0" quantity="77"/>
                            <sld:ColorMapEntry color="#FFFFFF" opacity="1.0" quantity="214"/>
                        </sld:ColorMap>
                    </sld:RasterSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:UserLayer>
</sld:StyledLayerDescriptor>
"""

line_sld = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  version="1.1.0" xmlns:se="http://www.opengis.net/se">
  <NamedLayer>
    <se:Name>line_3</se:Name>
    <UserStyle>
      <se:Name>line 3</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name>Single symbol</se:Name>
          <se:LineSymbolizer>
            <se:Stroke>
              <se:SvgParameter name="stroke">#db1e2a</se:SvgParameter>
              <se:SvgParameter name="stroke-width">2</se:SvgParameter>
              <se:SvgParameter name="stroke-linejoin">round</se:SvgParameter>
              <se:SvgParameter name="stroke-linecap">round</se:SvgParameter>
              <se:SvgParameter name="stroke-dasharray">2 7</se:SvgParameter>
            </se:Stroke>
          </se:LineSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""

SLDS = {
    'san_andres_y_providencia': san_andres_y_providencia_sld,
    'lac': lac_sld,
    'freshgwabs2': freshgwabs2_sld,
    'raster': raster_sld,
    'line': line_sld
}


class LayerTests(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super(LayerTests, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()
        self.config = Configuration.load()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_manager(self):
        """
        Ensures the layer_style_manage route returns a 200.
        """
        layer = Layer.objects.all()[0]

        bob = get_user_model().objects.get(username='bobby')
        assign_perm('change_layer_style', bob, layer)

        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEqual(logged_in, True)
        response = self.client.get(
            reverse(
                'layer_style_manage', args=(
                    layer.alternate,)))
        self.assertEqual(response.status_code, 200)

        form_data = {'default_style': 'polygon'}
        response = self.client.post(
            reverse(
                'layer_style_manage', args=(
                    layer.alternate,)), data=form_data)
        self.assertEqual(response.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_validity_and_name(self):
        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            files = (
                "san_andres_y_providencia.sld",
                "lac.sld",
                "freshgwabs2.sld",
                "raster.sld",
                "line.sld",
            )

            for f in files:
                path = os.path.join(d, f)
                with open(path, 'w') as f:
                    name, ext = splitext(basename(path))
                    f.write(SLDS[name])

            # Test 'san_andres_y_providencia.sld'
            san_andres_y_providencia_sld_file = os.path.join(
                d, "san_andres_y_providencia.sld")
            with open(san_andres_y_providencia_sld_file) as san_andres_y_providencia_sld_xml_file:
                san_andres_y_providencia_sld_xml = san_andres_y_providencia_sld_xml_file.read()
            san_andres_y_providencia_sld_name = extract_name_from_sld(
                None, san_andres_y_providencia_sld_xml)
            self.assertEqual(
                san_andres_y_providencia_sld_name,
                'san_andres_y_providencia_administrative')

            # Test 'lac.sld'
            lac_sld_file = os.path.join(d, "lac.sld")
            with open(lac_sld_file) as lac_sld_xml_file:
                lac_sld_xml = lac_sld_xml_file.read()
            lac_sld_name = extract_name_from_sld(
                None, lac_sld_xml, sld_file=lac_sld_file)
            self.assertEqual(lac_sld_name, 'LAC NonIndigenous Access to Sanitation')

            # Test 'freshgwabs2.sld'
            freshgwabs2_sld_file = os.path.join(d, "freshgwabs2.sld")
            with open(freshgwabs2_sld_file) as freshgwabs2_sld_xml_file:
                freshgwabs2_sld_xml = freshgwabs2_sld_xml_file.read()
            freshgwabs2_sld_name = extract_name_from_sld(
                None, freshgwabs2_sld_xml, sld_file=freshgwabs2_sld_file)
            self.assertEqual(freshgwabs2_sld_name, 'freshgwabs2')

            # Test 'raster.sld'
            raster_sld_file = os.path.join(d, "raster.sld")
            with open(raster_sld_file) as raster_sld_xml_file:
                raster_sld_xml = raster_sld_xml_file.read()
            raster_sld_name = extract_name_from_sld(
                None, raster_sld_xml, sld_file=raster_sld_file)
            self.assertEqual(
                raster_sld_name,
                'geonode-geonode_gwpollriskafriotest')

            # Test 'line.sld'
            line_sld_file = os.path.join(d, "line.sld")
            with open(line_sld_file) as line_sld_xml_file:
                line_sld_xml = line_sld_xml_file.read()
            line_sld_name = extract_name_from_sld(
                None, line_sld_xml, sld_file=line_sld_file)
            self.assertEqual(line_sld_name, 'line 3')
        finally:
            if d is not None:
                shutil.rmtree(d)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_feature_edit_check(self):
        """Verify that the feature_edit_check view is behaving as expected
        """

        # Setup some layer names to work with
        layer = Layer.objects.first()
        valid_layer_typename = layer.alternate
        layer.set_default_permissions()
        invalid_layer_typename = "n0ch@nc3"

        # Test that an invalid layer.typename is handled for properly
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    invalid_layer_typename,
                )))
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], False)

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], False)

        # Next Test with a user that has the proper perms (is owner)
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        # This will only be true for storeType dataStore
        if layer.storeType == 'dataStore':
            self.assertEqual(response_json['authorized'], True)
        else:
            self.assertEqual(response_json['authorized'], False)

        # Let's change layer permissions and try again with non-owner
        norman = get_user_model().objects.get(username='norman')
        remove_perm('change_layer_data', norman, layer)
        assign_perm('change_layer_style', norman, layer)
        perms = layer.get_all_level_info()
        self.assertIn('change_layer_style', perms['users'][norman])
        self.assertNotIn('change_layer_data', perms['users'][norman])

        logged_in = self.client.login(username='norman', password='norman')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], False)

        response = self.client.post(
            reverse(
                'style_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], True)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        # This will only be true for storeType dataStore
        if layer.storeType == 'dataStore':
            self.assertEqual(response_json['authorized'], True)
        else:
            self.assertEqual(response_json['authorized'], False)

        layer = Layer.objects.all()[0]
        layer.storeType = "dataStore"
        layer.save()

        # Test that the method returns authorized=True if it's a datastore
        if settings.OGC_SERVER['default']['DATASTORE']:
            # The check was moved from the template into the view
            response = self.client.post(
                reverse(
                    'feature_edit_check',
                    args=(
                        layer.alternate,
                    )))
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            response_json = json.loads(content)
            self.assertEqual(response_json['authorized'], True)

        # Test when the system is in readonly mode
        self.config.read_only = True
        self.config.save()
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], False)

        response = self.client.post(
            reverse(
                'style_edit_check',
                args=(
                    valid_layer_typename,
                )))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual(response_json['authorized'], False)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_acls(self):
        """ Verify that the layer_acls view is behaving as expected
        """

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = b"bobby:bob"
        invalid_uname_pw = b"n0t:v@l1d"

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': f"basic {base64.b64encode(valid_uname_pw).decode()}",
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': f"basic {base64.b64encode(invalid_uname_pw).decode()}",
        }

        bob = get_user_model().objects.get(username='bobby')
        layer_ca = Layer.objects.get(alternate='geonode:CA')
        assign_perm('change_layer_data', bob, layer_ca)

        # Test that requesting when supplying the geoserver credentials returns
        # the expected json

        expected_result = {
            'email': 'bobby@bob.com',
            'fullname': 'bobby',
            'is_anonymous': False,
            'is_superuser': False,
            'name': 'bobby',
            'ro': ['geonode:layer2',
                     'geonode:mylayer',
                     'geonode:foo',
                     'geonode:whatever',
                     'geonode:fooey',
                     'geonode:quux',
                     'geonode:fleem'],
            'rw': ['geonode:CA']
        }
        response = self.client.get(reverse('layer_acls'), **valid_auth_headers)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        # 'ro' and 'rw' are unsorted collections
        self.assertEqual(sorted(expected_result), sorted(response_json))

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(
            reverse('layer_acls'),
            **invalid_auth_headers)
        self.assertEqual(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_acls'))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)

        self.assertEqual('admin', response_json['fullname'])
        self.assertEqual('ad@m.in', response_json['email'])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_resolve_user(self):
        """Verify that the resolve_user view is behaving as expected
        """
        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = b"admin:admin"
        invalid_uname_pw = b"n0t:v@l1d"

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': f"basic {base64.b64encode(valid_uname_pw).decode()}",
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': f"basic {base64.b64encode(invalid_uname_pw).decode()}",
        }

        response = self.client.get(
            reverse('layer_resolve_user'),
            **valid_auth_headers)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        self.assertEqual({'geoserver': False,
                          'superuser': True,
                          'user': 'admin',
                          'fullname': 'admin',
                          'email': 'ad@m.in'}, response_json)

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(
            reverse('layer_acls'),
            **invalid_auth_headers)
        self.assertEqual(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_resolve_user'))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)

        self.assertEqual('admin', response_json['user'])
        self.assertEqual('admin', response_json['fullname'])
        self.assertEqual('ad@m.in', response_json['email'])


class UtilsTests(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super(UtilsTests, self).setUp()
        self.OGC_DEFAULT_SETTINGS = {
            'default': {
                'BACKEND': 'geonode.geoserver',
                'LOCATION': 'http://localhost:8080/geoserver/',
                'USER': 'admin',
                'PASSWORD': 'geoserver',
                'MAPFISH_PRINT_ENABLED': True,
                'PRINT_NG_ENABLED': True,
                'GEONODE_SECURITY_ENABLED': True,
                'GEOFENCE_SECURITY_ENABLED': True,
                'WMST_ENABLED': False,
                'BACKEND_WRITE_ENABLED': True,
                'WPS_ENABLED': False,
                'DATASTORE': str(),
            }
        }

        self.UPLOADER_DEFAULT_SETTINGS = {
            'BACKEND': 'geonode.rest',
            'OPTIONS': {
                'TIME_ENABLED': False,
                'MOSAIC_ENABLED': False}}

        self.DATABASE_DEFAULT_SETTINGS = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'development.db'}}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_ogc_server_settings(self):
        """
        Tests the OGC Servers Handler class.
        """

        with override_settings(OGC_SERVER=self.OGC_DEFAULT_SETTINGS, UPLOADER=self.UPLOADER_DEFAULT_SETTINGS):
            OGC_SERVER = self.OGC_DEFAULT_SETTINGS.copy()
            OGC_SERVER.update(
                {'PUBLIC_LOCATION': 'http://geoserver:8080/geoserver/'})

            ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']

            default = OGC_SERVER.get('default')
            self.assertEqual(ogc_settings.server, default)
            self.assertEqual(ogc_settings.BACKEND, default.get('BACKEND'))
            self.assertEqual(ogc_settings.LOCATION, default.get('LOCATION'))
            self.assertEqual(
                ogc_settings.PUBLIC_LOCATION,
                default.get('PUBLIC_LOCATION'))
            self.assertEqual(ogc_settings.USER, default.get('USER'))
            self.assertEqual(ogc_settings.PASSWORD, default.get('PASSWORD'))
            self.assertEqual(ogc_settings.DATASTORE, str())
            self.assertEqual(ogc_settings.credentials, ('admin', 'geoserver'))
            self.assertTrue(ogc_settings.MAPFISH_PRINT_ENABLED)
            self.assertTrue(ogc_settings.PRINT_NG_ENABLED)
            self.assertTrue(ogc_settings.GEONODE_SECURITY_ENABLED)
            self.assertFalse(ogc_settings.WMST_ENABLED)
            self.assertTrue(ogc_settings.BACKEND_WRITE_ENABLED)
            self.assertFalse(ogc_settings.WPS_ENABLED)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_ogc_server_defaults(self):
        """
        Tests that OGC_SERVER_SETTINGS are built if they do not exist in the settings.
        """
        from django.urls import reverse, resolve
        from ..ows import _wcs_get_capabilities, _wfs_get_capabilities, _wms_get_capabilities

        OGC_SERVER = {'default': dict()}

        defaults = self.OGC_DEFAULT_SETTINGS.get('default')
        ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
        self.assertEqual(ogc_settings.server, defaults)
        self.assertEqual(ogc_settings.rest, f"{defaults['LOCATION']}rest")
        self.assertEqual(ogc_settings.ows, f"{defaults['LOCATION']}ows")

        # Make sure we get None vs a KeyError when the key does not exist
        self.assertIsNone(ogc_settings.SFDSDFDSF)

        # Testing REST endpoints
        route = resolve('/gs/rest/layers').route
        self.assertEqual(route, '^gs/rest/layers')

        route = resolve('/gs/rest/imports').route
        self.assertEqual(route, '^gs/rest/imports')

        route = resolve('/gs/rest/sldservice').route
        self.assertEqual(route, '^gs/rest/sldservice')

        store_resolver = resolve('/gs/rest/stores/geonode_data/')
        self.assertEqual(store_resolver.url_name, 'stores')
        self.assertEqual(store_resolver.kwargs['store_type'], 'geonode_data')
        self.assertEqual(store_resolver.route, '^gs/rest/stores/(?P<store_type>\\w+)/$')

        sld_resolver = resolve('/gs/rest/styles')
        self.assertIsNone(sld_resolver.url_name)
        self.assertTrue('workspace' not in sld_resolver.kwargs)
        self.assertEqual(sld_resolver.kwargs['proxy_path'], '/gs/rest/styles')
        self.assertEqual(sld_resolver.kwargs['downstream_path'], 'rest/styles')
        self.assertEqual(sld_resolver.route, '^gs/rest/styles')

        sld_resolver = resolve('/gs/rest/workspaces/geonode/styles')
        self.assertIsNone(sld_resolver.url_name)
        self.assertEqual(sld_resolver.kwargs['workspace'], 'geonode')
        self.assertEqual(sld_resolver.kwargs['proxy_path'], '/gs/rest/workspaces')
        self.assertEqual(sld_resolver.kwargs['downstream_path'], 'rest/workspaces')
        self.assertEqual(sld_resolver.route, '^gs/rest/workspaces/(?P<workspace>\\w+)')

        # Testing OWS endpoints
        wcs = _wcs_get_capabilities()
        logger.debug(wcs)
        self.assertIsNotNone(wcs)

        try:
            wcs_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
        except Exception:
            wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')

        self.assertTrue(wcs.startswith(wcs_url))
        self.assertIn("service=WCS", wcs)
        self.assertIn("request=GetCapabilities", wcs)
        self.assertIn("version=2.0.1", wcs)

        wfs = _wfs_get_capabilities()
        logger.debug(wfs)
        self.assertIsNotNone(wfs)

        try:
            wfs_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
        except Exception:
            wfs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
        self.assertTrue(wfs.startswith(wfs_url))
        self.assertIn("service=WFS", wfs)
        self.assertIn("request=GetCapabilities", wfs)
        self.assertIn("version=1.1.0", wfs)

        wms = _wms_get_capabilities()
        logger.debug(wms)
        self.assertIsNotNone(wms)

        try:
            wms_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
        except Exception:
            wms_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
        self.assertTrue(wms.startswith(wms_url))
        self.assertIn("service=WMS", wms)
        self.assertIn("request=GetCapabilities", wms)
        self.assertIn("version=1.3.0", wms)

        # Test OWS Download Links
        from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
        instance = Layer.objects.all()[0]
        bbox = instance.bbox
        srid = instance.srid
        height = 512
        width = 512

        # Default Style (expect exception since we are offline)
        try:
            style = get_sld_for(gs_catalog, instance)
        except Exception:
            style = gs_catalog.get_style("line")
        self.assertIsNotNone(style)
        instance.default_style, _ = Style.objects.get_or_create(
            name=style.name,
            defaults=dict(
                sld_title=style.sld_title,
                sld_body=style.sld_body
            )
        )
        self.assertIsNotNone(instance.default_style)
        self.assertIsNotNone(instance.default_style.name)

        # WMS Links
        wms_links = wms_links(f"{ogc_settings.public_url}wms?",
                              instance.alternate,
                              bbox,
                              srid,
                              height,
                              width)
        self.assertIsNotNone(wms_links)
        self.assertEqual(len(wms_links), 3)
        wms_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'wms')
        identifier = urlencode({'layers': instance.alternate})
        for _link in wms_links:
            logger.debug(f'{wms_url} --> {_link[3]}')
            self.assertTrue(wms_url in _link[3])
            logger.debug(f'{identifier} --> {_link[3]}')
            self.assertTrue(identifier in _link[3])

        # WFS Links
        wfs_links = wfs_links(f"{ogc_settings.public_url}wfs?",
                              instance.alternate,
                              bbox,
                              srid)
        self.assertIsNotNone(wfs_links)
        self.assertEqual(len(wfs_links), 6)
        wfs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'wfs')
        identifier = urlencode({'typename': instance.alternate})
        for _link in wfs_links:
            logger.debug(f'{wfs_url} --> {_link[3]}')
            self.assertTrue(wfs_url in _link[3])
            logger.debug(f'{identifier} --> {_link[3]}')
            self.assertTrue(identifier in _link[3])

        # WCS Links
        wcs_links = wcs_links(f"{ogc_settings.public_url}wcs?",
                              instance.alternate,
                              bbox,
                              srid)
        self.assertIsNotNone(wcs_links)
        self.assertEqual(len(wcs_links), 2)
        wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'wcs')
        identifier = urlencode({'coverageid': instance.alternate.replace(':', '__', 1)})
        for _link in wcs_links:
            logger.debug(f'{wcs_url} --> {_link[3]}')
            self.assertTrue(wcs_url in _link[3])
            logger.debug(f'{identifier} --> {_link[3]}')
            self.assertTrue(identifier in _link[3])

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_importer_configuration(self):
        database_settings = self.DATABASE_DEFAULT_SETTINGS.copy()
        ogc_server_settings = self.OGC_DEFAULT_SETTINGS.copy()
        uploader_settings = self.UPLOADER_DEFAULT_SETTINGS.copy()

        uploader_settings['BACKEND'] = 'geonode.importer'
        self.assertTrue(['geonode_imports' not in database_settings.keys()])

        # Test the importer backend without specifying a datastore or
        # corresponding database.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']

        ogc_server_settings['default']['DATASTORE'] = 'geonode_imports'

        # Test the importer backend with a datastore but no corresponding
        # database.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']

        database_settings['geonode_imports'] = database_settings[
            'default'].copy()
        database_settings['geonode_imports'].update(
            {'NAME': 'geonode_imports'})

        # Test the importer backend with a datastore and a corresponding
        # database, no exceptions should be thrown.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']


class SignalsTests(GeoNodeBaseTestSupport):

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_set_resources_links(self):

        from django.db.models import Q
        from geonode.base.models import Link
        from geonode.catalogue import get_catalogue

        with self.settings(UPDATE_RESOURCE_LINKS_AT_MIGRATE=True, ASYNC_SIGNALS=False):
            # Links
            _def_link_types = ['original', 'metadata']
            _links = Link.objects.filter(link_type__in=_def_link_types)
            # Check 'original' and 'metadata' links exist
            self.assertIsNotNone(
                _links,
                "No 'original' and 'metadata' links have been found"
            )

            # Delete all 'original' and 'metadata' links
            _links.delete()
            self.assertFalse(_links.count() > 0, "No links have been deleted")
            # Delete resources metadata
            _layers = Layer.objects.exclude(
                Q(metadata_xml__isnull=True) |
                Q(metadata_xml__exact='') |
                Q(csw_anytext__isnull=True) |
                Q(csw_anytext__exact='')
            )
            count = _layers.count()
            if count:
                _layers.update(metadata_xml=None)
                _updated_layers = Layer.objects.exclude(
                    Q(metadata_xml__isnull=True) |
                    Q(metadata_xml__exact='') |
                    Q(csw_anytext__isnull=True) |
                    Q(csw_anytext__exact='')
                )
                updated_count = _updated_layers.count()
                self.assertTrue(
                    updated_count == 0,
                    "Metadata have not been updated (deleted) correctly"
                )

            # Call migrate
            call_command("migrate", verbosity=0)
            # Check links
            _post_migrate_links = Link.objects.filter(link_type__in=_def_link_types)
            self.assertTrue(
                _post_migrate_links.count() > 0,
                "No links have been restored"
            )
            # Check layers
            _post_migrate_layers = Layer.objects.exclude(
                Q(metadata_xml__isnull=True) |
                Q(metadata_xml__exact='') |
                Q(csw_anytext__isnull=True) |
                Q(csw_anytext__exact='')
            )

            for _lyr in _post_migrate_layers:
                # Check original links in csw_anytext
                _post_migrate_links_orig = Link.objects.filter(
                    resource=_lyr.resourcebase_ptr,
                    resource_id=_lyr.resourcebase_ptr.id,
                    link_type='original'
                )
                self.assertTrue(
                    _post_migrate_links_orig.count() > 0,
                    f"No 'original' links has been found for the layer '{_lyr.alternate}'"
                )
                for _link_orig in _post_migrate_links_orig:
                    self.assertIn(
                        _link_orig.url,
                        _lyr.csw_anytext,
                        f"The link URL {_link_orig.url} is not present in the 'csw_anytext' attribute of the layer '{_lyr.alternate}'")
                # Check catalogue
                catalogue = get_catalogue()
                record = catalogue.get_record(_lyr.uuid)
                self.assertIsNotNone(record)
                self.assertTrue(
                    hasattr(record, 'links'),
                    f"No records have been found in the catalogue for the resource '{_lyr.alternate}'"
                )
                # Check 'metadata' links for each record
                for mime, name, metadata_url in record.links['metadata']:
                    try:
                        _post_migrate_link_meta = Link.objects.get(
                            resource=_lyr.resourcebase_ptr,
                            url=metadata_url,
                            name=name,
                            extension='xml',
                            mime=mime,
                            link_type='metadata'
                        )
                    except Link.DoesNotExist:
                        _post_migrate_link_meta = None
                    self.assertIsNotNone(
                        _post_migrate_link_meta,
                        f"No '{name}' links have been found in the catalogue for the resource '{_lyr.alternate}'"
                    )
