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

from geonode.base.models import Region
from geonode.metadata.handlers.abstract import MetadataHandler

logger = logging.getLogger(__name__)


class RegionHandler(MetadataHandler):
    """
    The RegionsHandler adds the Regions model options to the schema
    """

    def update_schema(self, jsonschema, context, lang=None):
        regions = {
            "type": "array",
            "title": _("Regions"),
            "description": _("keyword identifies a location"),
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                    },
                    "label": {"type": "string", "title": _("title")},
                },
            },
            "geonode:handler": "region",
            "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_regions")},
        }

        # add regions after Attribution
        self._add_subschema(jsonschema, "regions", regions, after_what="attribution")
        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        return [{"id": str(r.id), "label": r.name} for r in resource.regions.all()]

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        data = json_instance[field_name]
        new_ids = {item["id"] for item in data}
        logger.info(f"Regions added {data} --> {new_ids}")

        regions = Region.objects.filter(id__in=new_ids)
        resource.regions.set(regions)
