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
from collections import defaultdict

from typing_extensions import deprecated

from django.utils.translation import gettext as _

from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


class MetadataHandler(metaclass=ABCMeta):
    """
    Handlers take care of reading, storing, encoding,
    decoding subschemas of the main Resource
    """

    @abstractmethod
    def update_schema(self, jsonschema: dict, context: dict, lang=None):
        """
        It is called by the MetadataManager when creating the JSON Schema
        It adds the subschema handled by the handler, and returns the
        augmented instance of the JSON Schema.
        Context is populated by the manager with some common info:
         - key "labels": contains the localized label loaded from the db as a dict, where key is the ThesaurusKeyword about
           and value is the localized ThesaurusKeywordLabel, or the AltLabel if the localized label does not exist.
        """
        pass

    @abstractmethod
    def get_jsonschema_instance(
        self, resource: ResourceBase, field_name: str, context: dict, errors: dict, lang: str = None
    ):
        """
        Called when reading metadata, returns the instance of the sub-schema
        associated with the field field_name.
        """
        pass

    @abstractmethod
    def update_resource(
        self, resource: ResourceBase, field_name: str, json_instance: dict, context: dict, errors: dict, **kwargs
    ):
        """
        Called when persisting data, updates the field `field_name` of the resource
        with the content content, where json_instance is  the full JSON Schema instance,
        in case the handler needs some cross related data contained in the resource.
        """
        pass

    def pre_save(self, resource: ResourceBase, json_instance: dict, context: dict, errors: dict, **kwargs):
        """
        Called just after all the calls to update_resource, and just before ResourceBase.save()
        """
        pass

    def post_save(self, resource: ResourceBase, json_instance: dict, context: dict, errors: dict, **kwargs):
        """
        Called after ResourceBase.save()
        """
        pass

    def load_serialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        """
        Called before calls to get_jsonschema_instance in order to initialize info needed by the handler
        """
        pass

    def load_deserialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        """
        Called before calls to update_resource in order to initialize info needed by the handler
        """
        pass

    def _add_subschema(self, jsonschema, property_name, subschema, after_what=None):
        after_what = after_what or subschema.get("geonode:after", None)

        if not after_what:
            jsonschema["properties"][property_name] = subschema
        else:
            ret_properties = {}
            added = False
            for key, val in jsonschema["properties"].items():
                ret_properties[key] = val
                if key == after_what:
                    ret_properties[property_name] = subschema
                    added = True

            if not added:
                logger.warning(f'Could not add "{property_name}" after "{after_what}"')
                ret_properties[property_name] = subschema

            jsonschema["properties"] = ret_properties

    @deprecated("Use _add_subschema instead")
    def _add_after(self, jsonschema, after_what, property_name, subschema):
        ret_properties = {}
        added = False
        for key, val in jsonschema["properties"].items():
            ret_properties[key] = val
            if key == after_what:
                ret_properties[property_name] = subschema
                added = True

        if not added:
            logger.warning(f'Could not add "{property_name}" after "{after_what}"')
            ret_properties[property_name] = subschema

        jsonschema["properties"] = ret_properties

    @staticmethod
    def _set_error(errors: dict, path: list, msg: str):
        logger.info(f"Setting error: {'/'.join(path)}: {msg}")
        elem = errors
        for step in path:
            elem = elem.setdefault(step, {})
        elem = elem.setdefault("__errors", [])
        elem.append(msg)

    @staticmethod
    def localize_message(context: dict, msg_code: str, msg_info: dict):
        msg_loc: str = MetadataHandler._get_tkl_labels(context, None, msg_code)
        if msg_loc:
            tokens = defaultdict(lambda: "N/A", msg_info or {})
            return msg_loc.format_map(tokens)
        else:
            logger.warning(f"Missing i18n entry for key '{msg_code}' -- info is {msg_info}")
            return f"{msg_code}:{msg_info}"

    @staticmethod
    def _localize_label(context, lang: str, text: str):
        label = MetadataHandler._get_tkl_labels(context, lang, text)
        return label if label else _(text)

    @staticmethod
    def _get_tkl_labels(context, lang: str | None, text: str):
        return context["labels"].get(text, None)

    @staticmethod
    def _localize_subschema_labels(context, subschema: dict, lang: str, property_name: str = None):
        for annotation_name, synt in (
            ("title", ""),
            ("description", "__descr"),
        ):
            if annotation_name in subschema:
                subschema[annotation_name] = MetadataHandler._localize_label(context, lang, subschema[annotation_name])
            elif property_name:  # arrays may not have a name
                label = MetadataHandler._get_tkl_labels(context, lang, f"{property_name}{synt}")
                if label:
                    subschema[annotation_name] = label
