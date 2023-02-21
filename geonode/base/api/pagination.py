#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE = getattr(settings, "REST_API_DEFAULT_PAGE", 1)
DEFAULT_PAGE_SIZE = getattr(settings, "REST_API_DEFAULT_PAGE_SIZE", 10)
DEFAULT_PAGE_QUERY_PARAM = getattr(settings, "REST_API_DEFAULT_PAGE_QUERY_PARAM", "page_size")


class GeoNodeApiPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = DEFAULT_PAGE_QUERY_PARAM

    def get_paginated_response(self, data):
        _paginated_response = {
            "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
            "total": self.page.paginator.count,
            "page": int(self.request.GET.get("page", DEFAULT_PAGE)),  # can not set default = self.page
            DEFAULT_PAGE_QUERY_PARAM: int(self.request.GET.get(DEFAULT_PAGE_QUERY_PARAM, self.page_size)),
        }
        _paginated_response.update(data)
        return Response(_paginated_response)
