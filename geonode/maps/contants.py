#########################################################################
#
# Copyright (C) 2021 OSGeo
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
from django.utils.translation import ugettext as _

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10
MAX_MAPS_SEARCH_BATCH_SIZE = 25

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this map.")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this map.")
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this map")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this map.")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this map's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this map.")
_PERMISSION_MSG_UNKNOWN = _("An unknown error has occured.")

MSG_NOT_ALLOWED = _("Not allowed")
MSG_NOT_FOUND = _("Not found")
