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
from cachetools import FIFOCache

from django.utils.translation import gettext as _

from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import MODEL_SCHEMA

logger = logging.getLogger(__name__)


class MetadataManager:
    """
    The metadata manager is the bridge between the API and the geonode model.
    The metadata manager will loop over all of the registered metadata handlers,
    calling their update_schema(jsonschema) which will add the subschemas of the
    fields handled by each handler. At the end of the loop, the schema will be ready
    to be delivered to the caller.
    """

    # FIFO bc we want to renew the data once in a while
    _schema_cache = FIFOCache(32)

    def __init__(self):
        self.root_schema = MODEL_SCHEMA
        self.handlers = {}

    def add_handler(self, handler_id, handler):
        self.handlers[handler_id] = handler()

    def build_schema(self, lang=None):
        logger.debug(f"build_schema {lang}")

        schema = copy.deepcopy(self.root_schema)
        schema["title"] = _(schema["title"])

        for key, handler in self.handlers.items():
            # logger.debug(f"build_schema: update schema -> {key}")
            schema = handler.update_schema(schema, lang)

        # Set required fields.
        required = []
        for fieldname, field in schema["properties"].items():
            if field.get("geonode:required", False):
                required.append(fieldname)

        if required:
            schema["required"] = required
        return schema

    def get_schema(self, lang=None):
        cache_key = str(lang)
        ret = MetadataManager._schema_cache.get(cache_key, None)
        if not ret:
            logger.info(f"Building schema for {cache_key}")
            ret = self.build_schema(lang)
            MetadataManager._schema_cache[cache_key] = ret
            logger.info("Schema built")
        return ret

    def build_schema_instance(self, resource, lang=None):
        schema = self.get_schema(lang)

        context = {}
        for handler in self.handlers.values():
            handler.load_serialization_context(resource, schema, context)

        instance = {}
        for fieldname, subschema in schema["properties"].items():
            # logger.debug(f"build_schema_instance: getting handler for property {fieldname}")
            handler_id = subschema.get("geonode:handler", None)
            if not handler_id:
                logger.warning(f"Missing geonode:handler for schema property {fieldname}. Skipping")
                continue
            handler = self.handlers[handler_id]
            content = handler.get_jsonschema_instance(resource, fieldname, context, lang)
            instance[fieldname] = content

        # TESTING ONLY
        if "error" in resource.title.lower():
            errors = {}
            MetadataHandler._set_error(errors, ["title"], "GET: test msg under /title")
            MetadataHandler._set_error(errors, ["properties", "title"], "GET: test msg under /properties/title")
            instance["extraErrors"] = errors

        return instance

    def update_schema_instance(self, resource, json_instance) -> dict:

        logger.debug(f"RECEIVED INSTANCE {json_instance}")

        schema = self.get_schema()
        errors = {}

        for fieldname, subschema in schema["properties"].items():
            handler = self.handlers[subschema["geonode:handler"]]
            # todo: get errors also
            handler.update_resource(resource, fieldname, json_instance, errors)
        try:
            resource.save()
        except Exception as e:
            logger.warning(f"Error while updating schema instance: {e}")
            errors.setdefault("__errors", []).append(f"Error while saving the resource: {e}")

        # TESTING ONLY
        if "error" in resource.title.lower():
            errors.setdefault("title", {}).setdefault("__errors", []).append("PUT: this is a test error under /title")
            errors.setdefault("properties", {}).setdefault("title", {}).setdefault("__errors", []).append(
                "PUT: this is a test error under /properties/title"
            )

            MetadataHandler._set_error(errors, ["title"], "PUT: this is another test msg under /title")
            MetadataHandler._set_error(
                errors, ["properties", "title"], "PUT: this is another test msg under /properties/title"
            )

        return errors


metadata_manager = MetadataManager()
