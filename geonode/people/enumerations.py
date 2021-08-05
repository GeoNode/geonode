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

from django.utils.translation import ugettext_lazy as _

CONTACT_FIELDS = [
    "name",
    "organization",
    "position",
    "voice",
    "facsimile",
    "delivery_point",
    "city",
    "administrative_area",
    "postal_code",
    "country",
    "email",
    "role"
]

ROLE_VALUES = (
    ('author', _('party who authored the resource')),
    ('processor', _('party who has processed the data in a manner such that the resource has been modified')),
    ('publisher', _('party who published the resource')),
    ('custodian', _('party that accepts accountability and responsibility for the data and ensures \
        appropriate care and maintenance of the resource')),
    ('pointOfContact', _('party who can be contacted for acquiring knowledge about or acquisition of the resource')),
    ('distributor', _('party who distributes the resource')),
    ('user', _('party who uses the resource')),
    ('resourceProvider', _('party that supplies the resource')),
    ('originator', _('party who created the resource')),
    ('owner', _('party that owns the resource')),
    ('principalInvestigator', _('key party responsible for gathering information and conducting research')),
)
