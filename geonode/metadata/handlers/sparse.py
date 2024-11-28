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

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.models import SparseField

logger = logging.getLogger(__name__)


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

    def update_schema(self, jsonschema, lang=None):
        # building the full base schema

        # TODO: manage i18n (thesaurus?)

        for field_name, field_info in sparse_field_registry.fields().items():
            subschema = field_info["schema"]
            if after := field_info["after"]:
                self._add_after(jsonschema, after, field_name, subschema)
            else:
                jsonschema["properties"][field_name] = subschema

            # add the handler info to the dictionary if it doesn't exist
            if "geonode:handler" not in subschema:
                subschema.update({"geonode:handler": "sparse"})

            # # perform further specific initializations
            # if init_func := field_info["init_func"]:
            #     logger.debug(f"Running init for sparse field {field_name}")
            #     init_func(field_name, subschema, lang)

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str, context, lang: str = None):
        # TODO: reading fields one by one may kill performance. We may want the manager to perform a loadcontext as a first call
        # before looping on the get_jsonschema_instance calls
        field = SparseField.objects.filter(resource=resource, name=field_name).first()
        return field.value if field else None

    def update_resource(self, resource: ResourceBase, field_name: str, json_instance: dict, errors: list, **kwargs):
        field_value = json_instance.get(field_name, None)
        try:
            sf, created = SparseField.objects.update_or_create(
                defaults={"value": field_value}, resource=resource, name=field_name
            )
        except Exception as e:
            logger.warning(f"Error setting field {field_name}={field_value}: {e}")
            self._set_error(errors, ["field_name"], f"Error setting value: {e}")
