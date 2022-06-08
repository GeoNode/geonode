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

from os.path import basename, splitext
from urllib.parse import urljoin, urlencode, urlsplit

from django.conf import settings
from django.urls import reverse
from django.test.client import RequestFactory
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from guardian.shortcuts import assign_perm

from geonode.geoserver.helpers import ogc_server_settings
from geonode.geoserver.views import check_geoserver_access, style_change_check

from geonode import geoserver
from geonode.base.models import Configuration
from geonode.decorators import on_ogc_backend

from geonode.utils import mkdtemp, OGC_Servers_Handler
from geonode.layers.models import Dataset, Style
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models,
    create_single_dataset)
from geonode.geoserver.helpers import (
    gs_catalog,
    get_sld_for,
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
        self.config = Configuration.load()

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
                'DATASTORE': '',
            }
        }

        self.UPLOADER_DEFAULT_SETTINGS = {
            'BACKEND': 'geonode.importer',
            'OPTIONS': {
                'TIME_ENABLED': False,
                'MOSAIC_ENABLED': False}}

        self.DATABASE_DEFAULT_SETTINGS = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'development.db'}}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_manager(self):
        """
        Ensures the dataset_style_manage route returns a 200.
        """
        layer = Dataset.objects.first()

        bob = get_user_model().objects.get(username='bobby')
        assign_perm('change_dataset_style', bob, layer)

        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(
            reverse(
                'dataset_style_manage', args=(
                    layer.alternate,)))
        self.assertEqual(response.status_code, 200)

        form_data = {'default_style': 'polygon'}
        response = self.client.post(
            reverse(
                'dataset_style_manage', args=(
                    layer.alternate,)), data=form_data)
        self.assertEqual(response.status_code, 302)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_validity_and_name(self):
        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        d = None
        try:
            d = mkdtemp()
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
                shutil.rmtree(d, ignore_errors=True)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_change_on_basic_auth(self):
        """
        Ensures we are able to update the style through a BASIC auth call only.
        """
        layer = Dataset.objects.filter(default_style__isnull=False).first()

        bob = get_user_model().objects.get(username='bobby')
        assign_perm('change_dataset_style', bob, layer)

        self.assertTrue(bob.has_perm('change_dataset_style', obj=layer))

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = b"bobby:bob"
        invalid_uname_pw = b"n0t:v@l1d"

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': f"BASIC {base64.b64encode(valid_uname_pw).decode()}",
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': f"BASIC {base64.b64encode(invalid_uname_pw).decode()}",
        }

        change_style_url = urljoin(
            settings.SITEURL,
            f"/gs/rest/workspaces/{settings.DEFAULT_WORKSPACE}/styles/{layer.name}?raw=true")
        logger.debug(f"{change_style_url}")

        rf = RequestFactory()

        # Check is 'authorized'
        post_request = rf.post(
            change_style_url,
            data=san_andres_y_providencia_sld,
            content_type='application/vnd.ogc.sld+xml',
            **valid_auth_headers
        )
        post_request.user = AnonymousUser()
        raw_url, headers, access_token, downstream_path = check_geoserver_access(
            post_request,
            '/gs/rest/workspaces',
            'rest/workspaces',
            workspace='geonode',
            layername=layer.name,
            allowed_hosts=[urlsplit(ogc_server_settings.public_url).hostname, ])
        self.assertIsNotNone(raw_url)
        self.assertIsNotNone(headers)
        self.assertIsNotNone(access_token)

        authorized = style_change_check(post_request, downstream_path, style_name='styles', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(post_request, 'rest/styles', style_name=f'{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(post_request, f'rest/workspaces/{layer.workspace}/styles/{layer.name}', style_name=f'{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(post_request, f'rest/layers/{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(post_request, f'rest/workspaces/{layer.workspace}/layers/{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        put_request = rf.put(
            change_style_url,
            data=san_andres_y_providencia_sld,
            content_type='application/vnd.ogc.sld+xml',
            **valid_auth_headers
        )
        put_request.user = AnonymousUser()
        raw_url, headers, access_token, downstream_path = check_geoserver_access(
            put_request,
            '/gs/rest/workspaces',
            'rest/workspaces',
            workspace='geonode',
            layername=layer.name,
            allowed_hosts=[urlsplit(ogc_server_settings.public_url).hostname, ])
        self.assertIsNotNone(raw_url)
        self.assertIsNotNone(headers)
        self.assertIsNotNone(access_token)

        # Check that, if we have been authorized through the "access_token",
        # we can still update a style no more present on GeoNode
        # ref: 05b000cdb06b0b6e9b72bd9eb8a8e03abeb204a8
        #  [Regression] "style_change_check" always fails in the case the style does not exist on GeoNode too, preventing a user editing temporary generated styles
        Style.objects.filter(name=layer.name).delete()

        authorized = style_change_check(put_request, downstream_path, style_name='styles', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(put_request, 'rest/styles', style_name=f'{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(put_request, f'rest/workspaces/{layer.workspace}/styles/{layer.name}', style_name=f'{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(put_request, f'rest/layers/{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        authorized = style_change_check(put_request, f'rest/workspaces/{layer.workspace}/layers/{layer.name}', access_token=access_token)
        self.assertTrue(authorized)

        # Check is NOT 'authorized'
        post_request = rf.post(
            change_style_url,
            data=san_andres_y_providencia_sld,
            content_type='application/vnd.ogc.sld+xml',
            **invalid_auth_headers
        )
        post_request.user = AnonymousUser()
        raw_url, headers, access_token, downstream_path = check_geoserver_access(
            post_request,
            '/gs/rest/workspaces',
            'rest/workspaces',
            workspace='geonode',
            layername=layer.name,
            allowed_hosts=[urlsplit(ogc_server_settings.public_url).hostname, ])
        self.assertIsNotNone(raw_url)
        self.assertIsNotNone(headers)
        self.assertIsNone(access_token)

        authorized = style_change_check(post_request, downstream_path, access_token=access_token)
        self.assertFalse(authorized)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_dataset_acls(self):
        """ Verify that the dataset_acls view is behaving as expected
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
        dataset_ca = Dataset.objects.get(alternate='geonode:CA')
        assign_perm('change_dataset_data', bob, dataset_ca)

        # Test that requesting when supplying the geoserver credentials returns
        # the expected json

        expected_result = {
            'email': 'bobby@bob.com',
            'fullname': 'bobby',
            'is_anonymous': False,
            'is_superuser': False,
            'name': 'bobby',
            'ro': [
                'geonode:layer2',
                'geonode:mylayer',
                'geonode:foo',
                'geonode:whatever',
                'geonode:fooey',
                'geonode:quux',
                'geonode:fleem'
            ],
            'rw': ['geonode:CA']
        }
        response = self.client.get(reverse('dataset_acls'), **valid_auth_headers)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)
        # 'ro' and 'rw' are unsorted collections
        self.assertEqual(sorted(expected_result), sorted(response_json))

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(
            reverse('dataset_acls'),
            **invalid_auth_headers)
        self.assertEqual(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('dataset_acls'))
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
            reverse('dataset_resolve_user'),
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
            reverse('dataset_acls'),
            **invalid_auth_headers)
        self.assertEqual(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('dataset_resolve_user'))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_json = json.loads(content)

        self.assertEqual('admin', response_json['user'])
        self.assertEqual('admin', response_json['fullname'])
        self.assertEqual('ad@m.in', response_json['email'])

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
            self.assertEqual(ogc_settings.DATASTORE, '')
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
        self.assertEqual(store_resolver.url_name, 'gs_stores')
        self.assertEqual(store_resolver.kwargs['store_type'], 'geonode_data')
        self.assertEqual(store_resolver.route, '^gs/rest/stores/(?P<store_type>\\w+)/$')

        sld_resolver = resolve('/gs/rest/styles')
        self.assertEqual(sld_resolver.url_name, 'gs_styles')
        self.assertTrue('workspace' not in sld_resolver.kwargs)
        self.assertEqual(sld_resolver.kwargs['proxy_path'], '/gs/rest/styles')
        self.assertEqual(sld_resolver.kwargs['downstream_path'], 'rest/styles')
        self.assertEqual(sld_resolver.route, '^gs/rest/styles')

        sld_resolver = resolve('/gs/rest/workspaces/geonode/styles')
        self.assertEqual(sld_resolver.url_name, 'gs_workspaces')
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
        instance = create_single_dataset("san_andres_y_providencia_water")
        instance.name = 'san_andres_y_providencia_water'
        instance.save()
        bbox = instance.bbox
        srid = instance.srid
        height = 512
        width = 512

        # Default Style (expect exception since we are offline)
        style = get_sld_for(gs_catalog, instance)
        if style and isinstance(style, str):
            style = gs_catalog.get_style(instance.name, workspace=instance.workspace)
            self.assertIsNotNone(style)
            self.assertFalse(isinstance(style, str))
        style_name = 'point'
        style_body = """
<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
 xmlns="http://www.opengis.net/sld"
 xmlns:ogc="http://www.opengis.net/ogc"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>default_point</Name>
    <UserStyle>
    <!-- Styles can have names, titles and abstracts -->
      <Title>Default Point</Title>
      <Abstract>A sample style that draws a point</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering points -->
      <FeatureTypeStyle>
        <Rule>
          <Name>rule1</Name>
          <Title>Red Square</Title>
          <Abstract>A 6 pixel square with a red fill and no stroke</Abstract>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>square</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">#FF0000</CssParameter>
                  </Fill>
                </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""
        instance.default_style, _ = Style.objects.get_or_create(
            name=style_name,
            defaults=dict(
                sld_title=style_name,
                sld_body=style_body
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
                              instance.alternate)
        self.assertIsNotNone(wcs_links)
        self.assertEqual(len(wcs_links), 1)
        wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'wcs')
        identifier = urlencode({'coverageid': instance.alternate.replace(':', '__', 1)})
        for _link in wcs_links:
            logger.debug(f'{wcs_url} --> {_link[3]}')
            self.assertTrue(wcs_url in _link[3])
            logger.debug(f'{identifier} --> {_link[3]}')
            self.assertTrue(identifier in _link[3])
            if srid:
                self.assertFalse('outputCrs' in _link[3])
            if bbox:
                self.assertFalse('subset=Long' in _link[3])
                self.assertFalse('subset=Lat' in _link[3])

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
            self.assertFalse(_links.exists(), "No links have been deleted")
            # Delete resources metadata
            _datasets = Dataset.objects.exclude(
                Q(metadata_xml__isnull=True) |
                Q(metadata_xml__exact='') |
                Q(csw_anytext__isnull=True) |
                Q(csw_anytext__exact='')
            )
            count = _datasets.count()
            if count:
                _datasets.update(metadata_xml=None)
                _updated_datasets = Dataset.objects.exclude(
                    Q(metadata_xml__isnull=True) |
                    Q(metadata_xml__exact='') |
                    Q(csw_anytext__isnull=True) |
                    Q(csw_anytext__exact='')
                )
                updated_count = _updated_datasets.count()
                self.assertTrue(
                    updated_count == 0,
                    "Metadata have not been updated (deleted) correctly"
                )

            # Call migrate
            call_command("migrate", verbosity=0)
            # Check links
            _post_migrate_links = Link.objects.filter(link_type__in=_def_link_types)
            self.assertTrue(
                _post_migrate_links.exists(),
                "No links have been restored"
            )
            # Check layers
            _post_migrate_datasets = Dataset.objects.exclude(
                Q(metadata_xml__isnull=True) |
                Q(metadata_xml__exact='') |
                Q(csw_anytext__isnull=True) |
                Q(csw_anytext__exact='')
            )

            for _lyr in _post_migrate_datasets:
                # Check original links in csw_anytext
                _post_migrate_links_orig = Link.objects.filter(
                    resource=_lyr.resourcebase_ptr,
                    resource_id=_lyr.resourcebase_ptr.id,
                    link_type='original'
                )
                self.assertTrue(
                    _post_migrate_links_orig.exists(),
                    f"No 'original' links has been found for the layer '{_lyr.alternate}'"
                )
                for _link_orig in _post_migrate_links_orig:
                    self.assertIn(
                        _link_orig.url,
                        _lyr.csw_anytext,
                        f"The link URL {_link_orig.url} is not present in the 'csw_anytext' attribute of the layer '{_lyr.alternate}'"
                    )
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

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_gs_proxy_never_caches(self):
        url = reverse('gs_styles')
        response = self.client.get(url)
        self.assertFalse(response.has_header('Cache-Control'))
