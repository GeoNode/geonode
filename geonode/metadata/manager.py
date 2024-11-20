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
import copy
from abc import ABCMeta

from django.utils.translation import gettext as _

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
        self.root_schema = MODEL_SCHEMA
        self.cached_schema = None
        self.handlers = {}

    def add_handler(self, handler_id, handler):
        self.handlers[handler_id] = handler()

    def build_schema(self, lang=None):
        schema = copy.deepcopy(self.root_schema)
        schema["title"] = _(schema["title"])

        for key, handler in self.handlers.items():
            logger.debug(f"build_schema: update schema -> {key}")
            schema = handler.update_schema(schema, lang)

        return schema

    def get_schema(self, lang=None):
        return self.build_schema(lang)
        # we dont want caching for the moment
        if not self.cached_schema:
            self.cached_schema = self.build_schema(lang)

        return self.cached_schema

    def build_schema_instance(self, resource, lang=None):

        schema = self.get_schema()
        instance = {}

        for fieldname, field in schema["properties"].items():
            # logger.debug(f"build_schema_instance: getting handler for property {fieldname}")
            handler_id = field.get("geonode:handler", None)
            if not handler_id:
                logger.warning(f"Missing geonode:handler for schema property {fieldname}. Skipping")
                continue
            handler = self.handlers[handler_id]
            content = handler.get_jsonschema_instance(resource, fieldname, lang)
            instance[fieldname] = content

        return instance

    def update_schema_instance(self, resource, json_instance):

        logger.info(f"RECEIVED INSTANCE {json_instance}")

        schema = self.get_schema()

        for fieldname, subschema in schema["properties"].items():
            handler = self.handlers[subschema["geonode:handler"]]
            handler.update_resource(resource, fieldname, json_instance)

        try:
            resource.save()
            return {"message": "The resource was updated successfully"}

        except Exception as e:
            logger.warning(f"Error while updating schema instance: {e}")
            return {"message": "Something went wrong... The resource was not updated"}


metadata_manager = MetadataManager()
