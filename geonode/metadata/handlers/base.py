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
from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import JSONSCHEMA_BASE
from geonode.base.enumerations import ALL_LANGUAGES
from django.utils.translation import gettext as _


logger = logging.getLogger(__name__)


class BaseHandler(MetadataHandler):
    """
    The base handler builds a valid empty schema with the simple
    fields of the ResourceBase model
    """

    def __init__(self):
        self.json_base_schema = JSONSCHEMA_BASE
        self.base_schema = None

    def update_schema(self, jsonschema, lang=None):
        def localize(subschema: dict, annotation_name):
            if annotation_name in subschema:
                subschema[annotation_name] = _(subschema[annotation_name])

        with open(self.json_base_schema) as f:
            self.base_schema = json.load(f)
        # building the full base schema
        for subschema_name, subschema_def in self.base_schema.items():
            localize(subschema_def, 'title')
            localize(subschema_def, 'abstract')

            jsonschema["properties"][subschema_name] = subschema_def

            # add the base handler identity to the dictionary if it doesn't exist
            if "geonode:handler" not in subschema_def:
                subschema_def.update({"geonode:handler": "base"})

            # build the language choices
            if subschema_name == "language":
                subschema_def["oneOf"] = []
                for key, val in dict(ALL_LANGUAGES).items():
                    langChoice = {
                        "const": key,
                        "title": val
                    }
                    subschema_def["oneOf"].append(langChoice)

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str):

        field_value = getattr(resource, field_name)

        return field_value

    def update_resource(self, resource: ResourceBase, field_name: str, content: dict, json_instance: dict):
       
        if field_name in content:
            # insert the content value to the corresponding field_name
            setattr(resource, field_name, content[field_name])

    def load_context(self, resource: ResourceBase, context: dict):

        pass
