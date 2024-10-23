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
from geonode.base.models import ResourceBase, TopicCategory, License, Region, RestrictionCodeType, \
    SpatialRepresentationType
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import JSONSCHEMA_BASE
from geonode.base.enumerations import ALL_LANGUAGES, UPDATE_FREQUENCIES
from django.utils.translation import gettext as _


logger = logging.getLogger(__name__)


class CategorySubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        # subschema["title"] = _("topiccategory")
        subschema["oneOf"] = [{"const": tc.identifier,"title": tc.gn_description, "description": tc.description}
                              for tc in TopicCategory.objects.order_by("gn_description")]

class FrequencySubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": key,"title": val}
                              for key, val in dict(UPDATE_FREQUENCIES).items()]

class LanguageSubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": key,"title": val}
                              for key, val in dict(ALL_LANGUAGES).items()]

class LicenseSubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": tc.identifier,"title": tc.name, "description": tc.description}
                              for tc in License.objects.order_by("name")]

class RegionSubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["items"]["anyOf"] = [{"const": tc.code,"title": tc.name}
                                       for tc in Region.objects.order_by("name")]

class RestrictionsSubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": tc.identifier,"title": tc.identifier, "description": tc.description}
                              for tc in RestrictionCodeType.objects.order_by("identifier")]

class SpatialRepresentationTypeSubHandler:
    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [{"const": tc.identifier,"title": tc.identifier, "description": tc.description}
                              for tc in SpatialRepresentationType.objects.order_by("identifier")]


SUBHANDLERS = {
    "category": CategorySubHandler,
    "language": LanguageSubHandler,
    "license": LicenseSubHandler,
    "maintenance_frequency": FrequencySubHandler,
    "regions": RegionSubHandler,
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

    def update_schema(self, jsonschema, lang=None):
        def localize(subschema: dict, annotation_name):
            if annotation_name in subschema:
                subschema[annotation_name] = _(subschema[annotation_name])

        with open(self.json_base_schema) as f:
            self.base_schema = json.load(f)
        # building the full base schema
        for property_name, subschema in self.base_schema.items():
            localize(subschema, 'title')
            localize(subschema, 'abstract')

            jsonschema["properties"][property_name] = subschema

            # add the base handler info to the dictionary if it doesn't exist
            if "geonode:handler" not in subschema:
                subschema.update({"geonode:handler": "base"})

            # perform further specific initializations

            if subhandler := SUBHANDLERS.get(property_name, None):
                logger.debug(f"Running subhandler for base field {property_name}")
                subhandler.update_subschema(subschema, lang)

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str):

        field_value = getattr(resource, field_name)

        return field_value

    def update_resource(self, resource: ResourceBase, field_name: str, content: dict, json_instance: dict):
       
        if field_name in content:
            # insert the content value to the corresponding field_name
            setattr(resource, field_name, content[field_name])

    def load_context(self, resource: ResourceBase, context: dict):

        pass

