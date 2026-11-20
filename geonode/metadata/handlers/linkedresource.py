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

from geonode.base.models import ResourceBase, LinkedResource
from geonode.metadata.handlers.abstract import MetadataHandler

logger = logging.getLogger(__name__)

MAP_VIEWER_TYPE = "mapviewer"


class LinkedResourceHandler(MetadataHandler):

    def update_schema(self, jsonschema, context, lang=None):
        linked = {
            "type": "array",
            "title": _("Related resources"),
            "description": _("Resources related to this one"),
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                    },
                    "label": {"type": "string", "title": _("title")},
                },
            },
            "geonode:handler": "linkedresource",
            "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_resources")},
        }

        jsonschema["properties"]["linkedresources"] = linked
        return jsonschema

    @staticmethod
    def _editable_links(resource):
        qs = LinkedResource.get_linked_resources(source=resource, relation_type=LinkedResource.RelationType.RELATED)
        # the link between a map and its viewer is managed by the client
        if resource.resource_type == "map":
            qs = qs.exclude(target__resource_type=MAP_VIEWER_TYPE)
        return qs

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        return [{"id": str(lr.target.id), "label": lr.target.title} for lr in self._editable_links(resource)]

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        data = json_instance[field_name]
        new_ids = {item["id"] for item in data}

        # add requested links
        for res_id in new_ids:
            target = ResourceBase.objects.get(pk=res_id)
            if resource.resource_type == "map" and target.resource_type == MAP_VIEWER_TYPE:
                self._set_error(errors, [field_name], f"Map viewer '{target.title}' can not be linked to a map.")
                continue
            LinkedResource.objects.get_or_create(
                source=resource, target=target, relation_type=LinkedResource.RelationType.RELATED
            )

        # delete remaining links
        self._editable_links(resource).exclude(target_id__in=new_ids).delete()
