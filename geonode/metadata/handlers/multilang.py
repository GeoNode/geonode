#########################################################################
#
# Copyright (C) 2025 OSGeo
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

from django.conf import settings

from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.handlers.sparse import sparse_field_registry
from geonode.metadata.multilang import utils as multi

logger = logging.getLogger(__name__)


class MultiLangHandler(MetadataHandler):

    def post_init(self):
        # register all multilang localized fields as sparse fields
        for property_name in settings.MULTILANG_FIELDS:
            prev_field = property_name
            for lang, ml_property_name in multi.get_multilang_field_names(property_name):
                ml_subschema = self._create_ml_subschema(property_name, lang)
                logger.debug(f"Registering multilang sparse field {property_name} --> {ml_property_name}")
                sparse_field_registry.register(
                    ml_property_name, ml_subschema, after=prev_field, init_func=self.init_func
                )
                prev_field = ml_property_name

    @staticmethod
    def init_func(field_name, subschema, jsonschema, req_lang):
        # process multilang localized fields when they are added to the schema
        logger.debug(f"Processing subschema for {field_name}")

        # copy into multilang entries some info read from the maim property
        parent_name = subschema["geonode:multilang-group"]
        parent_schema = jsonschema["properties"][parent_name]
        subschema_lang = subschema["geonode:multilang-lang"]
        main = " !" if subschema_lang == multi.get_default_language() else ""
        subschema["title"] = (
            f"{parent_schema.get('title', '')} [{subschema_lang.upper()}]{main}"  # parent title should already be localized
        )
        if "ui:options" in parent_schema:
            subschema["ui:options"] = parent_schema["ui:options"]

    def update_schema(self, jsonschema, context, lang=None):
        for property_name in settings.MULTILANG_FIELDS:
            # validate constraints
            parent_schema = jsonschema["properties"][property_name]
            if not MetadataHandler._check_type(parent_schema["type"], "string"):
                raise ValueError(f"Field {property_name} cannot be multilang")

            parent_schema["geonode:multilang"] = True  # mark the main field as lead multilang
            parent_schema["readOnly"] = True  # lock the main field (we'll update its content later)

        return jsonschema

    def _create_ml_subschema(self, parent_name, lang):
        return {
            "type": ["string", "null"],
            "geonode:handler": "sparse",
            "geonode:multilang-lang": lang,
            "geonode:multilang-group": parent_name,
        }

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        pass

    def post_serialization(self, resource, jsonschema: dict, instance: dict, context: dict):
        for property_name in settings.MULTILANG_FIELDS:
            logger.debug(f"checking post serialization for {property_name}")

            # set the default language entry the same as the main property
            # this may be useful when firstly configuring multilang in a populated catalog
            def_lang_pname = multi.get_multilang_field_name(property_name, multi.get_default_language())
            def_lang_value = instance.get(def_lang_pname, "")
            if not def_lang_value:
                main_value = instance.get(property_name, None)
                if main_value:
                    logger.info(
                        f"Fixing main lang field '{def_lang_pname}' with value from base field '{property_name}'"
                    )
                    instance[def_lang_pname] = main_value

    def pre_deserialization(self, resource, jsonschema: dict, instance: dict, context: dict):
        # store default-lang value into original fields
        for property_name in settings.MULTILANG_FIELDS:
            logger.debug(f"Copying base multilang field '{property_name}'")

            def_lang_pname = multi.get_multilang_field_name(property_name, multi.get_default_language())
            def_lang_value = instance.get(def_lang_pname, "")
            instance[property_name] = def_lang_value

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        # TODO
        pass
