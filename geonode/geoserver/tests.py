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

import base64
import json
import os
import shutil
import tempfile
from os.path import basename, splitext

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from guardian.shortcuts import assign_perm, get_anonymous_user

from geonode.geoserver.helpers import OGC_Servers_Handler, extract_name_from_sld
from geonode.base.populate_test_data import create_models
from geonode.layers.populate_layers_data import create_layer_data
from geonode.layers.models import Layer

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


class LayerTests(TestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()

    def test_style_manager(self):
        """
        Ensures the layer_style_manage route returns a 200.
        """
        layer = Layer.objects.all()[0]

        bob = get_user_model().objects.get(username='bobby')
        assign_perm('change_layer_style', bob, layer)

        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.get(reverse('layer_style_manage', args=(layer.alternate,)))
        self.assertEqual(response.status_code, 200)

    def test_style_validity_and_name(self):
        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("san_andres_y_providencia.sld",
                      "lac.sld",
                      "freshgwabs2.sld",
                      "raster.sld",
                      "line.sld",):
                path = os.path.join(d, f)
                f = open(path, "wb")
                f.write(SLDS[splitext(basename(path))[0]])
                f.close()

            # Test 'san_andres_y_providencia.sld'
            san_andres_y_providencia_sld_file = os.path.join(d, "san_andres_y_providencia.sld")
            san_andres_y_providencia_sld_xml = open(san_andres_y_providencia_sld_file).read()
            san_andres_y_providencia_sld_name = extract_name_from_sld(None, san_andres_y_providencia_sld_xml)
            self.assertEquals(san_andres_y_providencia_sld_name, 'san_andres_y_providencia_administrative')

            # Test 'lac.sld'
            lac_sld_file = os.path.join(d, "lac.sld")
            lac_sld_xml = open(lac_sld_file).read()
            lac_sld_name = extract_name_from_sld(None, lac_sld_xml, sld_file=lac_sld_file)
            self.assertEquals(lac_sld_name, 'LAC NonIndigenous Access to Sanitation')

            # Test 'freshgwabs2.sld'
            freshgwabs2_sld_file = os.path.join(d, "freshgwabs2.sld")
            freshgwabs2_sld_xml = open(freshgwabs2_sld_file).read()
            freshgwabs2_sld_name = extract_name_from_sld(None, freshgwabs2_sld_xml, sld_file=freshgwabs2_sld_file)
            self.assertEquals(freshgwabs2_sld_name, 'freshgwabs2')

            # Test 'raster.sld'
            raster_sld_file = os.path.join(d, "raster.sld")
            raster_sld_xml = open(raster_sld_file).read()
            raster_sld_name = extract_name_from_sld(None, raster_sld_xml, sld_file=raster_sld_file)
            self.assertEquals(raster_sld_name, 'geonode-geonode_gwpollriskafriotest')

            # Test 'line.sld'
            line_sld_file = os.path.join(d, "line.sld")
            line_sld_xml = open(line_sld_file).read()
            line_sld_name = extract_name_from_sld(None, line_sld_xml, sld_file=line_sld_file)
            self.assertEquals(line_sld_name, 'line 3')
        finally:
            if d is not None:
                shutil.rmtree(d)

    def test_feature_edit_check(self):
        """Verify that the feature_edit_check view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].alternate
        Layer.objects.all()[0].set_default_permissions()
        invalid_layer_typename = "n0ch@nc3"

        # Test that an invalid layer.typename is handled for properly
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    invalid_layer_typename,
                )))
        self.assertEquals(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))

        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], True)

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
                        valid_layer_typename,
                    )))
            response_json = json.loads(response.content)
            self.assertEquals(response_json['authorized'], True)

    def test_layer_acls(self):
        """ Verify that the layer_acls view is behaving as expected
        """

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = '%s:%s' % ('bobby', 'bob')
        invalid_uname_pw = '%s:%s' % ('n0t', 'v@l1d')

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' +
            base64.b64encode(invalid_uname_pw),
        }

        bob = get_user_model().objects.get(username='bobby')
        layer_ca = Layer.objects.get(alternate='geonode:CA')
        assign_perm('change_layer_data', bob, layer_ca)

        # Test that requesting when supplying the geoserver credentials returns
        # the expected json

        expected_result = {
            u'email': u'bobby@bob.com',
            u'fullname': u'bobby',
            u'is_anonymous': False,
            u'is_superuser': False,
            u'name': u'bobby',
            u'ro': [u'geonode:layer2',
                     u'geonode:mylayer',
                     u'geonode:foo',
                     u'geonode:whatever',
                     u'geonode:fooey',
                     u'geonode:quux',
                     u'geonode:fleem'],
            u'rw': [u'geonode:CA']
        }
        response = self.client.get(reverse('layer_acls'), **valid_auth_headers)
        response_json = json.loads(response.content)
        # 'ro' and 'rw' are unsorted collections
        self.assertEquals(sorted(expected_result), sorted(response_json))

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(reverse('layer_acls'), **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_acls'))
        response_json = json.loads(response.content)

        self.assertEquals('admin', response_json['fullname'])
        self.assertEquals('', response_json['email'])

        # TODO Lots more to do here once jj0hns0n understands the ACL system
        # better

    def test_resolve_user(self):
        """Verify that the resolve_user view is behaving as expected
        """
        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = "%s:%s" % ('admin', 'admin')
        invalid_uname_pw = "%s:%s" % ("n0t", "v@l1d")

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' +
            base64.b64encode(invalid_uname_pw),
        }

        response = self.client.get(reverse('layer_resolve_user'), **valid_auth_headers)
        response_json = json.loads(response.content)
        self.assertEquals({'geoserver': False,
                           'superuser': True,
                           'user': 'admin',
                           'fullname': 'admin',
                           'email': ''},
                          response_json)

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(reverse('layer_acls'), **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_resolve_user'))
        response_json = json.loads(response.content)

        self.assertEquals('admin', response_json['user'])
        self.assertEquals('admin', response_json['fullname'])
        self.assertEquals('', response_json['email'])


class UtilsTests(TestCase):

    def setUp(self):
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
                'GEOGIG_ENABLED': False,
                'WMST_ENABLED': False,
                'BACKEND_WRITE_ENABLED': True,
                'WPS_ENABLED': False,
                'DATASTORE': str(),
                'GEOGIG_DATASTORE_DIR': str(),
            }
        }

        self.UPLOADER_DEFAULT_SETTINGS = {
            'BACKEND': 'geonode.rest',
            'OPTIONS': {
                'TIME_ENABLED': False,
                'MOSAIC_ENABLED': False,
                'GEOGIG_ENABLED': False}}

        self.DATABASE_DEFAULT_SETTINGS = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'development.db'}}

    def test_ogc_server_settings(self):
        """
        Tests the OGC Servers Handler class.
        """

        with override_settings(OGC_SERVER=self.OGC_DEFAULT_SETTINGS, UPLOADER=self.UPLOADER_DEFAULT_SETTINGS):
            OGC_SERVER = self.OGC_DEFAULT_SETTINGS.copy()
            OGC_SERVER.update(
                {'PUBLIC_LOCATION': 'http://localhost:8080/geoserver/'})

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
            self.assertFalse(ogc_settings.GEOGIG_ENABLED)
            self.assertFalse(ogc_settings.WMST_ENABLED)
            self.assertTrue(ogc_settings.BACKEND_WRITE_ENABLED)
            self.assertFalse(ogc_settings.WPS_ENABLED)

    def test_ogc_server_defaults(self):
        """
        Tests that OGC_SERVER_SETTINGS are built if they do not exist in the settings.
        """

        OGC_SERVER = {'default': dict()}

        defaults = self.OGC_DEFAULT_SETTINGS.get('default')
        ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
        self.assertEqual(ogc_settings.server, defaults)
        self.assertEqual(ogc_settings.rest, defaults['LOCATION'] + 'rest')
        self.assertEqual(ogc_settings.ows, defaults['LOCATION'] + 'ows')

        # Make sure we get None vs a KeyError when the key does not exist
        self.assertIsNone(ogc_settings.SFDSDFDSF)

    def test_importer_configuration(self):
        """
        Tests that the OGC_Servers_Handler throws an ImproperlyConfigured exception when using the importer
        backend without a vector database and a datastore configured.
        """
        database_settings = self.DATABASE_DEFAULT_SETTINGS.copy()
        ogc_server_settings = self.OGC_DEFAULT_SETTINGS.copy()
        uploader_settings = self.UPLOADER_DEFAULT_SETTINGS.copy()

        uploader_settings['BACKEND'] = 'geonode.importer'
        self.assertTrue(['geonode_imports' not in database_settings.keys()])

        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):

            # Test the importer backend without specifying a datastore or
            # corresponding database.
            with self.assertRaises(ImproperlyConfigured):
                OGC_Servers_Handler(ogc_server_settings)['default']

        ogc_server_settings['default']['DATASTORE'] = 'geonode_imports'

        # Test the importer backend with a datastore but no corresponding
        # database.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            with self.assertRaises(ImproperlyConfigured):
                OGC_Servers_Handler(ogc_server_settings)['default']

        database_settings['geonode_imports'] = database_settings[
            'default'].copy()
        database_settings['geonode_imports'].update(
            {'NAME': 'geonode_imports'})

        # Test the importer backend with a datastore and a corresponding
        # database, no exceptions should be thrown.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']


class SecurityTest(TestCase):

    """
    Tests for the Geonode security app.
    """

    def setUp(self):
        self.admin, created = get_user_model().objects.get_or_create(
            username='admin', password='admin', is_superuser=True)

    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware()

        white_list = [
            reverse('account_ajax_login'),
            reverse('account_confirm_email', kwargs=dict(key='test')),
            reverse('account_login'),
            reverse('account_password_reset'),
            reverse('forgot_username'),
            reverse('layer_acls'),
            reverse('layer_resolve_user'),
        ]

        black_list = [
            reverse('account_signup'),
            reverse('document_browse'),
            reverse('maps_browse'),
            reverse('layer_browse'),
            reverse('layer_detail', kwargs=dict(layername='geonode:Test')),
            reverse('layer_remove', kwargs=dict(layername='geonode:Test')),
            reverse('profile_browse'),
        ]

        request = HttpRequest()
        request.user = get_anonymous_user()

        # Requests should be redirected to the the `redirected_to` path when un-authenticated user attempts to visit
        # a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
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
                msg="Middleware activated for white listed path: {0}".format(path))

        self.client.login(username='admin', password='admin')
        self.assertTrue(self.admin.is_authenticated())
        request.user = self.admin

        # The middleware should return None when an authenticated user attempts
        # to visit a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response)
