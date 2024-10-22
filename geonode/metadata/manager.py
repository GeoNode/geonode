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
from abc import ABCMeta

from django.utils.translation import gettext as _

from geonode.metadata.settings import MODEL_SCHEMA
from geonode.metadata.registry import metadata_registry

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
        self.instance = {}
        self.handlers = {}

    def add_handler(self, handler_id, handler):
        
        handler_instance = handler()
        
        self.handlers[handler_id] = handler_instance

    
    def build_schema(self, lang=None):
        self.schema =  self.jsonschema.copy()
        self.schema["title"] = _(self.schema["title"])

        for handler in self.handlers.values():
            self.schema = handler.update_schema(self.schema, lang)

        return self.schema    

    def get_schema(self, lang=None):
        if not self.schema:
           self.build_schema(lang)
            
        return self.schema
    
    def build_schema_instance(self, resource):
        
        schema = self.get_schema()

        for fieldname, field in schema["properties"].items():
            handler_id = field["geonode:handler"]
            handler = self.handlers[handler_id]
            content = handler.get_jsonschema_instance(resource, fieldname)
            self.instance[fieldname] = content
        
        return self.instance
    
    def update_schema_instance(self, resource, content, json_instance):
        
        schema = self.get_schema()

        for fieldname, field in schema["properties"].items():
            handler_id = field["geonode:handler"]
            handler = self.handlers[handler_id]
            handler.update_resource(resource, fieldname, content, json_instance)
        
        try:
            resource.save()
            return {"message": "The resource was updated successfully"}
        
        except:
            return {"message": "Something went wrong... The resource was not updated"}


metadata_manager = MetadataManager()