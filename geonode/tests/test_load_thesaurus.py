#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.test.testcases import SimpleTestCase
from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel
from django.test import TestCase
from django.core import management
from defusedxml import lxml as dlxml
from geonode.base.management.commands.load_thesaurus import get_all_lang_available_with_title, determinate_value
import os


class TestLoadThesaurus(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command(
            "load_thesaurus",
            file=f"{os.path.dirname(os.path.abspath(__file__))}/data/thesaurus.rdf",
            name="foo_name",
            stdout="out",
        )

    def setUp(self):
        self.rdf_path = f"{os.path.dirname(os.path.abspath(__file__))}/data/thesaurus.rdf"
        self.Thesaurus = Thesaurus(
            identifier="foo_name",
            title="Mocked Title",
            date="2018-05-23T10:25:56",
            description="Mocked Title",
            slug="",
            about="http://inspire.ec.europa.eu/theme",
        )

    def test_given_invalid_filename_will_raise_an_oserror(self):
        with self.assertRaises(OSError):
            management.call_command("load_thesaurus", file="abc", name="foo_name", stdout="out")

    def test_give_a_valid_name_should_save_the_expected_Thesaurus(self):
        actual = self.__get_last_thesaurus()
        self.assertEqual(self.Thesaurus.identifier, actual.identifier)
        self.assertEqual(self.Thesaurus.title, actual.title)
        self.assertEqual(self.Thesaurus.date, actual.date)
        self.assertEqual(self.Thesaurus.description, actual.description)
        self.assertEqual(self.Thesaurus.slug, actual.slug)
        self.assertEqual(self.Thesaurus.about, actual.about)

    def test_give_a_valid_name_should_save_the_expected_ThesaurusKeyword(self):
        tid = self.__get_last_thesaurus()
        actual = ThesaurusKeyword.objects.filter(thesaurus=tid)
        self.assertEqual(2, len(actual))

    def test_give_a_valid_name_should_save_the_expected_ThesaurusKeywordLabel(self):
        tkey = ThesaurusKeyword.objects.filter(thesaurus=self.__get_last_thesaurus())[0]
        actual = ThesaurusKeywordLabel.objects.filter(keyword=tkey)
        self.assertEqual(2, len(actual))

    def test_give_a_valid_name_should_save_the_expected_ThesaurusLabel(self):
        tid = self.__get_last_thesaurus()
        actual = ThesaurusLabel.objects.all().filter(thesaurus=tid)
        self.assertEqual(2, len(actual))

    @staticmethod
    def __get_last_thesaurus():
        return Thesaurus.objects.all().order_by("-id")[0]


class TestExtractLanguages(SimpleTestCase):
    def setUp(self):
        self.rdf_path = f"{os.path.dirname(os.path.abspath(__file__))}/data/thesaurus.rdf"

    def test_get_all_lang_available_should_return_all_the_lang_available_int_the_file(self):
        titles = self.__load_titles()
        XML_URI = "http://www.w3.org/XML/1998/namespace"
        LANG_ATTRIB = f"{{{XML_URI}}}lang"
        actual = get_all_lang_available_with_title(titles, LANG_ATTRIB)
        expected = [
            ("it", "Italian register of the reference data sets"),
            ("en", "Register of the reference data sets"),
            (None, "Mocked Title"),
        ]
        self.assertListEqual(expected, actual)

    def test_determinate_title_should_return_the_title_without_lang_if_available(self):
        titles = [
            ("it", "Italian register of the reference data sets"),
            ("en", "Register of the reference data sets"),
            (None, "Mocked Title"),
        ]
        actual = determinate_value(titles, None)
        self.assertEqual("Mocked Title", actual)

    def test_determinate_title_should_return_the_italian_lang_if_none_is_not_available(self):
        titles = [
            ("it", "Italian register of the reference data sets"),
            ("en", "Register of the reference data sets"),
        ]
        actual = determinate_value(titles, "it")
        self.assertEqual("Italian register of the reference data sets", actual)

    def test_determinate_title_should_return_the_title_whithout_lang_even_if_localized_is_available(self):
        titles = [
            ("it", "Italian register of the reference data sets"),
            ("en", "Register of the reference data sets"),
            (None, "Mocked Title"),
        ]
        actual = determinate_value(titles, "it")
        self.assertEqual("Mocked Title", actual)

    def test_determinate_title_should_take_the_first_localized_title_when_default_one_is_not_available(self):
        titles = [
            ("it", "Italian register of the reference data sets"),
            ("en", "Register of the reference data sets"),
        ]
        actual = determinate_value(titles, "not-existing")
        self.assertEqual("Italian register of the reference data sets", actual)

    def __load_titles(self):
        RDF_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ns = {
            "rdf": RDF_URI,
            "foaf": "http://xmlns.com/foaf/0.1/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
        }

        tfile = dlxml.parse(self.rdf_path)
        root = tfile.getroot()

        scheme = root.find("skos:ConceptScheme", ns)
        return scheme.findall("dc:title", ns)
