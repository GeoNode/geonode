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
from datetime import datetime

from rest_framework.reverse import reverse
from django.utils.translation import gettext as _

from geonode.base.models import TopicCategory, License, RestrictionCodeType, SpatialRepresentationType
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import JSONSCHEMA_BASE
from geonode.base.enumerations import ALL_LANGUAGES, UPDATE_FREQUENCIES


logger = logging.getLogger(__name__)


class SubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        pass

    @classmethod
    def serialize(cls, db_value):
        return db_value

    @classmethod
    def deserialize(cls, field_value):
        return field_value


class CategorySubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["ui:options"] = {
            "geonode-ui:autocomplete": reverse("metadata_autocomplete_categories"),
        }

    @classmethod
    def serialize(cls, db_value):
        if db_value is None:
            return None
        elif isinstance(db_value, TopicCategory):
            return {"id": db_value.identifier, "label": _(db_value.gn_description)}
        else:
            logger.warning(f"Category: can't decode <{type(db_value)}>'{db_value}'")
            return None

    @classmethod
    def deserialize(cls, field_value):
        return TopicCategory.objects.get(identifier=field_value["id"]) if field_value else None


class DateTypeSubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": i.lower(), "title": _(i)} for i in ["Creation", "Publication", "Revision"]]
        subschema["default"] = "Publication"


class DateSubHandler(SubHandler):
    @classmethod
    def serialize(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class FrequencySubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": key, "title": val} for key, val in dict(UPDATE_FREQUENCIES).items()]


class LanguageSubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": key, "title": val} for key, val in dict(ALL_LANGUAGES).items()]


class LicenseSubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["ui:options"] = {
            "geonode-ui:autocomplete": reverse("metadata_autocomplete_licenses"),
        }

    @classmethod
    def serialize(cls, db_value):
        if db_value is None:
            return None
        elif isinstance(db_value, License):
            return {"id": db_value.identifier, "label": _(db_value.name)}
        else:
            logger.warning(f"License: can't decode <{type(db_value)}>'{db_value}'")
            return None

    @classmethod
    def deserialize(cls, field_value):
        return License.objects.get(identifier=field_value["id"]) if field_value else None


class RestrictionsSubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [
            {"const": tc.identifier, "title": tc.identifier, "description": tc.description}
            for tc in RestrictionCodeType.objects.order_by("identifier")
        ]

    @classmethod
    def serialize(cls, db_value):
        if isinstance(db_value, RestrictionCodeType):
            return db_value.identifier
        return db_value

    @classmethod
    def deserialize(cls, field_value):
        return RestrictionCodeType.objects.get(identifier=field_value) if field_value else None


class SpatialRepresentationTypeSubHandler(SubHandler):
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [
            {"const": tc.identifier, "title": tc.identifier, "description": tc.description}
            for tc in SpatialRepresentationType.objects.order_by("identifier")
        ]

    @classmethod
    def serialize(cls, db_value):
        if isinstance(db_value, SpatialRepresentationType):
            return db_value.identifier
        return db_value

    @classmethod
    def deserialize(cls, field_value):
        return SpatialRepresentationType.objects.get(identifier=field_value) if field_value else None


SUBHANDLERS = {
    "category": CategorySubHandler,
    "date_type": DateTypeSubHandler,
    "date": DateSubHandler,
    "language": LanguageSubHandler,
    "license": LicenseSubHandler,
    "maintenance_frequency": FrequencySubHandler,
    "restriction_code_type": RestrictionsSubHandler,
    "spatial_representation_type": SpatialRepresentationTypeSubHandler,
}


class BaseHandler(MetadataHandler):
    """
    The base handler builds a valid empty schema with the simple
    fields of the ResourceBase model
    """

    def __init__(self):
        self.json_base_schema = JSONSCHEMA_BASE
        self.base_schema = None

    def update_schema(self, jsonschema, context, lang=None):

        with open(self.json_base_schema) as f:
            self.base_schema = json.load(f)
        # building the full base schema
        for property_name, subschema in self.base_schema.items():
            self._localize_subschema_label(context, subschema, lang, "title")
            self._localize_subschema_label(context, subschema, lang, "description")

            jsonschema["properties"][property_name] = subschema

            # add the base handler info to the dictionary if it doesn't exist
            if "geonode:handler" not in subschema:
                subschema.update({"geonode:handler": "base"})

            # perform further specific initializations
            if property_name in SUBHANDLERS:
                # logger.debug(f"Running subhandler for base field {property_name}")
                SUBHANDLERS[property_name].update_subschema(subschema, lang)

        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        field_value = getattr(resource, field_name)

        # perform specific transformation if any
        if field_name in SUBHANDLERS:
            # logger.debug(f"Serializing base field {field_name}")
            field_value = SUBHANDLERS[field_name].serialize(field_value)

        return field_value

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        field_value = json_instance.get(field_name, None)

        try:
            if field_name in SUBHANDLERS:
                logger.debug(f"Deserializing base field {field_name}")
                # Deserialize field values before setting them to the ResourceBase
                field_value = SUBHANDLERS[field_name].deserialize(field_value)

            setattr(resource, field_name, field_value)
        except Exception as e:
            logger.warning(f"Error setting field {field_name}={field_value}: {e}")
            self._set_error(errors, [field_name], "Error while storing field. Contact your administrator")
