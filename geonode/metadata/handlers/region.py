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

from rest_framework.reverse import reverse
from django.utils.translation import gettext as _

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import JSONSCHEMA_BASE
from geonode.base.views import RegionAutocomplete

logger = logging.getLogger(__name__)


class RegionHandler(MetadataHandler):
    """
    The RegionsHandler adds the Regions model options to the schema
    """

    def __init__(self):
        self.json_base_schema = JSONSCHEMA_BASE
        self.base_schema = None

    def update_schema(self, jsonschema, lang=None):

        from geonode.base.models import Region

        subschema = [{"const": tc.code,"title": tc.name}
                                       for tc in Region.objects.order_by("name")]
        
        regions = {
            "type": "array",
            "title": _("Regions"),
            "description": _("keyword identifies a location"),
            "items": {
                "type": "string",
                "anyOf": subschema
            },
            "geonode:handler": "region",
            "ui:options": {
                "geonode-ui:autocomplete": reverse(
                        "autocomplete_region"
                        )
                 },
        }

        # add regions after Attribution

        ret_properties = {}
        for key, val in jsonschema["properties"].items():
            ret_properties[key] = val
            if key == "attribution":
                ret_properties["regions"] = regions

        jsonschema["properties"] = ret_properties

        return jsonschema
       
    @classmethod
    def serialize(cls, db_value):
        # TODO
        return []

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str):

        return None

    def update_resource(self, resource: ResourceBase, field_name: str, content: dict, json_instance: dict):

        pass

    def load_context(self, resource: ResourceBase, context: dict):

        pass