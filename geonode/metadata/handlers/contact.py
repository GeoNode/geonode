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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.people import Roles

logger = logging.getLogger(__name__)

# contact roles names are spread in the code, let's map them here:
ROLE_NAMES_MAP = {
    Roles.OWNER: "owner",  # this is not saved as a contact
    Roles.METADATA_AUTHOR: "author",
    Roles.PROCESSOR: Roles.PROCESSOR.name,
    Roles.PUBLISHER: Roles.PUBLISHER.name,
    Roles.CUSTODIAN: Roles.CUSTODIAN.name,
    Roles.POC: "pointOfContact",
    Roles.DISTRIBUTOR: Roles.DISTRIBUTOR.name,
    Roles.RESOURCE_USER: Roles.RESOURCE_USER.name,
    Roles.RESOURCE_PROVIDER: Roles.RESOURCE_PROVIDER.name,
    Roles.ORIGINATOR: Roles.ORIGINATOR.name,
    Roles.PRINCIPAL_INVESTIGATOR: Roles.PRINCIPAL_INVESTIGATOR.name,
}

NAMES_ROLE_MAP = {v: k for k, v in ROLE_NAMES_MAP.items()}


class ContactHandler(MetadataHandler):
    """
    Handles role contacts
    """

    def update_schema(self, jsonschema, context, lang=None):
        contacts = {}
        required = []
        for role in Roles:
            rolename = ROLE_NAMES_MAP[role]
            minitems = 1 if role.is_required else 0
            card = f' [{minitems}..{"N" if role.is_multivalue else "1"}]' if settings.DEBUG else ""
            if role.is_required:
                required.append(rolename)

            if role.is_multivalue:
                contact = {
                    "type": "array",
                    "title": self._localize_label(context, lang, role.label) + card,
                    "minItems": minitems,
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
                }
            else:
                contact = {
                    "type": "object",
                    "title": self._localize_label(context, lang, role.label) + card,
                    "properties": {
                        "id": {
                            "type": "string",
                            "title": _("User id"),
                            "ui:widget": "hidden",
                        },
                        "label": {
                            "type": "string",
                            "title": _("User name"),
                        },
                    },
                    "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_users")},
                    "required": ["id"] if role.is_required else [],
                }

            contacts[rolename] = contact

            jsonschema["properties"]["contacts"] = {
                "type": "object",
                "title": self._localize_label(context, lang, "contacts"),
                "properties": contacts,
                "required": required,
                "geonode:required": bool(required),
                "geonode:handler": "contact",
            }

        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        def __create_user_entry(user):
            names = [n for n in (user.first_name, user.last_name) if n]
            postfix = f" ({' '.join(names)})" if names else ""
            return {"id": str(user.id), "label": f"{user.username}{postfix}"}

        contacts = {}
        for role in Roles:
            rolename = ROLE_NAMES_MAP[role]
            if role.is_multivalue:
                content = [__create_user_entry(user) for user in resource.__get_contact_role_elements__(rolename) or []]
            else:
                users = resource.__get_contact_role_elements__(rolename)
                if not users and role == Roles.OWNER:
                    users = [resource.owner]
                content = __create_user_entry(users[0]) if users else None

            contacts[rolename] = content

        return contacts

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        data = json_instance[field_name]
        logger.debug(f"CONTACTS {data}")
        for rolename, users in data.items():
            if rolename == Roles.OWNER.name:
                if not users:
                    logger.warning(f"User not specified for role '{rolename}'")
                    self._set_error(errors, ["contacts", rolename], f"User not specified for role '{rolename}'")
                else:
                    resource.owner = get_user_model().objects.get(pk=users["id"])
            else:
                ids = [u["id"] for u in users]
                profiles = get_user_model().objects.filter(pk__in=ids)
                resource.__set_contact_role_element__(profiles, rolename)
