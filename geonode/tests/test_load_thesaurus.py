#########################################################################
#
# Copyright (C) 2020 OSGeo
# Copyright (C) 2022 King's College London
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

import os
from typing import List

from django.core import management
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase
from django.test.testcases import SimpleTestCase
from rdflib import Graph, Literal
from rdflib.exceptions import ParserError
from rdflib.namespace import DC, RDF, SKOS

from geonode.base.management.commands.load_thesaurus import value_for_language
from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel, ThesaurusLabel


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
        self.thesaurus = Thesaurus(
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

    def test_expected_Thesaurus(self):
        actual = self.__get_last_thesaurus()
        self.assertEqual(self.thesaurus.identifier, actual.identifier)
        self.assertEqual(self.thesaurus.title, actual.title)
        self.assertEqual(self.thesaurus.date, actual.date)
        self.assertEqual(self.thesaurus.description, actual.description)
        self.assertEqual(self.thesaurus.slug, actual.slug)
        self.assertEqual(self.thesaurus.about, actual.about)

    def test_expected_ThesaurusKeyword(self):
        tid = self.__get_last_thesaurus()
        actual = ThesaurusKeyword.objects.filter(thesaurus=tid)
        self.assertEqual(2, len(actual))

    def test_expected_ThesaurusKeywordLabel(self):
        tid = self.__get_last_thesaurus()
        tkey = ThesaurusKeyword.objects.filter(thesaurus=tid)[0]
        actual = ThesaurusKeywordLabel.objects.filter(keyword=tkey)
        self.assertEqual(2, len(actual))

    def test_expected_ThesaurusLabel(self):
        tid = self.__get_last_thesaurus()
        actual = ThesaurusLabel.objects.all().filter(thesaurus=tid)
        self.assertEqual(2, len(actual))

    def test_load_from_UploadedFile(self):
        with open(self.rdf_path) as f:
            uf = UploadedFile(f, name=self.rdf_path)
            management.call_command("load_thesaurus", file=uf, name="alt_name", stdout="out")
            alt = Thesaurus.objects.get(identifier="alt_name")
            keywords = ThesaurusKeyword.objects.filter(thesaurus=alt)
            self.assertEqual(2, len(keywords))

    def test_load_from_UploadedFile_fails_with_no_extension(self):
        with open(self.rdf_path) as f:
            uf = UploadedFile(f, name="bad_extension.ext")
            with self.assertRaises(ParserError):
                management.call_command("load_thesaurus", file=uf, name="alt_name", stdout="out", stderr=None)

    @staticmethod
    def __get_last_thesaurus():
        return Thesaurus.objects.all().order_by("-id")[0]


class TestExtractLanguages(SimpleTestCase):
    def setUp(self):
        self.rdf_path = f"{os.path.dirname(os.path.abspath(__file__))}/data/thesaurus.rdf"

    def test_get_all_lang_available_should_return_all_the_lang_available_in_the_file(self):
        titles = self.__load_titles()
        expected = [
            Literal("Italian register of the reference data sets", lang="it"),
            Literal("Register of the reference data sets", lang="en"),
            Literal("Mocked Title", lang=None),
        ]
        self.assertListEqual(expected, titles)

    def test_determinate_title_should_return_the_title_without_lang_if_available(self):
        titles = [
            Literal("Italian register of the reference data sets", lang="it"),
            Literal("Register of the reference data sets", lang="en"),
            Literal("Mocked Title", lang=None),
        ]
        actual = value_for_language(titles, default_lang="")
        self.assertEqual("Mocked Title", actual)

    def test_determinate_title_should_return_the_italian_lang_if_none_is_not_available(self):
        titles = [
            Literal("Italian register of the reference data sets", lang="it"),
            Literal("Register of the reference data sets", lang="en"),
        ]
        actual = value_for_language(titles, "it")
        self.assertEqual("Italian register of the reference data sets", actual)

    def test_determinate_title_should_return_the_title_whithout_lang_even_if_localized_is_available(self):
        titles = [
            Literal("Italian register of the reference data sets", lang="it"),
            Literal("Register of the reference data sets", lang="en"),
            Literal("Mocked Title", lang=None),
        ]
        actual = value_for_language(titles, "it")
        self.assertEqual("Mocked Title", actual)

    def test_determinate_title_should_take_the_first_localized_title_when_default_one_is_not_available(self):
        titles = [
            Literal("Italian register of the reference data sets", lang="it"),
            Literal("Register of the reference data sets", lang="en"),
        ]
        actual = value_for_language(titles, "not-existing")
        self.assertEqual("Italian register of the reference data sets", actual)

    def __load_titles(self) -> List[Literal]:
        g = Graph()
        g.parse(self.rdf_path)

        scheme = g.value(None, RDF.type, SKOS.ConceptScheme, any=False)
        return [t for t in g.objects(scheme, DC.title) if isinstance(t, Literal)]
