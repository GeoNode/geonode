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
from abc import ABCMeta, abstractmethod
from geonode.base.models import ResourceBase
from geonode.metadata.settings import JSONSCHEMA_BASE

logger = logging.getLogger(__name__)

class Handler(metaclass=ABCMeta):
    """
    Handlers take care of reading, storing, encoding, 
    decoding subschemas of the main Resource
    """

    @abstractmethod
    def update_schema(self, jsonschema: dict = {}):
        """
        It is called by the MetadataManager when creating the JSON Schema 
        It adds the subschema handled by the handler, and returns the 
        augmented instance of the JSON Schema.
        """
        pass

    @abstractmethod
    def get_jsonschema_instance(resource: ResourceBase, field_name: str):
        """
        Called when reading metadata, returns the instance of the sub-schema 
        associated with the field field_name.
        """
        pass

    @abstractmethod
    def update_resource(resource: ResourceBase, field_name: str, content: dict, json_instance: dict):
        """
        Called when persisting data, updates the field field_name of the resource 
        with the content content, where json_instance is  the full JSON Schema instance, 
        in case the handler needs some cross related data contained in the resource.
        """
        pass

    @abstractmethod
    def load_context(resource: ResourceBase, context: dict):
        """
        Called before calls to update_resource in order to initialize info needed by the handler
        """
        pass


class CoreHandler(Handler):
    """
    The base handler builds a valid empty schema with the simple
    fields of the ResourceBase model
    """

    def __init__(self):
        self.json_base_schema = JSONSCHEMA_BASE
        self.basic_schema = None
    
    def update_schema(self, jsonschema):
        with open(self.json_base_schema) as f:
            self.basic_schema = json.load(f)
        # building the full base schema
        for key, val in dict.items(self.basic_schema):
            # add the base handler identity to the dictionary
            val.update({"geonode:handler": "base"})
            jsonschema["properties"].update({key: val})

        return jsonschema

    def get_jsonschema_instance(resource: ResourceBase, field_name: str):
        
        pass

    def update_resource(resource: ResourceBase, field_name: str, content: dict, json_instance: dict):
        
        pass

    def load_context(resource: ResourceBase, context: dict):
        
        pass
