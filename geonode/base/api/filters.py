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
import logging
from distutils.util import strtobool
from itertools import groupby

from django.contrib.postgres.search import SearchQuery
from rest_framework import serializers
from rest_framework.filters import SearchFilter, BaseFilterBackend

from django.db.models import Subquery, Q
from django.conf import settings
from django.utils.translation import get_language_from_request

from geonode.base.bbox_utils import filter_bbox
from geonode.base.models import ThesaurusKeyword
from geonode.favorite.models import Favorite
from geonode.indexing.models import ResourceIndex
from geonode.metadata.multilang import get_2letters_languages, get_pg_language

logger = logging.getLogger(__name__)


class DynamicSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        return request.GET.getlist("search_fields", [])


class ExtentFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.query_params.get("extent"):
            return filter_bbox(queryset, request.query_params.get("extent"))
        return queryset


class TKeywordsFilter(BaseFilterBackend):
    """
    TKeywords are a ManyToMany relation but DREST can't handle AND filtering the way we need.
    When the filter has more than one tkeyword, DREST by default will return Resources associated at least to one
    of the keywords.
    """

    def filter_queryset(self, request, queryset, view):
        # we must make the GET mutable since in the filters, some queryparams are popped
        request.GET._mutable = True
        try:
            return (
                self.filter_queryset_GROUP(request, queryset, view)
                if "force_and" not in request.GET
                else self.filter_queryset_AND(request, queryset, view)
            )
        finally:
            request.GET._mutable = False

    def filter_queryset_AND(self, request, queryset, view):
        """
        This implementation requires all the tkeywords to be assigned to the Resource
        """
        for v in request.GET.pop("filter{tkeywords}", []):
            queryset = queryset.filter(tkeywords__id=v)
        return queryset

    def filter_queryset_GROUP(self, request, queryset, view):
        """
        This implementation requires that at least one tkeyword for each thesaurus is assigned to the Resource
        """
        if tklist := request.GET.pop("filter{tkeywords}", None):
            if len(tklist) == 1:
                # if there's only one filtering keyword we don't need to tell to which thesaurus it belongs to
                return queryset.filter(tkeywords__id=tklist[0])

            tkinfo = (
                ThesaurusKeyword.objects.filter(id__in=tklist).values("id", "thesaurus__id").order_by("thesaurus__id")
            )

            for t, tk in groupby(tkinfo, lambda r: r["thesaurus__id"]):
                tklist_by_t = [x["id"] for x in tk]
                logger.info("Filtering by %s - %r keywords", t, tklist_by_t)
                queryset = queryset.filter(tkeywords__id__in=tklist_by_t)

        return queryset


class FavoriteFilter(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, _):
        if strtobool(request.query_params.get("favorite", "False")):
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

        _with_resources = ast.literal_eval(request.GET.get("with_resources", "False"))

        if _with_resources:
            _filter["id__in"] = [_facet.id for _facet in queryset if _facet.resourcebase_set.exists()]
        elif "with_resources" in request.GET and not _with_resources:
            # check that the facet has been passed and is false
            _filter["id__in"] = [_facet.id for _facet in queryset if not _facet.resourcebase_set.exists()]

        return queryset.filter(**_filter)


class ResourceIndexFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        def validate_lang(search_lang):
            if search_lang not in get_2letters_languages():
                logger.warning(f"Unknown search_lang {search_lang}")
                return None
            return search_lang

        search_index = request.query_params.get("search_index", None)
        search = request.query_params.get("search", None)

        if not search_index or not search:
            return queryset

        if request.query_params.getlist("search_fields", None):
            raise serializers.ValidationError("search_index and search_fields are mutually exclusive")

        if search_index not in settings.METADATA_INDEXES:
            raise serializers.ValidationError(f"Unknown index '{search_index}'")

        search_lang = request.query_params.get("search_lang", None)
        if search_lang:
            search_lang = validate_lang(search_lang)
        if not search_lang:
            search_lang = get_language_from_request(request)[:2]
            search_lang = validate_lang(search_lang)

        lang_filter = Q(lang__isnull=True)
        if search_lang:
            lang_filter = lang_filter | Q(lang=search_lang)

        pg_lang = get_pg_language(search_lang)

        queryset = queryset.filter(
            pk__in=Subquery(
                ResourceIndex.objects.values_list("resource_id", flat=True)
                .filter(name=search_index)
                .filter(lang_filter)
                .filter(vector=SearchQuery(search, config=pg_lang))
            )
        )

        logger.debug(queryset.query)
        return queryset
