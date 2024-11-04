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
from geonode.people import Roles

logger = logging.getLogger(__name__)


class ContactHandler(MetadataHandler):
    """
    The RegionsHandler adds the Regions model options to the schema
    """

    def update_schema(self, jsonschema, lang=None):

        contacts = {}
        for role in Roles:
            card = ("1" if role.is_required else "0") + ".." + ("N" if role.is_multivalue else "1")
            if role.is_multivalue:
                contact = {
                    "type": "array",
                    "title": _(role.label) + " " + card,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "title": _("User id"),
                            },
                            "label": {
                                "type": "string",
                                "title": _("User name"),
                            },
                        },
                    },
                    "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_users")},
                    "xxrequired": role.is_required,
                }
            else:
                contact = {
                    "type": "object",
                    "title": _(role.label) + " " + card,
                    "properties": {
                        "id": {
                            "type": "string",
                            "title": _("User id"),
                        },
                        "label": {
                            "type": "string",
                            "title": _("User name"),
                        },
                    },
                    "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_users")},
                    "xxrequired": role.is_required,
                }

            contacts[role.name] = contact

            jsonschema["properties"]["contacts"] = {
                "type": "object",
                "title": _("Contacts"),
                "properties": contacts,
                "geonode:handler": "contact",
            }

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str, lang=None):
        def __create_user_entry(user):
            return {"id": user.username, "name": f"{user.username} - {user.first_name} {user.last_name}"}

        contacts = {}
        for role in Roles:
            if role.is_multivalue:
                content = [__create_user_entry(user) for user in resource.__get_contact_role_elements__(role) or []]
            else:
                users = resource.__get_contact_role_elements__(role)
                if not users and role == Roles.OWNER:
                    users = [resource.owner]
                content = __create_user_entry(users[0]) if users else None

            contacts[role.name] = content

        return contacts

    def update_resource(self, resource: ResourceBase, field_name: str, json_instance: dict):

        pass

    def load_context(self, resource: ResourceBase, context: dict):

        pass
