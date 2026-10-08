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

import json
import logging
import sys

from django.core.management.base import BaseCommand, CommandError

from geonode.base.management import command_utils
from geonode.base.models import ResourceBase
from geonode.metadata.validation import MetadataValidator
from geonode.metadata.validation.reporting import write_report

logger = logging.getLogger(__name__)

# Exit codes, combined: a run with both problems exits with 3
EXIT_INVALID_RESOURCES = 1
EXIT_INVALID_SCHEMA = 2


class Command(BaseCommand):
    help = (
        "Validate the metadata of the GeoNode resources: the jsonschema instance of each resource "
        "is built and validated against the metadata jsonschema. Empty fields are only reported "
        "when mandatory, and only at top level: within a nested object every unset field is reported. "
        "Exits with 1 if any resource is invalid, 2 if the schema itself is, 3 if both"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary = []  # the lines to be repeated in the report

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            dest="ids",
            nargs="+",
            default=None,
            help="Only validate these resource ids (space and/or comma separated)",
        )

        parser.add_argument(
            "--resource-type",
            dest="resource_types",
            nargs="+",
            default=None,
            help="Only validate these resource types, e.g. dataset map document " "(space and/or comma separated)",
        )

        parser.add_argument(
            "--lang",
            default=None,
            help="Language used to build the schema and the schema instances (default: schema default)",
        )

        parser.add_argument(
            "--include-valid",
            action="store_true",
            help="Also report the resources that validate successfully (default: only the invalid ones)",
        )

        parser.add_argument(
            "--no-error-details",
            dest="error_details",
            action="store_false",
            default=True,
            help="Only report the number of errors, without the details of each single error",
        )

        parser.add_argument(
            "--max-errors",
            type=int,
            default=0,
            help="Max number of errors reported per resource; 0 (default) means no limit. "
            "The error count is not affected by this limit",
        )

        parser.add_argument(
            "--check-formats",
            action="store_true",
            help='Also enforce the jsonschema "format" keyword (needs the jsonschema format extra installed)',
        )

        parser.add_argument(
            "--format",
            dest="outformat",
            default="json",
            choices=["json", "csv"],
            help="Output format (default: json)",
        )

        parser.add_argument(
            "--output",
            default=None,
            help="Write the report to this file (default: stdout)",
        )

        parser.add_argument(
            "--schema",
            dest="schema_file",
            default=None,
            help="Read the jsonschema from this file instead of building it through the metadata manager",
        )

        parser.add_argument(
            "--instance",
            dest="instance_files",
            nargs="+",
            default=None,
            help="Validate the jsonschema instances read from these files, one instance per file, "
            "instead of the stored resources. Not compatible with --id and --resource-type",
        )

        parser.add_argument("--debug", dest="debug", action="store_true", help="Set log level to debug")

    def handle(self, *args, **options):
        log_level = logging.DEBUG if options.get("debug") else logging.INFO
        command_utils.setup_logger(logger_name=logger.name, level=log_level)

        if options["instance_files"] and (options["ids"] or options["resource_types"]):
            raise CommandError("--instance selects the instances by itself: --id and --resource-type do not apply")

        validator = self.build_validator(options)

        records = []
        total = 0
        invalid_count = 0

        for record in self.validate_all(validator, options):
            total += 1
            if not record["valid"]:
                invalid_count += 1
            if not record["valid"] or options["include_valid"]:
                records.append(record)

        self.report_schema_defects(validator)
        self.notify(
            f"Validated {total} resource(s): {invalid_count} invalid, {total - invalid_count} valid", logging.INFO
        )

        self.write_report(records, options)

        exit_code = (EXIT_INVALID_RESOURCES if invalid_count else 0) | (
            EXIT_INVALID_SCHEMA if validator.schema_errors else 0
        )
        if exit_code:
            sys.exit(exit_code)

    # -------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------
    def build_validator(self, options):
        try:
            validator = MetadataValidator(
                lang=options["lang"],
                check_formats=options["check_formats"],
                schema=self.read_json(options["schema_file"]) if options["schema_file"] else None,
            )
        except ImportError as e:
            raise CommandError(str(e))

        for message in validator.schema_errors:
            self.notify(message)

        return validator

    def read_json(self, path):
        try:
            with open(path, encoding="utf-8") as infile:
                return json.load(infile)
        except (OSError, ValueError) as e:
            raise CommandError(f"Can not read the JSON file '{path}': {e}")

    def select_resources(self, ids, resource_types):
        queryset = ResourceBase.objects.all()

        if ids:
            requested_ids = self.parse_list(ids, as_int=True)
            queryset = queryset.filter(pk__in=requested_ids)
            found_ids = set(queryset.values_list("pk", flat=True))
            if missing := set(requested_ids) - found_ids:
                logger.warning(f"Requested resources not found: {sorted(missing)}")

        if resource_types:
            queryset = queryset.filter(resource_type__in=self.parse_list(resource_types))

        return queryset.order_by("pk")

    def parse_list(self, values, as_int=False):
        parsed = []
        for value in values:
            for item in str(value).split(","):
                item = item.strip()
                if not item:
                    continue
                if as_int:
                    try:
                        item = int(item)
                    except ValueError:
                        raise CommandError(f"Not a valid resource id: '{item}'")
                parsed.append(item)
        return parsed

    # -------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------
    def validate_all(self, validator, options):
        """Yield a record per entry, reading them from the given files or from the stored resources"""
        if options["instance_files"]:
            logger.info(f"Validating {len(options['instance_files'])} instance file(s)")
            for path in options["instance_files"]:
                yield self.validate_file(path, validator, options["max_errors"])
            return

        queryset = self.select_resources(options["ids"], options["resource_types"])
        logger.info(f"Validating {queryset.count()} resource(s)")

        # Non polymorphic, exactly like the API read path: we validate what the client is served.
        # iterator() keeps the resources out of memory; the records being reported are not
        for resource in queryset.iterator():
            yield validator.validate_resource(resource, options["max_errors"])

    def validate_file(self, path, validator, max_errors):
        instance = self.read_json(path)
        record = {
            "id": path,
            "uuid": instance.get("uuid"),
            "resource_type": None,  # not part of the schema
            "title": instance.get("title"),
        }
        return validator.validate_instance(record, instance, max_errors)

    # -------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------
    def notify(self, message, level=logging.WARNING):
        # Logged, and repeated in the report: the report file is meant to travel on its own
        logger.log(level, message)
        self.summary.append(message)

    def report_schema_defects(self, validator):
        # Only what some resource really ran into: a null never handed over is nobody's problem
        for field, count in sorted(validator.observed_defects.items()):
            self.notify(
                f"The metadata schema does not allow a null value on the optional field "
                f"'{field}', left empty by {count} resource(s)"
            )

    def write_report(self, records, options):
        outpath = options["output"]

        if outpath:
            try:
                with open(outpath, "w", newline="", encoding="utf-8") as out:
                    write_report(self.summary, records, out, options["outformat"], options["error_details"])
            except OSError as e:
                raise CommandError(f"Can not write the report to '{outpath}': {e}")
            logger.info(f"Report written to {outpath}")
        else:
            # OutputWrapper appends a newline to every write() call, which would break the report
            self.stdout.ending = ""
            write_report(self.summary, records, self.stdout, options["outformat"], options["error_details"])
