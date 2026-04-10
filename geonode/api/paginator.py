#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django.conf import settings
from tastypie.exceptions import BadRequest
from tastypie.paginator import Paginator


class CrossSiteXHRPaginator(Paginator):
    def get_limit(self):
        """
        Determines the proper maximum number of results to return.

        In order of importance, it will use:

            * The user-requested ``limit`` from the GET parameters, if specified.
            * The object-level ``limit`` if specified.
            * ``settings.API_LIMIT_PER_PAGE`` if specified.

        Default is 20 per page.
        """

        limit = self.request_data.get("limit", self.limit)
        if limit is None:
            limit = getattr(settings, "API_LIMIT_PER_PAGE", 20)

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit provided. Please provide a positive integer.")

        if limit < 0:
            raise BadRequest("Invalid limit provided. Please provide a positive integer >= 0.")

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            return self.max_limit

        return limit

    def get_offset(self):
        """
        Determines the proper starting offset of results to return.

        It attempts to use the user-provided ``offset`` from the GET parameters,
        if specified. Otherwise, it falls back to the object-level ``offset``.

        Default is 0.
        """
        offset = self.offset

        if "offset" in self.request_data:
            offset = self.request_data["offset"]

        try:
            offset = int(offset)
        except ValueError:
            raise BadRequest("Invalid offset provided. Please provide an integer.")

        if offset < 0:
            raise BadRequest("Invalid offset provided. Please provide a positive integer >= 0.")

        return offset
