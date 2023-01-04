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


class GeneralDatasetException(APIException):
    status_code = 500
    default_detail = "Error during dataset replace."
    default_code = "dataset_exception"
    category = "dataset_api"


class InvalidDatasetException(APIException):
    status_code = 500
    default_detail = "Input payload is not valid"
    default_code = "invalid_dataset_exception"
    category = "dataset_api"


class InvalidMetadataException(APIException):
    status_code = 500
    default_detail = "Input payload is not valid"
    default_code = "invalid_metadata_exception"
    category = "dataset_api"


class MissingMetadataException(APIException):
    status_code = 400
    default_detail = "Metadata is missing"
    default_code = "missing_metadata_exception"
    category = "dataset_api"
