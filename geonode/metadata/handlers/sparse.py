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
import json
import logging

from geonode.metadata.handlers.abstract import MetadataHandler
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

    def update_schema(self, jsonschema, context, lang=None):
        # add all registered fields

        # TODO: manage i18n (thesaurus?)
        for field_name, field_info in sparse_field_registry.fields().items():
            subschema = field_info["schema"]

            self._localize_subschema_label(context, subschema, lang, "title")
            self._localize_subschema_label(context, subschema, lang, "description")

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

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        field_type = context[CONTEXT_ID]["schema"]["properties"][field_name]["type"]
        match field_type:
            case "string":
                return context[CONTEXT_ID]["fields"].get(field_name, None)
            case "array":
                # assuming it's an array of string: TODO implement other cases
                try:
                    arr = context[CONTEXT_ID]["fields"].get(field_name, None) or "[]"
                    return json.loads(arr)
                except Exception as e:
                    logger.warning(f"Error loading field '{field_name}' with content ({type(arr)}){arr}: {e}")
            case _:
                logger.warning(f"Unhandled type '{field_type}' for sparse field '{field_name}'")
                return None

    def load_deserialization_context(self, resource, jsonschema: dict, context: dict):
        context[CONTEXT_ID] = {"schema": jsonschema}

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        bare_value = json_instance.get(field_name, None)
        type = context[CONTEXT_ID]["schema"]["properties"][field_name]["type"]
        match type:
            case "string":
                field_value = bare_value
            case "array":
                field_value = json.dumps(bare_value) if bare_value else []
            case _:
                logger.warning(f"Unhandled type '{type}' for sparse field '{field_name}'")
                self._set_error(errors, [field_name], f"Unhandled type {type}. Contact your administrator")
                return

        try:
            sf, created = SparseField.objects.update_or_create(
                defaults={"value": field_value}, resource=resource, name=field_name
            )
        except Exception as e:
            logger.warning(f"Error setting field {field_name}={field_value}: {e}")
            self._set_error(errors, [field_name], f"Error setting value: {e}")
