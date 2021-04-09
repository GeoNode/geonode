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

from django.test.testcases import SimpleTestCase
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


class TestHandleMetadataKeyword(SimpleTestCase):
    def setUp(self):
        self.raw_keyword = {
            "raw_keyword": [
                {
                    "keywords": ["features", "test_layer"],
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
        }
        self.extracted_keyword = ["features", "test_layer"]
        self.sut = utils.KeywordHandler(
            instance='', 
            extracted_keyword=self.extracted_keyword,
            raw_keyword=self.raw_keyword
        )

    def test_return_extracted_keyword_if_custom_is_an_empty_dict(self):
        setattr(self.sut, 'raw_keyword', {})
        keyword, thesaurus_keyword = self.sut.handle_metadata_keywords()
        self.assertListEqual(self.extracted_keyword, keyword)
        self.assertListEqual([], thesaurus_keyword)

    def test_should_return_the_expected_keyword_extracted_from_raw_and_the_thesaurus_keyword(self):
        keyword, thesaurus_keyword = self.sut.handle_metadata_keywords()
        self.assertListEqual(["features", "test_layer"], keyword)
        self.assertListEqual(["no conditions to access and use", "ad", "af"], thesaurus_keyword)
