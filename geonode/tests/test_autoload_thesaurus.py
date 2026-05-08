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

import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase

from geonode.base.management.commands.thesaurus import autoload_thesauri
from geonode.base.models import Thesaurus


RDF_CONTENT = """\
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <skos:ConceptScheme xmlns:skos="http://www.w3.org/2004/02/skos/core#"
      rdf:about="http://example.com/autoload-test-scheme">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">Autoload Test Thesaurus</dc:title>
    <dcterms:issued xmlns:dcterms="http://purl.org/dc/terms/">2024-01-01</dcterms:issued>
  </skos:ConceptScheme>
  <skos:Concept xmlns:skos="http://www.w3.org/2004/02/skos/core#"
      rdf:about="http://example.com/autoload-test-scheme/concept1">
    <skos:prefLabel xml:lang="en">Concept One</skos:prefLabel>
    <skos:inScheme rdf:resource="http://example.com/autoload-test-scheme" />
  </skos:Concept>
</rdf:RDF>
"""


class TestAutoloadThesauri(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.thesauri_dir = os.path.join(self.tmp_dir, "thesauri")
        os.makedirs(self.thesauri_dir)
        self.rdf_file = os.path.join(self.thesauri_dir, "autoload_test.rdf")
        with open(self.rdf_file, "w", encoding="utf-8") as f:
            f.write(RDF_CONTENT)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _make_app_config(self, name, path):
        app_config = MagicMock()
        app_config.name = name
        app_config.path = path
        return app_config

    def test_autoload_loads_rdf_files_from_thesauri_dirs(self):
        """autoload_thesauri should load .rdf files found in thesauri/ dirs of installed apps."""
        app_configs = [self._make_app_config("fake_app", self.tmp_dir)]
        with patch("geonode.base.management.commands.thesaurus.apps.get_app_configs", return_value=app_configs):
            autoload_thesauri()

        self.assertTrue(
            Thesaurus.objects.filter(about="http://example.com/autoload-test-scheme").exists(),
            "The thesaurus should have been loaded from the app's thesauri/ directory",
        )

    def test_autoload_is_idempotent(self):
        """Calling autoload_thesauri twice should not create duplicate thesauri (uses update action)."""
        app_configs = [self._make_app_config("fake_app", self.tmp_dir)]
        with patch("geonode.base.management.commands.thesaurus.apps.get_app_configs", return_value=app_configs):
            autoload_thesauri()
            autoload_thesauri()

        count = Thesaurus.objects.filter(about="http://example.com/autoload-test-scheme").count()
        self.assertEqual(1, count, "Running autoload twice should not create duplicate thesauri")

    def test_autoload_skips_apps_without_thesauri_dir(self):
        """autoload_thesauri should silently skip apps that have no thesauri/ directory."""
        app_without_thesauri = self._make_app_config("no_thesauri_app", self.tmp_dir.rstrip("/") + "_no_dir")
        app_configs = [app_without_thesauri]
        with patch("geonode.base.management.commands.thesaurus.apps.get_app_configs", return_value=app_configs):
            # Should not raise
            autoload_thesauri()

        self.assertEqual(0, Thesaurus.objects.count(), "No thesauri should be loaded when thesauri/ dir is absent")

    def test_autoload_continues_after_error(self):
        """autoload_thesauri should continue loading other files if one fails."""
        bad_rdf = os.path.join(self.thesauri_dir, "aaaa_bad.rdf")
        with open(bad_rdf, "w") as f:
            f.write("THIS IS NOT VALID RDF")

        app_configs = [self._make_app_config("fake_app", self.tmp_dir)]
        with patch("geonode.base.management.commands.thesaurus.apps.get_app_configs", return_value=app_configs):
            # Should not raise despite the bad file
            autoload_thesauri()

        # The valid thesaurus (sorted after the bad one alphabetically: autoload_test > aaaa_bad) should still load
        self.assertTrue(
            Thesaurus.objects.filter(about="http://example.com/autoload-test-scheme").exists(),
            "Valid thesaurus should be loaded even if another file in the same dir fails",
        )
