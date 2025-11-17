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

import os
import logging
from types import SimpleNamespace

from unittest.mock import patch

from django.test import override_settings

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.multilang import MultiLangHandler
from geonode.metadata.handlers.sparse import SparseHandler, SparseFieldRegistry
from geonode.metadata.manager import MetadataManager
from geonode.metadata.multilang import utils as multi
from geonode.metadata.tests.handlers import FakeHandler, LoaderHandler

from geonode.tests.base import GeoNodeBaseTestSupport


logger = logging.getLogger(__name__)


class MetadataMultilangTests(GeoNodeBaseTestSupport):

    def setUp(self):
        pass

    def tearDown(self):
        super().tearDown()

    def create_metadata_manager(self):
        sr = SparseFieldRegistry()
        mm = MetadataManager()
        mm.handlers = {
            # "base": BaseHandler(),
            "loader": LoaderHandler(schemafile=os.path.join(os.path.dirname(__file__), "data/minimal_schema.json")),
            "fake": FakeHandler(),
            "sparse": SparseHandler(registry=sr),
            "multilang": MultiLangHandler(registry=sr),
        }
        mm.post_init()
        return mm, sr

    def test_schema_add_language(self):
        """
        The MultiLang handler should create one field for each language for each field declared as multilang
        """

        with override_settings(
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=(),
        ):
            mm, sr = self.create_metadata_manager()
            schema = mm.build_schema()
            start_len = len(schema["properties"])

            self.assertIn("title", schema["properties"])
            self.assertEqual(0, len(sr.fields()), f"Unexpected sparse fields found: {sr.fields()}")

        with override_settings(
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
        ):
            mm, sr = self.create_metadata_manager()
            schema = mm.build_schema()

            self.assertEqual(2, len(sr.fields()), "Bad set of sparse fields found")
            self.assertEqual(start_len + 2, len(schema["properties"]), "Bad number of properties in schema")
            self.assertIn(
                multi.get_multilang_field_name("title", "en"), schema["properties"], "Multilang field not found"
            )

    def test_bad_field(self):
        """
        Only text fields should be declared as multilang
        """
        with override_settings(
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["license"],
        ):
            try:
                mm, _ = self.create_metadata_manager()
                mm.build_schema()
                self.fail("Non multilang-able field not detected")
            except ValueError as e:
                logger.info(f"Bad multilang field properly caught: {e}")

    def test_unexisting_field(self):
        """
        Test field existence on declaration of multilang field
        """
        with override_settings(
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["does_not_exists"],
        ):
            try:
                mm, _ = self.create_metadata_manager()
                mm.build_schema()
                self.fail("Missing field not detected")
            except KeyError as e:
                logger.info(f"Missing field properly caught: {e}")

    def test_default_preserialization(self):
        """
        Check that if a multilang field is not populated but the main field is,
        the main field value is copied into the multilang field of the default language
        """
        with override_settings(
            LANGUAGE_CODE="it",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
        ):
            mm, _ = self.create_metadata_manager()
            instance = mm.build_schema_instance(None)
            # logger.info(f"INSTANCE {instance}")
            self.assertEqual("title_fake", instance["title"])
            self.assertEqual("title_fake", instance["title_multilang_it"])
            self.assertIsNone(instance["title_multilang_en"])

    @patch("geonode.base.models.ResourceBase.get_real_instance_class")
    @patch("geonode.indexing.manager.TSVectorIndexManager.update_index")
    @patch("geonode.metadata.handlers.sparse.SparseHandler.update_resource")
    def test_default_base_value(self, mock_get_real_instance_class, mock_update_index, mock_sparse_update):
        """
        The value in the default language of the multilang field should go in the base field whan saving
        """
        with override_settings(
            LANGUAGE_CODE="it",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
        ):
            mm, _ = self.create_metadata_manager()
            self.assertNotIn("base", mm.handlers)
            instance = {
                "title": "whatever",
                "title_multilang_it": "title_it",
                "title_multilang_en": None,
                "abstract": "abstract_fake",
                "license": "license_fake",
            }

            resource = ResourceBase()
            fake_req = SimpleNamespace(data=instance, user=None)
            mm.update_schema_instance(resource, fake_req)

            self.assertEqual("title_it", instance["title"])
