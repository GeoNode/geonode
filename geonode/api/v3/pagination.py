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
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE_SIZE = int(getattr(settings, "REST_API_DEFAULT_PAGE_SIZE", 10))
MAX_PAGE_SIZE = int(getattr(settings, "REST_API_V3_MAX_PAGE_SIZE", 200))


class V3Pagination(PageNumberPagination):
    """Page-number pagination with a hard upper bound.

    ``page_size`` is capped: values above ``max_page_size`` are clamped down by
    DRF rather than rejected. The response envelope is DRF's standard
    ``count``/``next``/``previous``/``results``.
    """

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = MAX_PAGE_SIZE
