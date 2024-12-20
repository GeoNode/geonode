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

from geonode.groups.models import GroupProfile
from geonode.metadata.handlers.abstract import MetadataHandler

logger = logging.getLogger(__name__)


class GroupHandler(MetadataHandler):
    """
    The GroupHandler handles the group FK field.
    This handler is only used in the first transition to the new metadata editor, and will be then replaced by
    an entry in the resource management panel
    """

    def update_schema(self, jsonschema, context, lang=None):
        group_schema = {
            "type": "object",
            "title": _("group"),
            "properties": {
                "id": {
                    "type": "string",
                    "ui:widget": "hidden",
                },
                "label": {
                    "type": "string",
                    "title": _("group"),
                },
            },
            "geonode:handler": "group",
            "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_groups")},
        }

        # add group after date_type
        self._add_subschema(jsonschema, "group", group_schema, after_what="date_type")

        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        return (
            {"id": str(resource.group.groupprofile.pk), "label": resource.group.groupprofile.title}
            if resource.group
            else None
        )

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        data = json_instance.get(field_name, None)
        id = data.get("id", None) if data else None
        if id is not None:
            gp = GroupProfile.objects.get(pk=id)
            resource.group = gp.group
        else:
            resource.group = None
