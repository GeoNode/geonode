#########################################################################
#
# Copyright (C) 2026 OSGeo
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
"""
MetadataValidator exercised as a direct API: no management command, no CLI parsing.
geonode.metadata.tests.test_validate_metadata already covers the reporting contract
(valid/invalid, max_errors, value truncation, ...) through the command; this file is
about what is only reachable by calling the class itself.
"""
import sys
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext_lazy

from geonode.base.models import ResourceBase
from geonode.metadata.validation import MAX_SCHEMA_ERRORS, MetadataValidator

# Optional "edition" rejects the null it gets when left empty: a defect of the schema.
# Optional "abstract" accepts it: not a defect.
BASE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string", "title": "Title"},
        "abstract": {"type": ["string", "null"], "title": "Abstract"},
        "edition": {"type": "string", "title": "Edition"},
    },
}


class MetadataValidatorConstructionTests(SimpleTestCase):
    def test_required_and_broken_optionals_are_computed_from_the_schema(self):
        validator = MetadataValidator(schema=BASE_SCHEMA)

        self.assertEqual({"title"}, validator.required_fields)
        self.assertEqual({"edition"}, validator.broken_optionals)

    def test_valid_schema_has_no_schema_errors(self):
        validator = MetadataValidator(schema=BASE_SCHEMA)

        self.assertEqual([], validator.schema_errors)

    def test_broken_schema_is_reported_in_schema_errors(self):
        broken = dict(BASE_SCHEMA, properties=dict(BASE_SCHEMA["properties"], edition={"maxLength": "nope"}))

        validator = MetadataValidator(schema=broken)

        self.assertEqual(1, len(validator.schema_errors))
        self.assertIn("/properties/edition/maxLength", validator.schema_errors[0])

    def test_schema_errors_are_capped(self):
        # one broken keyword per property, well past the cap
        properties = {f"f{i}": {"maxLength": "nope"} for i in range(MAX_SCHEMA_ERRORS + 5)}
        broken = dict(BASE_SCHEMA, properties=properties)

        validator = MetadataValidator(schema=broken)

        self.assertEqual(MAX_SCHEMA_ERRORS + 1, len(validator.schema_errors))
        self.assertIn("skipping the rest", validator.schema_errors[-1])

    def test_missing_jsonschema_package_raises_import_error(self):
        with patch.dict(sys.modules, {"jsonschema": None}):
            with self.assertRaises(ImportError):
                MetadataValidator(schema=BASE_SCHEMA)


class MetadataValidatorFormatCheckingTests(SimpleTestCase):
    SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"reportDate": {"type": "string", "title": "Report date", "format": "date"}},
    }

    def test_bad_format_is_ignored_by_default(self):
        validator = MetadataValidator(schema=self.SCHEMA)

        record = validator.validate_instance({"id": 1}, {"reportDate": "not-a-date"})

        self.assertTrue(record["valid"])

    def test_bad_format_is_reported_when_check_formats_is_enabled(self):
        validator = MetadataValidator(schema=self.SCHEMA, check_formats=True)

        record = validator.validate_instance({"id": 1}, {"reportDate": "not-a-date"})

        self.assertFalse(record["valid"])
        self.assertEqual("format", record["errors"][0]["validator"])
        self.assertEqual("/reportDate", record["errors"][0]["path"])


class MetadataValidatorInstanceTests(SimpleTestCase):
    def test_empty_optional_field_is_a_schema_defect_counted_and_excluded(self):
        validator = MetadataValidator(schema=BASE_SCHEMA)

        first = validator.validate_instance({"id": 1}, {"title": "a", "edition": None})
        second = validator.validate_instance({"id": 2}, {"title": "b", "edition": None})

        self.assertTrue(first["valid"])
        self.assertTrue(second["valid"])
        self.assertEqual({"edition": 2}, validator.observed_defects)

    def test_null_failing_several_keywords_is_reported_once_preferring_type(self):
        # "code" is nested, so it is not eligible for the top-level-only schema-defect shortcut:
        # the null genuinely trips both "type" and "enum", and drop_redundant must dedupe them
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "title": "Nested",
                    "properties": {"code": {"type": "string", "enum": ["a", "b"], "title": "Code"}},
                }
            },
        }
        validator = MetadataValidator(schema=schema)

        record = validator.validate_instance({"id": 1}, {"nested": {"code": None}})

        self.assertEqual(1, len(record["errors"]))
        self.assertEqual("type", record["errors"][0]["validator"])

    def test_missing_required_field_below_top_level_is_worded_as_required(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "title": "Nested",
                    "required": ["code"],
                    "properties": {"code": {"type": "string", "title": "Code"}},
                }
            },
        }
        validator = MetadataValidator(schema=schema)

        record = validator.validate_instance({"id": 1}, {"nested": {}})

        error = record["errors"][0]
        self.assertEqual("/nested/code", error["path"])
        self.assertEqual("Nested/Code", error["title"])
        self.assertEqual("not set (required field)", error["message"])

    def test_array_item_error_path_and_title_carry_the_index(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "contacts": {
                    "type": "array",
                    "title": "Contacts",
                    "items": {
                        "type": "object",
                        "title": "Contact",
                        "properties": {"email": {"type": "string", "title": "Email"}},
                    },
                }
            },
        }
        validator = MetadataValidator(schema=schema)

        record = validator.validate_instance({"id": 1}, {"contacts": [{"email": 123}]})

        error = record["errors"][0]
        self.assertEqual("/contacts/0/email", error["path"])
        self.assertEqual("Contacts/[0]/Email", error["title"])

    def test_extra_errors_testing_key_is_dropped_before_validation(self):
        validator = MetadataValidator(schema=BASE_SCHEMA)
        instance = {"title": "a", "extraErrors": "boom"}

        validator.validate_instance({"id": 1}, instance)

        self.assertNotIn("extraErrors", instance)

    def test_as_json_types_renders_lazy_strings_down_to_plain_str(self):
        rendered = MetadataValidator.as_json_types({"title": gettext_lazy("hello")})

        self.assertEqual({"title": "hello"}, rendered)
        self.assertIs(str, type(rendered["title"]))


class MetadataValidatorResourceTests(TestCase):
    """validate_resource(), the entry point that goes through the metadata manager"""

    def setUp(self):
        owner = get_user_model().objects.create_user("validator_user", "v@fakemail.com", "pwd")
        self.resource = ResourceBase.objects.create(
            title="A dataset", uuid=str(uuid4()), resource_type="dataset", owner=owner
        )
        self.validator = MetadataValidator(schema=BASE_SCHEMA)

        patcher = patch("geonode.metadata.validation.validator.metadata_manager")
        self.manager = patcher.start()
        self.addCleanup(patcher.stop)

    def test_instance_is_built_through_the_metadata_manager_and_then_validated(self):
        self.manager.build_schema_instance.return_value = {"title": "fine"}

        record = self.validator.validate_resource(self.resource)

        self.manager.build_schema_instance.assert_called_once_with(self.resource, self.validator.lang)
        self.assertEqual(self.resource.pk, record["id"])
        self.assertEqual(self.resource.uuid, record["uuid"])
        self.assertEqual("dataset", record["resource_type"])
        self.assertTrue(record["valid"])

    def test_a_failing_handler_is_reported_against_the_resource_not_raised(self):
        self.manager.build_schema_instance.side_effect = RuntimeError("handler exploded")

        record = self.validator.validate_resource(self.resource)

        self.assertFalse(record["valid"])
        self.assertEqual("geonode:build_schema_instance", record["errors"][0]["validator"])
        self.assertIn("handler exploded", record["errors"][0]["message"])
