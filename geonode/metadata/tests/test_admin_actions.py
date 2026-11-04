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
The validate_metadata / download_validation_report admin actions, exercised directly: both only
need a modeladmin with message_user() and a request/queryset, no admin site or HTTP client involved.
"""
import json
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from geonode.base.models import ResourceBase
from geonode.metadata.admin import MAX_REPORTED_RESOURCES, download_validation_report, validate_metadata

# "edition" is optional and rejects the null it gets when left empty: a schema defect, not a
# resource error. "title" has a tight maxLength so a long one is an easy resource error to trigger.
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string", "title": "Title", "maxLength": 20},
        "edition": {"type": "string", "title": "Edition"},
    },
}


class MetadataManagerMixin:
    """Resources plus a mocked metadata_manager feeding MetadataValidator a known schema/instances"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user("admin_action_user", "a@fakemail.com", "pwd")
        self.valid = self.make_resource("Valid one")
        self.invalid = self.make_resource("Invalid one")
        self.defect = self.make_resource("Defect one")

        self.instances = {
            self.valid.uuid: {"title": "fine"},
            self.invalid.uuid: {"title": "x" * 25},  # longer than the schema's maxLength: 20
            self.defect.uuid: {"title": "fine", "edition": None},
        }

        patcher = patch("geonode.metadata.validation.validator.metadata_manager")
        self.manager = patcher.start()
        self.addCleanup(patcher.stop)
        self.manager.get_schema.return_value = SCHEMA
        self.manager.build_schema_instance.side_effect = lambda resource, lang: dict(self.instances[resource.uuid])

        self.modeladmin = MagicMock()
        self.request = RequestFactory().get("/admin/")

    def make_resource(self, title):
        return ResourceBase.objects.create(title=title, uuid=str(uuid4()), resource_type="dataset", owner=self.owner)

    def queryset(self, *resources):
        return ResourceBase.objects.filter(pk__in=[r.pk for r in resources])


class ValidateMetadataActionTests(MetadataManagerMixin, TestCase):
    def messages(self):
        return [(call.args[1], call.args[2]) for call in self.modeladmin.message_user.call_args_list]

    def test_all_valid_reports_success(self):
        validate_metadata(self.modeladmin, self.request, self.queryset(self.valid))

        text, level = self.messages()[-1]
        self.assertEqual("Validated 1 resource(s): all valid", text)
        self.assertEqual(messages.SUCCESS, level)

    def test_invalid_resource_is_described_and_summarized_as_an_error(self):
        validate_metadata(self.modeladmin, self.request, self.queryset(self.valid, self.invalid))

        calls = self.messages()
        texts = [t for t, _ in calls]
        described = next(t for t in texts if t.startswith("'Invalid one'"))
        self.assertIn("too long", described)
        self.assertEqual("Validated 2 resource(s): 1 invalid, 1 valid", calls[-1][0])
        self.assertEqual(messages.ERROR, calls[-1][1])

    def test_schema_defect_is_blamed_on_the_schema_not_the_resource(self):
        validate_metadata(self.modeladmin, self.request, self.queryset(self.defect))

        calls = self.messages()
        texts = [t for t, _ in calls]
        self.assertTrue(any("a problem of the schema itself, not of the selected resources" in t for t in texts))
        # the resource itself is not to blame: it is reported as valid
        self.assertEqual("Validated 1 resource(s): all valid", calls[-1][0])

    def broken_schema(self, property_count):
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {f"f{i}": {"maxLength": "nope"} for i in range(property_count)},
        }

    def test_schema_errors_within_the_cap_are_all_shown(self):
        self.manager.get_schema.return_value = self.broken_schema(3)

        validate_metadata(self.modeladmin, self.request, self.queryset(self.valid))

        warnings = [text for text, level in self.messages() if level == messages.WARNING]
        self.assertEqual(3, len(warnings))
        self.assertFalse(any("more schema problem" in w for w in warnings))

    def test_schema_errors_past_the_cap_point_at_the_download_action(self):
        self.manager.get_schema.return_value = self.broken_schema(MAX_REPORTED_RESOURCES + 3)

        validate_metadata(self.modeladmin, self.request, self.queryset(self.valid))

        warnings = [text for text, level in self.messages() if level == messages.WARNING]
        self.assertEqual(MAX_REPORTED_RESOURCES + 1, len(warnings))  # capped, plus one omission notice
        self.assertIn("3 more schema problem", warnings[-1])
        self.assertIn("Download validation report", warnings[-1])

    def test_reported_resources_are_capped(self):
        extra = [self.make_resource(f"Bad {i}") for i in range(MAX_REPORTED_RESOURCES)]
        for resource in extra:
            self.instances[resource.uuid] = {"title": "x" * 25}

        validate_metadata(self.modeladmin, self.request, self.queryset(self.invalid, *extra))

        texts = [t for t, _ in self.messages()]
        described = [t for t in texts if t.startswith("'Bad") or t.startswith("'Invalid one'")]
        self.assertEqual(MAX_REPORTED_RESOURCES, len(described))
        self.assertIn("only the first", texts[-1])

    def test_missing_jsonschema_package_is_reported_and_stops_processing(self):
        with patch.dict(sys.modules, {"jsonschema": None}):
            validate_metadata(self.modeladmin, self.request, self.queryset(self.valid))

        calls = self.messages()
        self.assertEqual(1, len(calls))
        self.assertIn("jsonschema", calls[0][0])
        self.assertEqual(messages.ERROR, calls[0][1])
        self.manager.build_schema_instance.assert_not_called()


class DownloadValidationReportActionTests(MetadataManagerMixin, TestCase):
    def test_response_is_a_json_attachment(self):
        response = download_validation_report(self.modeladmin, self.request, self.queryset(self.valid))

        self.assertEqual("application/json", response["Content-Type"])
        self.assertEqual('attachment; filename="metadata_validation_report.json"', response["Content-Disposition"])

    def test_report_holds_every_resource_with_full_error_details(self):
        response = download_validation_report(self.modeladmin, self.request, self.queryset(self.valid, self.invalid))

        report = json.loads(response.content)
        by_id = {record["id"]: record for record in report["resources"]}
        self.assertEqual({self.valid.pk, self.invalid.pk}, set(by_id))
        self.assertTrue(by_id[self.valid.pk]["valid"])
        self.assertFalse(by_id[self.invalid.pk]["valid"])
        self.assertIn("too long", by_id[self.invalid.pk]["errors"][0]["message"])

    def test_nothing_is_capped_past_the_admin_message_limit(self):
        extra = [self.make_resource(f"Bad {i}") for i in range(MAX_REPORTED_RESOURCES + 3)]
        for resource in extra:
            self.instances[resource.uuid] = {"title": "x" * 25}

        response = download_validation_report(self.modeladmin, self.request, self.queryset(self.invalid, *extra))

        report = json.loads(response.content)
        self.assertEqual(MAX_REPORTED_RESOURCES + 4, len(report["resources"]))
        self.assertNotIn("only the first", report["summary"][-1])

    def test_schema_defect_is_worded_the_same_way_as_the_message_action(self):
        response = download_validation_report(self.modeladmin, self.request, self.queryset(self.defect))

        report = json.loads(response.content)
        self.assertTrue(
            any("a problem of the schema itself, not of the selected resources" in m for m in report["summary"])
        )

    def test_missing_jsonschema_package_messages_the_user_and_returns_none(self):
        with patch.dict(sys.modules, {"jsonschema": None}):
            result = download_validation_report(self.modeladmin, self.request, self.queryset(self.valid))

        self.assertIsNone(result)
        self.modeladmin.message_user.assert_called_once()
        self.assertEqual(messages.ERROR, self.modeladmin.message_user.call_args.args[2])
