#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.utils.translation import ugettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase
import enum


class PeopleAppConfig(NotificationsAppConfigBase):
    name = "geonode.people"
    NOTIFICATIONS = (
        (
            "user_follow",
            _("User following you"),
            _("Another user has started following you"),
        ),
        (
            "account_approve",
            _("User requested access"),
            _("A new user has requested access to the site"),
        ),
        (
            "account_active",
            _("Account activated"),
            _("This account is now active and can log in the site"),
        ),
    )

    def ready(self):
        super().ready()


default_app_config = "geonode.people.PeopleAppConfig"


class Role:
    def __init__(self, label, is_required, is_multivalue):
        self.label = label
        self.is_required = is_required
        self.is_multivalue = is_multivalue

    def __repr__(self):
        return self.label


class Roles(enum.Enum):
    """Roles with their `label`, `is_required`, and `is_multivalue`"""

    OWNER = Role("Owner", True, False)
    METADATA_AUTHOR = Role("Metadata Author", True, True)
    PROCESSOR = Role("Processor", False, True)
    PUBLISHER = Role("Publisher", False, True)
    CUSTODIAN = Role("Custodian", False, True)
    POC = Role("Point of Contact", True, True)
    DISTRIBUTOR = Role("Distributor", False, True)
    RESOURCE_USER = Role("Resource User", False, True)
    RESOURCE_PROVIDER = Role("Resource Provider", False, True)
    ORIGINATOR = Role("Originator", False, True)
    PRINCIPAL_INVESTIGATOR = Role("Principal Investigator", False, True)

    @property
    def name(self):
        return super().name.lower()

    @property
    def label(self):
        return self.value.label

    @property
    def is_required(self):
        return self.value.is_required

    @property
    def is_multivalue(self):
        return self.value.is_multivalue

    def __repr__(self):
        return self.name

    @classmethod
    def get_required_ones(cls):
        return [role for role in cls if role.is_required]

    @classmethod
    def get_multivalue_ones(cls):
        return [role for role in cls if role.is_multivalue]
