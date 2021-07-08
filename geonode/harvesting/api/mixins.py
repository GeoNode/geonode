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

import logging

from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class UpdateListModelMixin:
    """Adds the `update_list` method to a viewset

    `update_list` is used by `api.routers.ListPatchRouter` in order to allow
    performing PATCH requests against a viewset's `list` endpoint
    """

    def update_list(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()
