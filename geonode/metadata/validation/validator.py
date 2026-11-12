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

from rest_framework.utils.encoders import JSONEncoder

from geonode.metadata.manager import metadata_manager

logger = logging.getLogger(__name__)

# Max length of the offending instance value reported along with an error
MAX_VALUE_REPR = 200

# Max number of problems reported for the schema itself
MAX_SCHEMA_ERRORS = 20


class MetadataValidator:
    """
    Validate the metadata of the resources against the metadata jsonschema.

    A record is returned per resource, holding the resource identification, whether it is valid,
    how many errors it has and the details of each of them.

    Two kinds of problem are not the resource's fault and are kept apart from its errors:
    `schema_errors` lists what is wrong in the schema itself, and `observed_defects` counts, per
    field, the optional fields the schema refuses to leave empty. Both are returned as data, for
    the caller to word as it sees fit.
    """

    def __init__(self, lang=None, check_formats=False, schema=None):
        try:
            from jsonschema import validators as js_validators
        except ImportError:
            raise ImportError("The 'jsonschema' package is needed to validate the metadata. Please install it")

        # A schema handed over by the caller is plain JSON already: nothing to render down
        self.lang = lang
        self.schema = schema if schema is not None else self.as_json_types(metadata_manager.get_schema(lang))

        validator_class = js_validators.validator_for(self.schema)
        logger.debug(f"Using validator {validator_class.__name__}")

        self.schema_errors = self._check_schema(js_validators, validator_class)

        # A schema reported as invalid above may hold anything in place of a keyword: nothing
        # derived from it can be taken on trust, starting with the shape of these two
        required = self.schema.get("required", [])
        self.required_fields = set(required) if isinstance(required, list) else set()
        properties = self.schema.get("properties", {})

        # Optional fields not accepting the null they get when left empty: a defect of the schema,
        # to be kept out of the resource errors and counted here.
        # Probed with an actual null: a "oneOf" or an "enum" may reject it as well as "type" does
        self.broken_optionals = {
            name
            for name, subschema in (properties.items() if isinstance(properties, dict) else ())
            if name not in self.required_fields and self._rejects_null(validator_class, subschema)
        }
        self.observed_defects = {}

        format_checker = getattr(validator_class, "FORMAT_CHECKER", None) if check_formats else None
        self.validator = validator_class(self.schema, format_checker=format_checker)

    # -------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------
    def _check_schema(self, js_validators, validator_class):
        """
        Return the problems of the schema itself. A broken schema is worth reporting, but the
        resources may still be validated against it: check_schema() would raise on the first
        problem only, and we want to see them all at once
        """
        metaschema_validator = js_validators.validator_for(validator_class.META_SCHEMA, default=validator_class)

        problems = []
        for count, error in enumerate(metaschema_validator(validator_class.META_SCHEMA).iter_errors(self.schema), 1):
            if count > MAX_SCHEMA_ERRORS:
                problems.append(f"More than {MAX_SCHEMA_ERRORS} problems in the metadata schema, skipping the rest")
                break
            path = "/" + "/".join(str(item) for item in error.absolute_path)
            problems.append(f"The metadata schema itself is not valid: {path}: {error.message}")
        return problems

    def _rejects_null(self, validator_class, subschema):
        try:
            return not validator_class(subschema).is_valid(None)
        except Exception:  # a malformed subschema: the metaschema check has reported it already
            return False

    @staticmethod
    def as_json_types(data):
        """
        Render the data down to plain JSON types, as the API does before sending it to the client:
        a lazy translation is not a str, and jsonschema would reject it as "not of type 'string'"
        """
        return json.loads(json.dumps(data, cls=JSONEncoder))

    # -------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------
    def validate_resource(self, resource, max_errors=0):
        record = {
            "id": resource.pk,
            "uuid": resource.uuid,
            "resource_type": resource.resource_type,
            "title": resource.title,
        }
        logger.debug(f"Validating resource {resource.pk}: '{resource.title}'")

        try:
            instance = metadata_manager.build_schema_instance(resource, self.lang)
            instance = self.as_json_types(instance)
        except Exception as e:
            logger.error(f"Can not build the schema instance for resource {resource.pk}", exc_info=e)
            return self._failed(record, "geonode:build_schema_instance", f"Can not build the schema instance: {e}")

        return self.validate_instance(record, instance, max_errors)

    def validate_instance(self, record, instance, max_errors=0):
        # GeoNode injects this key in the instance for testing purposes only (resources titled "*error*")
        instance.pop("extraErrors", None)

        try:
            errors = self.drop_redundant(self.validator.iter_errors(instance))
        except Exception as e:
            # A keyword the metaschema has already refused can blow up on a value of the right type
            logger.error(f"Can not validate {record['id']} against the schema", exc_info=e)
            return self._failed(record, "geonode:invalid_schema", f"Can not validate against the schema: {e}")

        errors = [error for error in errors if not self.is_schema_defect(error)]
        errors = sorted(errors, key=lambda err: ([str(p) for p in err.absolute_path], str(err.validator)))
        reported = errors[:max_errors] if max_errors > 0 else errors

        return dict(
            record,
            valid=not errors,
            error_count=len(errors),
            errors=[self.format_error(err) for err in reported],
        )

    @staticmethod
    def _failed(record, validator, message):
        return dict(
            record,
            valid=False,
            error_count=1,
            errors=[{"path": "/", "title": "", "validator": validator, "message": message, "value": None}],
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

    # -------------------------------------------------------------------
    # Error rendering
    # -------------------------------------------------------------------
    def path_title(self, path):
        # The property names are ids: walk the schema alongside the path to pick up their titles
        titles = []
        subschema = self.schema
        for item in path:
            # A malformed schema may hold anything in place of a subschema: fall back to the names
            if isinstance(item, int):
                subschema = self.as_dict(subschema).get("items")
                titles.append(f"[{item}]")
            else:
                subschema = self.as_dict(self.as_dict(subschema).get("properties")).get(item)
                titles.append(self.as_dict(subschema).get("title", item))
        return "/".join(titles)

    @staticmethod
    def as_dict(value):
        return value if isinstance(value, dict) else {}

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
