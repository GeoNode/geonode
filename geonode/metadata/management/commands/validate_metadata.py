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

BASE_FIELDS = ["id", "uuid", "resource_type", "title", "valid", "error_count"]
ERROR_FIELDS = ["error_path", "error_validator", "error_message", "error_value"]


class Command(BaseCommand):
    help = (
        "Validate the metadata of the GeoNode resources: for each resource the jsonschema "
        "instance is built and validated against the metadata jsonschema."
    )

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

        # iterator() keeps the memory usage bounded: the polymorphic queryset resolves
        # the real instances in chunks, so we never hold the whole catalogue at once
        for resource in queryset.iterator():
            total += 1
            record = self.validate_resource(resource, validator, options["lang"], options["max_errors"])
            if not record["valid"]:
                invalid_count += 1
            if not record["valid"] or options["include_valid"]:
                records.append(record)

        self.write_report(records, options)

        logger.info(f"Validated {total} resource(s): {invalid_count} invalid, {total - invalid_count} valid")

        if invalid_count:
            sys.exit(1)

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
            if count > MAX_SCHEMA_ERRORS:
                logger.warning(f"More than {MAX_SCHEMA_ERRORS} problems in the metadata schema, skipping the rest")
                break
            path = "/" + "/".join(str(item) for item in error.absolute_path)
            logger.warning(f"The metadata schema itself is not valid: {path}: {error.message}")

        self.required_fields = set(schema.get("required", []))

        format_checker = getattr(validator_class, "FORMAT_CHECKER", None) if check_formats else None
        return validator_class(schema, format_checker=format_checker)

    def as_json_types(self, data):
        """
        Render the data down to plain JSON types, the same way the metadata API does before
        sending it to the client.

        Both the schema and the instances are built out of django objects: lazy translations,
        dates, decimals... A lazy translation is not a str instance, so jsonschema would reject
        it as "not of type 'string'" even though the client receives a perfectly good string.
        We want to validate what the client actually gets, not the intermediate python objects.
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
                        "validator": "geonode:build_schema_instance",
                        "message": f"Can not build the schema instance: {e}",
                        "value": None,
                    }
                ],
            )

        # GeoNode injects this key in the instance for testing purposes only (resources titled "*error*")
        instance.pop("extraErrors", None)

        errors = self.drop_redundant(validator.iter_errors(instance))
        errors = sorted(errors, key=lambda err: ([str(p) for p in err.absolute_path], str(err.validator)))
        reported = errors[:max_errors] if max_errors > 0 else errors

        return dict(
            record,
            valid=not errors,
            error_count=len(errors),
            errors=[self.format_error(err) for err in reported],
        )

    def is_unset(self, error):
        return error.validator == "type" and error.instance is None

    def drop_redundant(self, errors):
        """
        An unset field is a null, and a null fails every single keyword declared for that field:
        "type", but also "oneOf", "enum", "format"... They all report the very same problem, so
        we only keep the clearest one.
        """
        errors = list(errors)
        unset_paths = {tuple(error.absolute_path) for error in errors if self.is_unset(error)}

        return [error for error in errors if self.is_unset(error) or tuple(error.absolute_path) not in unset_paths]

    def format_error(self, error):
        path = "/" + "/".join(str(item) for item in error.absolute_path)
        message = error.message

        # For errors sitting at the root (e.g. "required") the offending value is the whole
        # instance: it adds nothing to the message and would be repeated on every single error
        value = None
        if error.absolute_path:
            value = json.dumps(error.instance, ensure_ascii=False, default=str)
            if len(value) > MAX_VALUE_REPR:
                value = f"{value[:MAX_VALUE_REPR]}…"

        # An unset field ends up in the instance as a null, and jsonschema reports it in python
        # terms as "None is not of type 'object'", which reads as a type mismatch while it only
        # means "the field is empty". Spell it out, and drop the pointless null value.
        if self.is_unset(error):
            # Whether the field was mandatory is what tells a curator (mandatory field left empty)
            # from a schema glitch (optional field whose type does not allow the null it gets)
            if len(error.absolute_path) == 1:
                kind = "required" if error.absolute_path[0] in self.required_fields else "optional"
                message = f"not set ({kind} field)"
            else:
                expected = error.validator_value
                expected = expected if isinstance(expected, list) else [expected]
                message = f"not set (expected {' or '.join(expected)})"
            value = None

        # jsonschema quotes the whole offending string in the message ("'xxxxx…' is too long"),
        # which is exactly the value we are careful to truncate in the value column
        elif error.validator == "maxLength":
            message = f"too long: {len(error.instance)} chars (max {error.validator_value})"

        return {
            "path": path,
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
            json.dump(records, out, indent=2, ensure_ascii=False, default=str)
            out.write("\n")
        else:
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
                        error_validator=error["validator"],
                        error_message=error["message"],
                        error_value=error["value"],
                    )
                )
