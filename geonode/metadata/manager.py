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

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.exceptions import UnsetFieldException
from geonode.metadata.i18n import get_localized_labels, I18N_THESAURUS_IDENTIFIER
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

    @classmethod
    def clear_schema_cache(cls):
        logger.info("Clearing schema cache")
        while True:
            try:
                MetadataManager._schema_cache.popitem()
            except KeyError:
                return

    def add_handler(self, handler_id, handler):
        self.handlers[handler_id] = handler()

    def _init_schema_context(self, lang):
        # todo: cache localizations
        return {"labels": get_localized_labels(lang)}

    def build_schema(self, lang=None):
        logger.debug(f"build_schema {lang}")

        schema = copy.deepcopy(self.root_schema)
        schema["title"] = _(schema["title"])

        context = self._init_schema_context(lang)

        for key, handler in self.handlers.items():
            # logger.debug(f"build_schema: update schema -> {key}")
            schema = handler.update_schema(schema, context, lang)

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
        errors = {}
        for fieldname, subschema in schema["properties"].items():
            # logger.debug(f"build_schema_instance: getting handler for property {fieldname}")
            handler_id = subschema.get("geonode:handler", None)
            if not handler_id:
                logger.warning(f"Missing geonode:handler for schema property {fieldname}. Skipping")
                continue
            handler = self.handlers[handler_id]
            try:
                content = handler.get_jsonschema_instance(resource, fieldname, context, errors, lang)
                instance[fieldname] = content
            except UnsetFieldException:
                pass

        # TESTING ONLY
        if "error" in resource.title.lower():
            for fieldname in schema["properties"]:
                MetadataHandler._set_error(
                    errors, [fieldname], f"TEST: test msg for field '{fieldname}' in GET request"
                )
            instance["extraErrors"] = errors

        return instance

    def update_schema_instance(self, resource, json_instance) -> dict:
        logger.debug(f"RECEIVED INSTANCE {json_instance}")
        resource = resource.get_real_instance()
        schema = self.get_schema()
        context = {}
        for handler in self.handlers.values():
            handler.load_deserialization_context(resource, schema, context)

        errors = {}

        for fieldname, subschema in schema["properties"].items():
            handler = self.handlers[subschema["geonode:handler"]]
            try:
                handler.update_resource(resource, fieldname, json_instance, context, errors)
            except Exception as e:
                MetadataHandler._set_error(errors, [fieldname], f"Error while processing this field: {e}")
        try:
            resource.save()
        except Exception as e:
            logger.warning(f"Error while updating schema instance: {e}")
            MetadataHandler._set_error(errors, [], f"Error while saving the resource: {e}")

        # TESTING ONLY
        if "error" in resource.title.lower():
            _create_test_errors(schema, errors, [], "TEST: field <{schema_type}>'{path}' PUT request")

        return errors


def _create_test_errors(schema, errors, path, msg_template, create_message=True):
    if create_message:
        stringpath = "/".join(path) if path else "ROOT"
        MetadataHandler._set_error(errors, path, msg_template.format(path=stringpath, schema_type=schema["type"]))

    if schema["type"] == "object":
        for field, subschema in schema["properties"].items():
            _create_test_errors(subschema, errors, path + [field], msg_template)
    elif schema["type"] == "array":
        _create_test_errors(schema["items"], errors, path, msg_template, create_message=False)


# signals for invalidating cached data
def thesaurus_changed(sender, instance, **kwargs):
    base = f"Thesaurus changed: class {sender.__class__.__name__} -->"
    if sender == Thesaurus and instance.identifier == I18N_THESAURUS_IDENTIFIER:
        logger.debug(f"{base} {instance.identifier}")
        MetadataManager.clear_schema_cache()
    elif sender == ThesaurusKeyword and instance.thesaurus.identifier == I18N_THESAURUS_IDENTIFIER:
        logger.debug(f"{base} {instance.about} ALT:{instance.alt_label}")
        MetadataManager.clear_schema_cache()
    elif sender == ThesaurusKeywordLabel and instance.keyword.thesaurus.identifier == I18N_THESAURUS_IDENTIFIER:
        logger.debug(f"{base} {instance.keyword.about} ALT:{instance.keyword.alt_label} L:{instance.lang}")
        MetadataManager.clear_schema_cache()


metadata_manager = MetadataManager()
