#########################################################################
#
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
import json
import os
from io import StringIO

from django.core import management
from django.test import TestCase

from geonode.base.models import Thesaurus


class TestDumpThesaurus(TestCase):
    rdf_path = f"{os.path.dirname(os.path.abspath(__file__))}/data/thesaurus.rdf"

    @classmethod
    def setUpTestData(cls):
        management.call_command(
            "load_thesaurus",
            file=cls.rdf_path,
            name="foo_name",
            stdout="out",
        )

    def setUp(self):
        self.thesaurus = Thesaurus(
            identifier="foo_name",
            title="Mocked Title",
            date="2018-05-23T10:25:56",
            description="Mocked Title",
            slug="",
            about="http://inspire.ec.europa.eu/theme",
        )

    def test_list_thesauri(self):
        out = self.call_dump_command("--list")
        expected = f'id: 1 sort:  0 [0..N]   name={self.thesaurus.identifier} title="{self.thesaurus.title}" URI:{self.thesaurus.about}'
        self.assertEqual(out, expected)

    def test_dump_thesaurus(self):
        out = self.call_dump_command("--name", "foo_name")
        self.assertIn('<skos:ConceptScheme rdf:about="http://inspire.ec.europa.eu/theme">', out)
        self.assertIn('<skos:Concept rdf:about="http://inspire.ec.europa.eu/theme/ad">', out)

    def test_dump_thesaurus_ttl(self):
        out = self.call_dump_command("--name", "foo_name", "--format", "ttl")
        self.assertIn("<http://inspire.ec.europa.eu/theme> a skos:ConceptScheme", out)
        self.assertIn("<http://inspire.ec.europa.eu/theme/ad> a skos:Concept", out)

    def test_dump_thesaurus_jsonld(self):
        out = self.call_dump_command("--name", "foo_name", "--format", "json-ld")
        self.assertEqual(3, len(json.loads(out)))
        self.assertIn("Italian register of the reference data sets", out)

    @staticmethod
    def call_dump_command(*args) -> str:
        out = StringIO()
        management.call_command(
            "dump_thesaurus",
            *args,
            stdout=out,
        )
        return out.getvalue().strip()
