#########################################################################
#
# Copyright (C) 2022 OSGeo
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


class DuplicateGeoAppException(APIException):
    status_code = 409
    default_detail = "GeoApp already exists"
    default_code = "geoapp_exception"
    category = "geoapp_api"


class InvalidGeoAppException(APIException):
    status_code = 400
    default_detail = "The provided data is not valid"
    default_code = "geoapp_exception"
    category = "geoapp_api"


class GeneralGeoAppException(APIException):
    status_code = 500
    default_detail = "An error has occurred while processing your request"
    default_code = "geoapp_exception"
    category = "geoapp_api"
