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
import enum


class Role:
    def __init__(self, label, is_required, is_multivalue, is_toggled_in_metadata_editor):
        self.label = label
        self.is_required = is_required
        self.is_multivalue = is_multivalue
        self.is_toggled_in_metadata_editor = is_toggled_in_metadata_editor

    def __repr__(self):
        return self.label


class Roles(enum.Enum):
    """Roles with their `label`, `is_required`, `is_multivalue`, `is_toggled_in_metadata_editor"""

    OWNER = Role("Owner", True, False, False)
    METADATA_AUTHOR = Role("Metadata Author", True, True, True)
    PROCESSOR = Role("Processor", False, True, True)
    PUBLISHER = Role("Publisher", False, True, True)
    CUSTODIAN = Role("Custodian", False, True, True)
    POC = Role("Point of Contact", True, True, False)
    DISTRIBUTOR = Role("Distributor", False, True, True)
    RESOURCE_USER = Role("Resource User", False, True, True)
    RESOURCE_PROVIDER = Role("Resource Provider", False, True, True)
    ORIGINATOR = Role("Originator", False, True, True)
    PRINCIPAL_INVESTIGATOR = Role("Principal Investigator", False, True, True)

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

    @property
    def is_toggled_in_metadata_editor(self):
        return self.value.is_toggled_in_metadata_editor

    def __repr__(self):
        return self.name

    @classmethod
    def get_required_ones(cls):
        return [role for role in cls if role.is_required]

    @classmethod
    def get_multivalue_ones(cls):
        return [role for role in cls if role.is_multivalue]

    @classmethod
    def get_toggled_ones(cls):
        return [role for role in cls if role.is_toggled_in_metadata_editor]
