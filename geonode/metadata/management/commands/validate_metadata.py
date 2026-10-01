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
import logging
import sys

from django.core.management.base import BaseCommand, CommandError
from rest_framework.utils.encoders import JSONEncoder

from geonode.base.management import command_utils
from geonode.base.models import ResourceBase
from geonode.metadata.manager import metadata_manager

logger = logging.getLogger(__name__)

# Max length of the offending instance value reported along with an error
MAX_VALUE_REPR = 200

# Max number of problems reported for the schema itself
MAX_SCHEMA_ERRORS = 20

# Exit codes, combined: a run with both problems exits with 3
EXIT_INVALID_RESOURCES = 1
EXIT_INVALID_SCHEMA = 2


BASE_FIELDS = ["id", "uuid", "resource_type", "title", "valid", "error_count"]
ERROR_FIELDS = ["error_path", "error_title", "error_validator", "error_message", "error_value"]


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
        self.schema_errors = 0

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

        parser.add_argument("--debug", dest="debug", action="store_true", help="Set log level to debug")

    def handle(self, *args, **options):
        log_level = logging.DEBUG if options.get("debug") else logging.INFO
        command_utils.setup_logger(logger_name=logger.name, level=log_level)

        validator = self.build_validator(options["lang"], options["check_formats"])

        queryset = self.select_resources(options["ids"], options["resource_types"])
        logger.info(f"Validating {queryset.count()} resource(s)")

        records = []
        total = 0
        invalid_count = 0

        # iterator() resolves the polymorphic instances in chunks, so the resources are never all
        # in memory at once. The records being reported are, at some 2kB each
        for resource in queryset.iterator():
            total += 1
            record = self.validate_resource(resource, validator, options["lang"], options["max_errors"])
            if not record["valid"]:
                invalid_count += 1
            if not record["valid"] or options["include_valid"]:
                records.append(record)

        self.report_schema_defects()
        self.notify(
            f"Validated {total} resource(s): {invalid_count} invalid, {total - invalid_count} valid", logging.INFO
        )

        self.write_report(records, options)

        exit_code = (EXIT_INVALID_RESOURCES if invalid_count else 0) | (
            EXIT_INVALID_SCHEMA if self.schema_errors else 0
        )
        if exit_code:
            sys.exit(exit_code)

    # -------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------
    def build_validator(self, lang, check_formats):
        try:
            from jsonschema import validators as js_validators
        except ImportError:
            raise CommandError("The 'jsonschema' package is needed by this command. Please install it")

        schema = self.as_json_types(metadata_manager.get_schema(lang))
        validator_class = js_validators.validator_for(schema)
        logger.debug(f"Using validator {validator_class.__name__}")

        # A broken schema is worth reporting, but the resources may still be validated against it.
        # check_schema() would raise on the first problem only: we want to see them all at once
        metaschema_validator = js_validators.validator_for(validator_class.META_SCHEMA, default=validator_class)
        for count, error in enumerate(metaschema_validator(validator_class.META_SCHEMA).iter_errors(schema), 1):
            self.schema_errors += 1
            if count > MAX_SCHEMA_ERRORS:
                self.notify(f"More than {MAX_SCHEMA_ERRORS} problems in the metadata schema, skipping the rest")
                break
            path = "/" + "/".join(str(item) for item in error.absolute_path)
            self.notify(f"The metadata schema itself is not valid: {path}: {error.message}")

        self.schema = schema
        self.required_fields = set(schema.get("required", []))

        # Optional fields not accepting the null they get when left empty: a defect of the schema,
        # reported once at the end of the run rather than against every resource.
        # Probed with an actual null: a "oneOf" or an "enum" may reject it as well as "type" does
        self.broken_optionals = {
            name
            for name, subschema in schema.get("properties", {}).items()
            if name not in self.required_fields and not validator_class(subschema).is_valid(None)
        }
        self.observed_defects = {}

        format_checker = getattr(validator_class, "FORMAT_CHECKER", None) if check_formats else None
        return validator_class(schema, format_checker=format_checker)

    def as_json_types(self, data):
        """
        Render the data down to plain JSON types, as the API does before sending it to the client:
        a lazy translation is not a str, and jsonschema would reject it as "not of type 'string'"
        """
        return json.loads(json.dumps(data, cls=JSONEncoder))

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
    def validate_resource(self, resource, validator, lang, max_errors):
        record = {
            "id": resource.pk,
            "uuid": resource.uuid,
            "resource_type": resource.resource_type,
            "title": resource.title,
        }
        logger.debug(f"Validating resource {resource.pk}: '{resource.title}'")

        try:
            instance = metadata_manager.build_schema_instance(resource, lang)
            instance = self.as_json_types(instance)
        except Exception as e:
            logger.error(f"Can not build the schema instance for resource {resource.pk}", exc_info=e)
            return dict(
                record,
                valid=False,
                error_count=1,
                errors=[
                    {
                        "path": "/",
                        "title": "",
                        "validator": "geonode:build_schema_instance",
                        "message": f"Can not build the schema instance: {e}",
                        "value": None,
                    }
                ],
            )

        # GeoNode injects this key in the instance for testing purposes only (resources titled "*error*")
        instance.pop("extraErrors", None)

        errors = self.drop_redundant(validator.iter_errors(instance))
        errors = [error for error in errors if not self.is_schema_defect(error)]
        errors = sorted(errors, key=lambda err: ([str(p) for p in err.absolute_path], str(err.validator)))
        reported = errors[:max_errors] if max_errors > 0 else errors

        return dict(
            record,
            valid=not errors,
            error_count=len(errors),
            errors=[self.format_error(err) for err in reported],
        )

    def is_unset(self, error):
        # Keyed on the value: depending on the subschema a null may trip "type", "oneOf", or both
        return error.instance is None

    def is_schema_defect(self, error):
        # An optional field left empty: blame the schema, not the resource
        if not (self.is_unset(error) and len(error.absolute_path) == 1):
            return False

        field = error.absolute_path[0]
        if field not in self.broken_optionals:
            return False

        self.observed_defects[field] = self.observed_defects.get(field, 0) + 1
        return True

    def notify(self, message, level=logging.WARNING):
        # Logged, and repeated in the report: the report file is meant to travel on its own
        logger.log(level, message)
        self.summary.append(message)

    def report_schema_defects(self):
        # Only what some resource really ran into: a null never handed over is nobody's problem
        for field, count in sorted(self.observed_defects.items()):
            self.notify(
                f"The metadata schema does not allow a null value on the optional field "
                f"'{field}', left empty by {count} resource(s)"
            )

    def drop_redundant(self, errors):
        """
        A null fails every keyword declared for the field, all reporting the same problem: keep
        one error per unset field, preferring "type" since it names the expected types
        """
        errors = list(errors)
        unset_paths = {tuple(error.absolute_path) for error in errors if self.is_unset(error)}

        kept = [error for error in errors if tuple(error.absolute_path) not in unset_paths]

        for path in unset_paths:
            at_path = [error for error in errors if tuple(error.absolute_path) == path]
            kept.append(next((e for e in at_path if e.validator == "type"), at_path[0]))

        return kept

    def path_title(self, path):
        # The property names are ids: walk the schema alongside the path to pick up their titles
        titles = []
        subschema = self.schema
        for item in path:
            if isinstance(item, int):
                subschema = subschema.get("items", {})
                titles.append(f"[{item}]")
            else:
                subschema = subschema.get("properties", {}).get(item, {})
                titles.append(subschema.get("title", item))
        return "/".join(titles)

    def missing_property(self, error):
        # jsonschema names the missing property in the message only, and does not add it to the
        # path: match the message back to the required list, so a reworded one just yields nothing
        if error.validator != "required":
            return None
        return next((p for p in error.validator_value if f"{p!r} is a required property" == error.message), None)

    def format_error(self, error):
        path = tuple(error.absolute_path)
        message = error.message

        # A missing property is reported against the object holding it: point at the property
        missing = self.missing_property(error)
        if missing is not None:
            path += (missing,)

        # The instance behind a container error is the container itself: useless noise
        value = None
        if path and missing is None:
            value = json.dumps(error.instance, ensure_ascii=False, default=str)
            if len(value) > MAX_VALUE_REPR:
                value = f"{value[:MAX_VALUE_REPR]}…"

        # A top level field only gets reported when mandatory, no point in repeating it. Deeper
        # down nothing is filtered, so there it is worth telling a mandatory field from the rest
        if missing is not None:
            message = "not set" if len(path) == 1 else "not set (required field)"

        # jsonschema puts it in python terms ("None is not of type 'object'"), reading as a type
        # mismatch where the field is simply empty. Spell it out, and drop the pointless null
        elif self.is_unset(error):
            if len(path) > 1 and error.validator == "type":
                expected = error.validator_value
                expected = expected if isinstance(expected, list) else [expected]
                message = f"not set (expected {' or '.join(expected)})"
            else:
                message = "not set"
            value = None

        # jsonschema quotes the whole offending string in the message ("'xxxxx…' is too long"),
        # which is exactly the value we are careful to truncate in the value column
        elif error.validator == "maxLength":
            message = f"too long: {len(error.instance)} chars (max {error.validator_value})"

        return {
            "path": "/" + "/".join(str(item) for item in path),
            "title": self.path_title(path),
            "validator": str(error.validator),
            "message": message,
            "value": value,
        }

    # -------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------
    def write_report(self, records, options):
        outpath = options["output"]

        if outpath:
            try:
                with open(outpath, "w", newline="", encoding="utf-8") as out:
                    self.dump(records, out, options)
            except OSError as e:
                raise CommandError(f"Can not write the report to '{outpath}': {e}")
            logger.info(f"Report written to {outpath}")
        else:
            # OutputWrapper appends a newline to every write() call, which would break the report
            self.stdout.ending = ""
            self.dump(records, self.stdout, options)

    def dump(self, records, out, options):
        if not options["error_details"]:
            records = [{k: v for k, v in record.items() if k != "errors"} for record in records]

        if options["outformat"] == "json":
            json.dump({"summary": self.summary, "resources": records}, out, indent=2, ensure_ascii=False, default=str)
            out.write("\n")
        else:
            # CSV has no comment syntax: "#" is only a widespread convention
            for message in self.summary:
                out.write(f"# {message}\n")
            self.dump_csv(records, out, options["error_details"])

    def dump_csv(self, records, out, error_details):
        fields = BASE_FIELDS + (ERROR_FIELDS if error_details else [])
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()

        for record in records:
            if not error_details or not record["errors"]:
                writer.writerow(record)
                continue

            # one row per error, the resource columns are repeated
            for error in record["errors"]:
                writer.writerow(
                    dict(
                        record,
                        error_path=error["path"],
                        error_title=error["title"],
                        error_validator=error["validator"],
                        error_message=error["message"],
                        error_value=error["value"],
                    )
                )
