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


logger = logging.getLogger(__name__)


class LoaderHandler(MetadataHandler):
    """
    This handler simply loads a json file and adds fields from it.
    """

    def __init__(self, **kwargs):
        self.schema_file = kwargs.get("schemafile")
        self.base_schema = None

    def update_schema(self, jsonschema, context, lang=None):

        if not self.base_schema:
            with open(self.schema_file) as f:
                self.base_schema = json.load(f)

        for property_name, subschema in self.base_schema.items():
            self._add_subschema(jsonschema, property_name, subschema)

            if "geonode:handler" not in subschema:
                raise KeyError(f"Missing schema handler for property {property_name}")

        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        raise KeyError(f"Unexpected get request for field {field_name}")

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        raise KeyError(f"Unexpected update request for field {field_name}")


class FakeHandler(MetadataHandler):
    """
    This handler
    - does not add any subschema
    - swallow any update request
    - create fake string values for instances
    """

    def update_schema(self, jsonschema, context, lang=None):
        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        return f"{field_name}_fake"

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        pass
