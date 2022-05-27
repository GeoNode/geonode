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
import ast
from geonode.favorite.models import Favorite
import logging
from rest_framework.filters import SearchFilter, BaseFilterBackend

from geonode.base.bbox_utils import filter_bbox
from django.db.models import Subquery
from distutils.util import strtobool

logger = logging.getLogger(__name__)


class DynamicSearchFilter(SearchFilter):

    def get_search_fields(self, view, request):
        return request.GET.getlist('search_fields', [])


class ExtentFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.query_params.get('extent'):
            return filter_bbox(queryset, request.query_params.get('extent'))
        return queryset


class FavoriteFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, _):
        if strtobool(request.query_params.get("favorite", 'False')):
            c_types = list({r.polymorphic_ctype.model for r in queryset})
            return queryset.filter(
                pk__in=Subquery(
                    Favorite.objects.values_list("object_id", flat=True)
                    .filter(user=request.user)
                    .filter(content_type__model__in=c_types)
                )
            )
        return queryset


class FacetVisibleResourceFilter(BaseFilterBackend):
    """
    Return Only elements that have a resource assigned.
    """

    def filter_queryset(self, request, queryset, _):
        _filter = {}

        _with_resources = ast.literal_eval(request.GET.get("with_resources", 'False'))

        if _with_resources:
            _filter["id__in"] = [
                _facet.id
                for _facet in queryset
                if _facet.resourcebase_set.exists()
            ]
        elif 'with_resources' in request.GET and not _with_resources:
            # check that the facet has been passed and is false
            _filter["id__in"] = [
                _facet.id
                for _facet in queryset
                if not _facet.resourcebase_set.exists()
            ]

        return queryset.filter(**_filter)
