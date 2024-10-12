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

    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def build_schema(self):
        for handler in self.handlers:
            handler_instance = handler()

            if self.schema:
                # Update the properties key of the schema with the properties of the new handler
                self.schema["properties"].update(handler_instance.update_schema(self.jsonschema)["properties"])
            else:
                self.schema = handler_instance.update_schema(self.jsonschema)

        return self.schema    

    def get_schema(self):
        if not self.schema:
           self.build_schema()
            
        return self.schema

metadata_manager = MetadataManager()