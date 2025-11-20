import logging
import re

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db.models import Q, Subquery
from django.utils.translation import get_language_from_request
from rest_framework import serializers
from rest_framework.filters import BaseFilterBackend

from geonode.indexing.models import ResourceIndex
from geonode.metadata.multilang.utils import get_2letters_languages, get_pg_language


logger = logging.getLogger(__name__)


class AsteriskSearchQuery(SearchQuery):
    def as_sql(self, compiler, connection, function=None, template=None):
        sql, params = super().as_sql(compiler, connection, function, template)
        value = params[1]
        # sanitize search string
        value = re.sub(r"[^0-9A-Za-z/_\.-]+", "", value)
        value = f"{value or '*'}:*"
        return sql, [params[0], value]


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
                .filter(vector=AsteriskSearchQuery(search, config=pg_lang, search_type="raw"))
            )
        )

        return queryset
