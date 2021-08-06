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


from django.test.utils import override_settings
from geonode.base.populate_test_data import create_single_layer
from django.test import TestCase
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


class TestHandleMetadataKeyword(TestCase):
    fixtures = [
        "test_thesaurus.json"
    ]

    def setUp(self):
        self.keyword = [
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
        self.layer = create_single_layer('keyword-handler')
        self.sut = utils.KeywordHandler(
            instance=self.layer,
            keywords=self.keyword
        )

    def test_return_empty_if_keywords_is_an_empty_list(self):
        setattr(self.sut, 'keywords', [])
        keyword, thesaurus_keyword = self.sut.handle_metadata_keywords()
        self.assertListEqual([], keyword)
        self.assertListEqual([], thesaurus_keyword)

    def test_should_return_the_expected_keyword_extracted_from_raw_and_the_thesaurus_keyword(self):
        keyword, thesaurus_keyword = self.sut.handle_metadata_keywords()
        self.assertSetEqual({"features", "test_layer", "no conditions to access and use"}, set(keyword))
        self.assertListEqual(["ad", "af"], [x.alt_label for x in thesaurus_keyword])

    def test_should_assign_correclty_the_keyword_to_the_layer_object(self):
        self.sut.set_keywords()
        current_keywords = [keyword.name for keyword in self.layer.keywords.all()]
        current_tkeyword = [t.alt_label for t in self.layer.tkeywords.all()]
        self.assertSetEqual({"features", "test_layer", "no conditions to access and use"}, set(current_keywords))
        self.assertSetEqual({"ad", "af"}, set(current_tkeyword))

    def test_is_thesaurus_available_should_return_queryset_with_existing_thesaurus(self):
        keyword = "ad"
        thesaurus = {"title": "GEMET - INSPIRE themes, version 1.0"}
        actual = self.sut.is_thesaurus_available(thesaurus, keyword)
        self.assertEqual(1, len(actual))

    def test_is_thesaurus_available_should_return_empty_queryset_for_non_existing_thesaurus(self):
        keyword = "ad"
        thesaurus = {"title": "Random Thesaurus Title"}
        actual = self.sut.is_thesaurus_available(thesaurus, keyword)
        self.assertEqual(0, len(actual))


'''
Smoke test to explain how the new function for multiple storer will work
Is required to define a fuction that takes 2 parametersand return 2 parameters.
            Parameters:
                    layer: (Layer): Layer instance
                    custom (dict): Custom dict generated by the parser

            Returns:
                    None
'''


class TestMetadataStorers(TestCase):
    def setUp(self):
        self.layer = create_single_layer('metadata-storer')
        self.uuid = self.layer.uuid
        self.abstract = self.layer.abstract
        self.custom = {
            "processes": {"uuid": "abc123cfde", "abstract": "updated abstract"},
            "second-stage": {"title": "Updated Title", "abstract": "another update"},
        }

    @override_settings(METADATA_STORERS=['geonode.upload.tests.test_utils.dummy_metadata_storer'])
    def test_will_use_single_storers_defined(self):
        utils.metadata_storers(self.layer, self.custom)
        self.assertEqual('abc123cfde', self.layer.uuid)
        self.assertEqual("updated abstract", self.layer.abstract)

    @override_settings(
        METADATA_STORERS=[
            "geonode.upload.tests.test_utils.dummy_metadata_storer",
            "geonode.upload.tests.test_utils.dummy_metadata_storer2",
        ]
    )
    def test_will_use_multiple_storers_defined(self):
        layer = utils.metadata_storers(self.layer, self.custom)
        self.assertEqual('abc123cfde', layer.uuid)
        self.assertEqual("another update", layer.abstract)
        self.assertEqual("Updated Title", layer.title)


'''
Just a dummy function required for the smoke test above
'''


def dummy_metadata_storer(layer, custom):
    if custom.get('processes', None):
        for key, value in custom['processes'].items():
            setattr(layer, key, value)


def dummy_metadata_storer2(layer, custom):
    if custom.get('second-stage', None):
        for key, value in custom['second-stage'].items():
            setattr(layer, key, value)
