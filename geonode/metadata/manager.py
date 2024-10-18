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
from abc import ABCMeta, abstractmethod
from geonode.metadata.handlers import CoreHandler
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.metadata.api.serializers import MetadataSerializer

logger = logging.getLogger(__name__)

class MetadataManagerInterface(metaclass=ABCMeta):

    pass

class MetadataManager(MetadataManagerInterface):
    """
    The metadata manager is the bridge between the API and the geonode model. 
    The metadata manager will loop over all of the registered metadata handlers, 
    calling their update_schema(jsonschema) which will add the subschemas of the 
    fields handled by each handler. At the end of the loop, the schema will be ready 
    to be delivered to the caller.
    """

    def __init__(self):
        self.jsonschema = MODEL_SCHEMA
        self.schema = None
        self.handlers = []
        self.serializer_class = MetadataSerializer

    def add_handler(self, handler):
        
        # Handlers initialization
        handler_obj = handler()
        self.handlers.append(handler_obj)
    
    def build_schema(self):
        for handler in self.handlers:

            if self.schema:
                # Update the properties key of the current schema with the properties of the new handler
                self.schema["properties"].update(handler.update_schema(self.jsonschema)["properties"])
            else:
                self.schema = handler.update_schema(self.jsonschema)

        return self.schema    

    def get_schema(self):
        if not self.schema:
           self.build_schema()
            
        return self.schema
    
    def build_schema_instance(self, resource):

        instance = {}
        
        # serialized_resource = self.get_resource_base(resource)
        schema = self.get_schema()

        for fieldname, field in schema["properties"].items():
            handler_id = field["geonode:handler"]
            # temp 
            handler = self.handlers[0]
            content = handler.get_jsonschema_instance(resource, fieldname)
            instance[fieldname] = content
        
        return instance

        
    
    def resource_base_serialization(self, resource):
        """
        Get a serialized dataset from the ResourceBase model
        """
        serializer = self.serializer_class
        
        serialized_data = serializer(resource, many=True).data
        return serialized_data

metadata_manager = MetadataManager()