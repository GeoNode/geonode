#########################################################################
#
# Copyright (C) 2024 OSGeo
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

import time

from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.metadata.handlers.sparse import SparseHandler, SparseFieldRegistry
from geonode.metadata.manager import MetadataManager
from geonode.metadata.i18n import I18N_THESAURUS_IDENTIFIER

from geonode.base.models import (
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    Thesaurus,
)


class MetadataI18NTests(GeoNodeBaseTestSupport):

    def setUp(self):
        # set a single handler to speed up things
        self.sparse_registry = SparseFieldRegistry()

        self.mm = MetadataManager()
        self.mm.handlers = {
            "sparse": SparseHandler(registry=self.sparse_registry),
        }

        self.tid = Thesaurus.objects.create(title="Spatial scope thesaurus", identifier=I18N_THESAURUS_IDENTIFIER).id

    def _add_label(self, about, lang, label):
        tk, created = ThesaurusKeyword.objects.get_or_create(
            about=about, thesaurus_id=self.tid, defaults={"alt_label": f"alt_{about}"}
        )
        if lang and label:
            ThesaurusKeywordLabel.objects.create(keyword=tk, label=label, lang=lang)
        # this is needed to invalidate i18ncache
        Thesaurus.objects.filter(pk=self.tid).update(date=str(time.time_ns()))

    def tearDown(self):
        super().tearDown()

    def test_schema_i18n_title_not_defined(self):
        """
        Ensure the title is set according to the Thesaurus entries, when annotation is not in the schema
        """

        self.sparse_registry.register("field1", {"type": "number"})
        schema = self.mm.build_schema(lang="en")

        # print(f"TEST SCHEMA:  {schema}")
        # print(f"TEST I18NCACHE:  {metadata_manager._i18n_cache.get_entry('en', I18nCache.DATA_KEY_LABELS)}")

        # plain schema, no labels
        self.assertIn("field1", schema["properties"])
        self.assertNotIn("title", schema["properties"]["field1"])

        # label from property name
        self._add_label("field1", "en", "f1_en")
        schema = self.mm.build_schema(lang="en")
        self.assertIn("title", schema["properties"]["field1"])
        self.assertEqual("f1_en", schema["properties"]["field1"]["title"])

        # label from overridden label
        self._add_label("field1__ovr", "en", "f1_ovr_en")
        schema = self.mm.build_schema(lang="en")
        self.assertIn("title", schema["properties"]["field1"])
        self.assertEqual("f1_ovr_en", schema["properties"]["field1"]["title"])

        # ovr should not affect other languages
        schema_it = self.mm.build_schema(lang="it")
        self.assertIn("title", schema_it["properties"]["field1"])
        self.assertEqual("alt_field1", schema_it["properties"]["field1"]["title"])

    def test_schema_i18n_description_not_defined(self):
        """
        Ensure the description is set according to the Thesaurus entries, when annotation is not in the schema
        """

        self.sparse_registry.register("field1", {"type": "number"})
        schema = self.mm.build_schema(lang="en")

        # print(f"TEST SCHEMA:  {schema}")
        # print(f"TEST I18NCACHE:  {metadata_manager._i18n_cache.get_entry('en', I18nCache.DATA_KEY_LABELS)}")

        # plain schema, no labels
        self.assertIn("field1", schema["properties"])
        self.assertNotIn("description", schema["properties"]["field1"])

        # label from property name
        self._add_label("field1__descr", "en", "f1_en_descr")
        schema = self.mm.build_schema(lang="en")
        self.assertIn("description", schema["properties"]["field1"])
        self.assertEqual("f1_en_descr", schema["properties"]["field1"]["description"])

        # label from overridden label
        self._add_label("field1__descr__ovr", "en", "f1_ovr_en__descr")
        schema = self.mm.build_schema(lang="en")
        self.assertIn("description", schema["properties"]["field1"])
        self.assertEqual("f1_ovr_en__descr", schema["properties"]["field1"]["description"])

    def test_schema_i18n_title_defined(self):
        """
        Ensure the title is set according to the Thesaurus entries, when annotation is in the schema
        """

        self.sparse_registry.register("field1", {"type": "number", "title": "t1"})
        schema = self.mm.build_schema(lang="en")

        # declared label, no thesaurus entry
        self.assertIn("field1", schema["properties"])
        self.assertIn("title", schema["properties"]["field1"])
        self.assertEqual("t1", schema["properties"]["field1"]["title"])

        # label defined with key=propertyname should not be used
        self._add_label("field1", "en", "f1_en")
        schema = self.mm.build_schema(lang="en")
        self.assertEqual("t1", schema["properties"]["field1"]["title"])

        # label from explicit title annotation
        self._add_label("t1", "en", "t1_en")
        schema = self.mm.build_schema(lang="en")
        self.assertEqual("t1_en", schema["properties"]["field1"]["title"])

        # label from overridden label -- key is the property name
        self._add_label("field1__ovr", "en", "f1_ovr_en")
        schema = self.mm.build_schema(lang="en")
        self.assertEqual("f1_ovr_en", schema["properties"]["field1"]["title"])
