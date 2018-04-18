# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

"""unit tests for geonode.upload.utils module"""

from geonode.tests.base import GeoNodeBaseTestSupport

from lxml import etree

from geonode.upload import utils


class UtilsTestCase(GeoNodeBaseTestSupport):

    def test_pages(self):
        self.assertIn("kml-overlay", utils._pages)

    def test_get_kml_doc(self):
        kml_bytes = """
            <?xml version="1.0" encoding="UTF-8"?>
            <kml xmlns="http://earth.google.com/kml/2.1">
            <Document>
              <name>CSR5r3_annual</name>
              <GroundOverlay id="groundoverlay">
                <name>CSR5r3_annual</name>
                <description><![CDATA[]]></description>
                <color>ffffffff</color>
                <visibility>1</visibility>
                <extrude>0</extrude>
                <Icon>
                  <href>CSR5r3_annual.png</href>
                  <viewBoundScale>1</viewBoundScale>
                </Icon>
                <LatLonBox>
                  <north>70.000000</north>
                  <south>-60.500000</south>
                  <east>180.000000</east>
                  <west>-180.000000</west>
                  <rotation>0.0000000000000000</rotation>
                </LatLonBox>
              </GroundOverlay>
            </Document>
            </kml>
        """.strip()
        kml_doc, ns = utils.get_kml_doc(kml_bytes)
        self.assertTrue(etree.QName(kml_doc.tag).localname, "kml")
        self.assertIn("kml", ns.keys())
