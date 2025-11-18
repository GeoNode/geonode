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

import logging

from unittest.mock import patch, ANY

from django.test import override_settings

from geonode.indexing.manager import TSVectorIndexManager
from geonode.tests.base import GeoNodeBaseTestSupport


logger = logging.getLogger(__name__)


class IndexingTests(GeoNodeBaseTestSupport):

    def setUp(self):
        pass

    def tearDown(self):
        super().tearDown()

    @patch("geonode.indexing.models.ResourceIndex.objects.update_or_create")
    def test_no_multilang(self, mock_uoc):
        """
        If no multilang fields, indexes should be created with lang=None
        """
        with override_settings(
            LANGUAGE_CODE="en",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=[],
            METADATA_INDEXES={
                "idx1": ["title"],
                "idx2": ["title", "f2"],
            },
        ):
            instance = {
                "title": "TheTitle",
                "f2": "data2",
            }

            expected_calls = (
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx1"}, "TheTitle"),
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx2"}, "TheTitle data2"),
            )

            self._run_index_test(instance, mock_uoc, expected_calls)

    @patch("geonode.indexing.models.ResourceIndex.objects.update_or_create")
    def test_multilang_title(self, mock_uoc):
        """
        Only the title is multilang
        """
        with override_settings(
            LANGUAGE_CODE="en",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
            METADATA_INDEXES={
                "idx1": ["title"],
                "idx12": ["title", "f2"],
                "idx123": ["title", "f2", "f3"],
            },
        ):
            instance = {
                "title": "TheTitleBase",
                "title_multilang_en": "TheTitle",
                "title_multilang_it": "IlTitolo",
                "f2": "v2",
                "f3": "v3",
            }

            expected_calls = (
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx1"}, "TheTitle"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx1"}, "IlTitolo"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx12"}, "TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx12"}, "IlTitolo v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx123"}, "TheTitle v2 v3"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx123"}, "IlTitolo v2 v3"),
            )

            self._run_index_test(instance, mock_uoc, expected_calls)

    @patch("geonode.indexing.models.ResourceIndex.objects.update_or_create")
    def test_multilang_title_missing(self, mock_uoc):
        """
        Title is multilang, one translation is missing.
        The missing index should include the default field and all the translated entries
        """
        with override_settings(
            LANGUAGE_CODE="en",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["title"],
            METADATA_INDEXES={
                "idx1": ["title"],
                "idx12": ["title", "f2"],
                "idx123": ["title", "f2", "f3"],
            },
        ):
            instance = {
                "title": "TheTitleBase",
                "title_multilang_en": "TheTitle",
                "title_multilang_it": None,  # this is the missing translation
                "f2": "v2",
                "f3": "v3",
            }

            expected_calls = (
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx1"}, "TheTitle"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx1"}, "TheTitle TheTitleBase"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx12"}, "TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx12"}, "TheTitle TheTitleBase v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx123"}, "TheTitle v2 v3"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx123"}, "TheTitle TheTitleBase v2 v3"),
            )

            self._run_index_test(instance, mock_uoc, expected_calls)

    @patch("geonode.indexing.models.ResourceIndex.objects.update_or_create")
    def test_multilang_single_secondary_field(self, mock_uoc):
        """
        The multilang field is a secondary field.
        In a multilang context, indexes created with only non multilang fields should be created with lang=None.
        """
        with override_settings(
            LANGUAGE_CODE="en",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["f3"],
            METADATA_INDEXES={
                "idx1": ["title"],
                "idx12": ["title", "f2"],
                "idx123": ["title", "f2", "f3"],
            },
        ):
            instance = {
                "title": "TheTitle",
                "f2": "v2",
                "f3": "v3",
                "f3_multilang_en": "v3_EN",
                "f3_multilang_it": "v3_IT",
            }

            expected_calls = (
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx1"}, "TheTitle"),
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx12"}, "TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx123"}, "v3_IT TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx123"}, "v3_EN TheTitle v2"),
            )

            self._run_index_test(instance, mock_uoc, expected_calls)

    @patch("geonode.indexing.models.ResourceIndex.objects.update_or_create")
    def test_multilang_with_secondary_lang_missing(self, mock_uoc):
        """
        The multilang field is a secondary field, with one translation missing.
        In a multilang context, indexes created with only non multilang fields should be created with lang=None.
        """
        with override_settings(
            LANGUAGE_CODE="en",
            LANGUAGES=[("en", "English"), ("it", "Italiano")],
            MULTILANG_FIELDS=["f3"],
            METADATA_INDEXES={
                "idx1": ["title"],
                "idx12": ["title", "f2"],
                "idx123": ["title", "f2", "f3"],
            },
        ):
            instance = {
                "title": "TheTitle",
                "f2": "v2",
                "f3": "v3",
                "f3_multilang_en": "v3_multilang_en",
                "f3_multilang_it": None,
            }

            expected_calls = (
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx1"}, "TheTitle"),
                ({"defaults": ANY, "resource_id": 0, "lang": None, "name": "idx12"}, "TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "en", "name": "idx123"}, "v3_multilang_en TheTitle v2"),
                ({"defaults": ANY, "resource_id": 0, "lang": "it", "name": "idx123"}, "TheTitle v2"),
            )

            self._run_index_test(instance, mock_uoc, expected_calls)

    def _run_index_test(self, instance, mock_uoc, expected_calls):
        """
        Test the calls to update_or_create
        :param: expected_calls contains the explicit params ass dict and a String containing the indexed data
        """
        im = TSVectorIndexManager()
        im.update_index(0, instance)
        call_args_list = mock_uoc.call_args_list
        # logger.debug(f"UOC called with {mock_uoc.call_args_list}")

        self.assertEqual(len(expected_calls), mock_uoc.call_count)
        for args, idx_data in expected_calls:
            # check the explicit call's params
            mock_uoc.assert_any_call(**args)
            # check the string to be indexed
            self._assert_tsvector_value(idx_data, args, call_args_list)

    def _assert_tsvector_value(self, idx_data, args, call_args_list):
        def find_call(args, call_args_list):
            for _, ck in call_args_list:
                if args["lang"] == ck["lang"] and args["name"] == ck["name"]:
                    return ck
            raise KeyError(f"Call not found {args}")  # should not happen

        called = find_call(args, call_args_list)
        vector = called["defaults"]["vector"]
        # logger.debug(f"VECTOR {vector}")
        # logger.debug(f"VECTOR EXPR is {vector.source_expressions}")
        value = vector.source_expressions[0].value
        # logger.debug(f"VECTOR VALUE is '{value}'")
        if idx_data is not None:
            self.assertEqual(idx_data, value, f"Bad index content for {args}")
        else:
            logger.info(f"Skipping test for index value for {args}")
            logger.debug(f"VECTOR VALUE is '{value}'")
            return
