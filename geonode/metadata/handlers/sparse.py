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
import copy
import json
import logging

from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.exceptions import UnsetFieldException
from geonode.metadata.models import SparseField

logger = logging.getLogger(__name__)


CONTEXT_ID = "sparse"


class SparseFieldRegistry:

    sparse_fields = {}

    def register(self, field_name: str, schema: dict, after: str = None, init_func=None):
        self.sparse_fields[field_name] = {"schema": schema, "after": after, "init_func": init_func}

    def fields(self):
        return self.sparse_fields


sparse_field_registry = SparseFieldRegistry()


class SparseHandler(MetadataHandler):
    """
    Handles sparse in fields in the SparseField table
    """

    def _recurse_localization(self, context, schema, lang, field_name=None):
        self._localize_subschema_labels(context, schema, lang, field_name)

        match schema["type"]:
            case "object":
                for prop_name, subschema in schema["properties"].items():
                    self._recurse_localization(context, subschema, lang, prop_name)
            case "array":
                self._recurse_localization(context, schema["items"], lang, None)
            case _:
                pass

    def update_schema(self, jsonschema, context, lang=None):
        # add all registered fields
        for field_name, field_info in sparse_field_registry.fields().items():
            subschema = copy.deepcopy(field_info["schema"])
            self._recurse_localization(context, subschema, lang, field_name)
            self._add_subschema(jsonschema, field_name, subschema, after_what=field_info["after"])

            # add the handler info to the dictionary if it doesn't exist
            if "geonode:handler" not in subschema:
                subschema.update({"geonode:handler": "sparse"})

            # # perform further specific initializations
            # if init_func := field_info["init_func"]:
            #     logger.debug(f"Running init for sparse field {field_name}")
            #     init_func(field_name, subschema, lang)

        return jsonschema

    def load_serialization_context(self, resource, jsonschema: dict, context: dict):
        logger.debug(f"Preloading sparse fields {sparse_field_registry.fields().keys()}")
        context[CONTEXT_ID] = {
            "fields": {
                f.name: f.value for f in SparseField.get_fields(resource, names=sparse_field_registry.fields().keys())
            },
            "schema": jsonschema,
        }

    @staticmethod
    def get_sparse_field(context, fieldname):
        return context[CONTEXT_ID]["fields"].get(fieldname, None)

    @staticmethod
    def set_sparse_field(context, fieldname, value):
        context[CONTEXT_ID]["fields"][fieldname] = value

    @staticmethod
    def _check_type(declared, checked):
        return declared == checked or (type(declared) is list and checked in declared)

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        field_type = context[CONTEXT_ID]["schema"]["properties"][field_name]["type"]
        field_value = context[CONTEXT_ID]["fields"].get(field_name, None)

        is_nullable = self._check_type(field_type, "null")

        if field_name not in context[CONTEXT_ID]["fields"] and not is_nullable:
            raise UnsetFieldException()

        if is_nullable and field_value is None:
            return None

        if self._check_type(field_type, "string"):
            return field_value
        elif self._check_type(field_type, "number"):
            try:
                return float(field_value)
            except Exception as e:
                logger.warning(
                    f"Error loading NUMBER field '{field_name}' with content ({type(field_value)}){field_value}: {e}"
                )
                raise UnsetFieldException()  # should be a different exception
        elif self._check_type(field_type, "integer"):
            try:
                return int(field_value)
            except Exception as e:
                logger.warning(
                    f"Error loading INTEGER field '{field_name}' with content ({type(field_value)}){field_value}: {e}"
                )
                raise UnsetFieldException()  # should be a different exception
        elif field_type == "array":
            # assuming it's a single level array: TODO implement other cases
            try:
                return json.loads(field_value) if field_value is not None else None
            except Exception as e:
                logger.warning(
                    f"Error loading field '{field_name}' with content ({type(field_value)}){field_value}: {e}"
                )
        elif field_type == "object":
            # assuming it's a single level object: TODO implement other cases
            try:
                return json.loads(field_value) if field_value is not None else None
            except Exception as e:
                logger.warning(
                    f"Error loading field '{field_name}' with content ({type(field_value)}){field_value}: {e}"
                )
        else:
            logger.warning(f"Unhandled type '{field_type}' for sparse field '{field_name}'")
            return None

    def load_deserialization_context(self, resource, jsonschema: dict, context: dict):
        context[CONTEXT_ID] = {"schema": jsonschema}

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):

        bare_value = json_instance.get(field_name, None)
        field_type = context[CONTEXT_ID]["schema"]["properties"][field_name]["type"]

        is_nullable = self._check_type(field_type, "null")

        if self._check_type(field_type, "string"):
            field_value = bare_value
        elif self._check_type(field_type, "number"):
            try:
                field_value = str(float(bare_value)) if bare_value is not None else None
            except ValueError as e:
                logger.warning(f"Error parsing sparse field '{field_name}'::'{field_type}'='{bare_value}': {e}")
                self._set_error(
                    errors,
                    [field_name],
                    self.localize_message(
                        context,
                        "metadata_sparse_error_parse",
                        {"fieldname": field_name, "type": "number", "value": bare_value},
                    ),
                )

                return
        elif self._check_type(field_type, "integer"):
            try:
                field_value = str(int(bare_value)) if bare_value is not None else None
            except ValueError as e:
                logger.warning(f"Error parsing sparse field '{field_name}'::'{field_type}'='{bare_value}': {e}")
                self._set_error(
                    errors,
                    [field_name],
                    self.localize_message(
                        context,
                        "metadata_sparse_error_parse",
                        {"fieldname": field_name, "type": "integer", "value": bare_value},
                    ),
                )

                return
        elif field_type == "array":
            field_value = json.dumps(bare_value) if bare_value is not None else "[]"
        elif field_type == "object":
            field_value = json.dumps(bare_value) if bare_value is not None else "{}"
        else:
            logger.warning(f"Unhandled type '{field_type}' for sparse field '{field_name}'")
            self._set_error(
                errors,
                [field_name],
                self.localize_message(
                    context, "metadata_sparse_error_type", {"fieldname": field_name, "type": field_type}
                ),
            )
            return

        try:
            if field_value is not None:
                SparseField.objects.update_or_create(
                    defaults={"value": field_value}, resource=resource, name=field_name
                )
            elif is_nullable:
                SparseField.objects.filter(resource=resource, name=field_name).delete()
            else:
                self._set_error(
                    errors,
                    [field_name],
                    self.localize_message(context, "metadata_error_empty_field", {"fieldname": field_name}),
                )
                logger.debug(f"Not setting null value for {field_name}")
        except Exception as e:
            logger.warning(f"Error setting field {field_name}={field_value}: {e}")
            self._set_error(
                errors,
                [field_name],
                self.localize_message(context, "metadata_error_store", {"fieldname": field_name, "exc": e}),
            )
