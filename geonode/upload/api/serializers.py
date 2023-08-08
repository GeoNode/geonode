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

from geonode.upload.models import (
    UploadParallelismLimit,
    UploadSizeLimit,
)
from geonode.base.api.serializers import BaseDynamicModelSerializer

import logging

logger = logging.getLogger(__name__)


class UploadSizeLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadSizeLimit
        name = "upload-size-limit"
        view_name = "upload-size-limits-list"
        fields = (
            "slug",
            "description",
            "max_size",
            "max_size_label",
        )


class UploadParallelismLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadParallelismLimit
        name = "upload-parallelism-limit"
        view_name = "upload-parallelism-limits-list"
        fields = (
            "slug",
            "description",
            "max_number",
        )
        read_only_fields = ("slug",)
