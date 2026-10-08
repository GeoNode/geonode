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
import csv
import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from geonode.base.models import ResourceBase
from geonode.metadata.management.commands import validate_metadata

COMMAND = "validate_metadata"

# A schema small enough to make every assertion below exact
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["title", "abstract"],
    "properties": {
        "uuid": {"type": "string", "title": "UUID"},
        "title": {"type": "string", "title": "Title", "maxLength": 10},
        "abstract": {"type": ["string", "null"], "title": "Abstract"},
        # optional and not nullable: the null it gets when empty is a defect of the schema
        "edition": {"type": "string", "title": "Edition"},
    },
}


class ValidateMetadataCommandMixin:
    def call(self, *args, **options):
        """Run the command, returning its output and its exit code"""
        out = StringIO()
        code = 0
        try:
            management.call_command(COMMAND, *args, stdout=out, **options)
        except SystemExit as e:
            code = e.code
        return out.getvalue(), code

    def write_json(self, name, content):
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w") as outfile:
            json.dump(content, outfile)
        return path


class ValidateMetadataOfflineTests(ValidateMetadataCommandMixin, SimpleTestCase):
    """
    The reporting contract, exercised through --schema and --instance: no db, no metadata manager
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.schema = self.write_json("schema.json", SCHEMA)

        self.valid = self.write_json("valid.json", {"uuid": "u-1", "title": "fine", "abstract": "a"})
        self.invalid = self.write_json("invalid.json", {"uuid": "u-2", "title": 42, "abstract": "a"})

    def report(self, *instances, **options):
        out, code = self.call(schema_file=self.schema, instance_files=list(instances), **options)
        return json.loads(out), code

    def test_valid_instance_is_not_reported_and_exits_zero(self):
        report, code = self.report(self.valid)

        self.assertEqual([], report["resources"])
        self.assertEqual(0, code)

    def test_valid_instance_is_reported_on_demand(self):
        report, _ = self.report(self.valid, include_valid=True)

        self.assertEqual(1, len(report["resources"]))
        self.assertTrue(report["resources"][0]["valid"])
        self.assertEqual(self.valid, report["resources"][0]["id"])
        self.assertEqual("u-1", report["resources"][0]["uuid"])

    def test_invalid_instance_exits_one(self):
        report, code = self.report(self.invalid)

        self.assertEqual(1, code)
        self.assertEqual(1, len(report["resources"]))

        error = report["resources"][0]["errors"][0]
        self.assertEqual("/title", error["path"])
        self.assertEqual("Title", error["title"])  # the schema title, not the property name
        self.assertEqual("type", error["validator"])

    def test_missing_mandatory_field_is_reported_against_the_field(self):
        # jsonschema reports "required" against the object: the field itself is the useful subject
        path = self.write_json("no_title.json", {"uuid": "u-3", "abstract": "a"})
        report, _ = self.report(path)

        errors = report["resources"][0]["errors"]
        self.assertEqual(["/title"], [e["path"] for e in errors])
        self.assertEqual(["not set"], [e["message"] for e in errors])

    def test_empty_optional_field_is_a_schema_defect_not_a_resource_error(self):
        path = self.write_json("no_edition.json", {"uuid": "u-4", "title": "fine", "abstract": "a", "edition": None})
        report, code = self.report(path, include_valid=True)

        # the resource is not to blame: the schema is the one not allowing the null
        self.assertTrue(report["resources"][0]["valid"])
        self.assertEqual(0, code)
        self.assertIn(
            "The metadata schema does not allow a null value on the optional field 'edition', "
            "left empty by 1 resource(s)",
            report["summary"],
        )

    def test_schema_defects_are_not_reported_when_no_instance_runs_into_them(self):
        report, _ = self.report(self.valid, include_valid=True)

        self.assertFalse([message for message in report["summary"] if "optional field" in message])

    def test_max_errors_caps_the_details_but_not_the_count(self):
        path = self.write_json("three.json", {"uuid": 1, "title": "way too long to fit", "edition": 2})
        full, _ = self.report(path)
        capped, _ = self.report(path, max_errors=1)

        self.assertEqual(4, full["resources"][0]["error_count"])  # uuid, title, edition, missing abstract
        self.assertEqual(4, len(full["resources"][0]["errors"]))

        self.assertEqual(4, capped["resources"][0]["error_count"])
        self.assertEqual(1, len(capped["resources"][0]["errors"]))

    def test_long_value_is_not_quoted_back_in_the_message(self):
        path = self.write_json("long.json", {"uuid": "u-5", "title": "x" * 300, "abstract": "a"})
        report, _ = self.report(path)

        error = report["resources"][0]["errors"][0]
        self.assertEqual("too long: 300 chars (max 10)", error["message"])

    def test_json_report_carries_the_summary(self):
        report, _ = self.report(self.invalid)

        self.assertIn("Validated 1 resource(s): 1 invalid, 0 valid", report["summary"])
        self.assertEqual(["summary", "resources"], list(report))

    def test_csv_report_has_one_row_per_error_and_comments_the_summary(self):
        out, _ = self.call(schema_file=self.schema, instance_files=[self.valid, self.invalid], outformat="csv")

        comments = [line for line in out.splitlines() if line.startswith("#")]
        rows = list(csv.DictReader(line for line in out.splitlines() if not line.startswith("#")))

        self.assertIn("# Validated 2 resource(s): 1 invalid, 1 valid", comments)
        self.assertEqual(1, len(rows))  # only the invalid one
        self.assertEqual("/title", rows[0]["error_path"])
        self.assertEqual("Title", rows[0]["error_title"])
        self.assertEqual("u-2", rows[0]["uuid"])

    def test_csv_report_without_details_has_one_row_per_instance(self):
        out, _ = self.call(
            schema_file=self.schema,
            instance_files=[self.valid, self.invalid],
            outformat="csv",
            include_valid=True,
            error_details=False,
        )

        rows = list(csv.DictReader(line for line in out.splitlines() if not line.startswith("#")))
        self.assertEqual(2, len(rows))
        self.assertNotIn("error_path", rows[0])

    def test_report_can_be_written_to_a_file(self):
        outpath = os.path.join(self.tmpdir.name, "report.json")
        self.call(schema_file=self.schema, instance_files=[self.valid], output=outpath, include_valid=True)

        with open(outpath) as infile:
            self.assertEqual(1, len(json.load(infile)["resources"]))

    def test_broken_schema_is_reported_and_flagged_in_the_exit_code(self):
        broken = dict(SCHEMA, properties=dict(SCHEMA["properties"], edition={"maxLength": "not a number"}))
        schema = self.write_json("broken.json", broken)

        out, code = self.call(schema_file=schema, instance_files=[self.valid], include_valid=True)

        self.assertEqual(2, code)  # the instance is valid: only the schema flag is raised
        self.assertTrue([m for m in json.loads(out)["summary"] if "schema itself is not valid" in m])

    def test_broken_schema_and_invalid_instance_combine_in_the_exit_code(self):
        broken = dict(SCHEMA, properties=dict(SCHEMA["properties"], edition={"maxLength": "not a number"}))
        schema = self.write_json("broken.json", broken)

        _, code = self.call(schema_file=schema, instance_files=[self.invalid])

        self.assertEqual(3, code)

    def test_unreadable_file_is_refused(self):
        with self.assertRaises(CommandError):
            self.call(schema_file=self.schema, instance_files=[os.path.join(self.tmpdir.name, "nope.json")])

    def test_instances_and_resource_filters_are_mutually_exclusive(self):
        with self.assertRaises(CommandError):
            self.call(schema_file=self.schema, instance_files=[self.valid], ids=["1"])

        with self.assertRaises(CommandError):
            self.call(schema_file=self.schema, instance_files=[self.valid], resource_types=["dataset"])


class ValidateMetadataResourceTests(ValidateMetadataCommandMixin, TestCase):
    """
    Selection of the stored resources. The schema comes from a file and the instances from a mock,
    so that the assertions are about which resources are picked, not about the metadata of a fixture
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.schema = self.write_json("schema.json", SCHEMA)

        owner = get_user_model().objects.create_user("validate_user", "v@fakemail.com", "pwd")
        self.dataset = ResourceBase.objects.create(
            title="A dataset", uuid=str(uuid4()), resource_type="dataset", owner=owner
        )
        self.document = ResourceBase.objects.create(
            title="A document", uuid=str(uuid4()), resource_type="document", owner=owner
        )

        patcher = patch("geonode.metadata.validation.validator.metadata_manager")
        self.manager = patcher.start()
        self.addCleanup(patcher.stop)
        # every resource yields the same valid instance: what is under test here is the selection
        self.manager.build_schema_instance.side_effect = lambda resource, lang: {
            "uuid": resource.uuid,
            "title": "fine",
            "abstract": "an abstract",
        }

    def reported_ids(self, **options):
        out, _ = self.call(schema_file=self.schema, include_valid=True, **options)
        return [record["id"] for record in json.loads(out)["resources"]]

    def test_all_the_resources_are_validated_by_default(self):
        self.assertEqual([self.dataset.pk, self.document.pk], self.reported_ids())

    def test_filter_by_id(self):
        self.assertEqual([self.document.pk], self.reported_ids(ids=[str(self.document.pk)]))

    def test_filter_by_resource_type(self):
        self.assertEqual([self.dataset.pk], self.reported_ids(resource_types=["dataset"]))

    def test_filters_are_combined(self):
        self.assertEqual([], self.reported_ids(ids=[str(self.dataset.pk)], resource_types=["document"]))

    def test_unknown_id_is_warned_about_and_skipped(self):
        # not assertLogs: setup_logger() drops every handler on this logger, capture included
        with patch.object(validate_metadata.logger, "warning") as warning:
            self.assertEqual([self.dataset.pk], self.reported_ids(ids=[f"{self.dataset.pk},999999"]))

        self.assertIn("Requested resources not found: [999999]", [call.args[0] for call in warning.call_args_list])

    def test_not_an_id_is_refused(self):
        with self.assertRaises(CommandError):
            self.call(schema_file=self.schema, ids=["not-a-number"])

    def test_a_failing_handler_is_reported_against_the_resource(self):
        self.manager.build_schema_instance.side_effect = RuntimeError("handler exploded")

        out, code = self.call(schema_file=self.schema, ids=[str(self.dataset.pk)])
        record = json.loads(out)["resources"][0]

        self.assertEqual(1, code)
        self.assertEqual("geonode:build_schema_instance", record["errors"][0]["validator"])
        self.assertIn("handler exploded", record["errors"][0]["message"])
