#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from rest_framework.exceptions import APIException


class SourceUnavailable(APIException):
    """The source could not be reached or read, the cause is logged and never returned"""

    status_code = 502
    default_detail = "Could not reach the source."
    default_code = "source_unavailable"


class GeoServerUnavailable(APIException):
    """The local GeoServer refused or did not answer, the cause is logged and never returned"""

    status_code = 502
    default_detail = "Could not reach GeoServer."
    default_code = "geoserver_unavailable"
