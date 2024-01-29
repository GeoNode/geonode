#########################################################################
#
# Copyright (C) 2023 Open Source Geospatial Foundation - all rights reserved
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
from urllib.parse import urlencode

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView

from django.http import HttpResponseNotFound, JsonResponse
from django.urls import reverse
from django.conf import settings

from geonode.base.api.views import ResourceBaseViewSet
from geonode.base.models import ResourceBase
from geonode.facets.models import FacetProvider, DEFAULT_FACET_PAGE_SIZE, facet_registry
from geonode.security.utils import get_visible_resources

PARAM_PAGE = "page"
PARAM_PAGE_SIZE = "page_size"
PARAM_LANG = "lang"
PARAM_ADD_LINKS = "add_links"
PARAM_INCLUDE_TOPICS = "include_topics"
PARAM_INCLUDE_CONFIG = "include_config"
PARAM_TOPIC_CONTAINS = "topic_contains"

logger = logging.getLogger(__name__)


class BaseFacetingView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    @classmethod
    def _get_topics(
        cls,
        provider,
        queryset,
        page: int = 0,
        page_size: int = DEFAULT_FACET_PAGE_SIZE,
        lang: str = "en",
        topic_contains: str = None,
        keys: set = {},
        **kwargs,
    ):
        start = page * page_size
        end = start + page_size

        cnt, items = provider.get_facet_items(
            queryset, start=start, end=end, lang=lang, topic_contains=topic_contains, keys=keys, **kwargs
        )

        if keys:
            keys.difference_update({str(t["key"]) for t in items})
            if keys:
                ext = provider.get_topics(keys, lang)
                items.extend(ext)
                cnt += len(ext)
                logger.debug("Extending facets to %d for %s", cnt, provider.name)

        return {"page": page, "page_size": page_size, "start": start, "total": cnt, "items": items}

    @classmethod
    def _prefilter_topics(cls, request):
        """
        Perform some prefiltering on resources, such as
          - auth visibility
          - filtering by other facets already applied
        :param request:
        :return: a QuerySet on ResourceBase
        """
        logger.debug("Filtering by user '%s'", request.user)
        filters = {k: vlist for k, vlist in request.query_params.lists() if k.startswith("filter{")}
        logger.warning(f"FILTERING BY  {filters}")

        if filters:
            viewset = ResourceBaseViewSet(request=request, format_kwarg={}, kwargs=filters)
            viewset.initial(request)
            return get_visible_resources(queryset=viewset.filter_queryset(viewset.get_queryset()), user=request.user)
        else:
            # return ResourceBase.objects
            return get_visible_resources(ResourceBase.objects, request.user)

    @classmethod
    def _resolve_language(cls, request) -> (str, bool):
        """
        :return: the resolved language, a boolean telling if the language was requested
        """
        # first try with an explicit request using params
        if lang := request.GET.get(PARAM_LANG, None):
            return lang, True
        # 2nd try: use LANGUAGE_CODE
        try:
            return request.LANGUAGE_CODE.split("-")[0], False
        except AttributeError:
            return settings.LANGUAGE_CODE, False

    @classmethod
    def _resolve_boolean(cls, request, name, fallback=None):
        """
        Parse boolean query params
        """
        val = request.GET.get(name, None)
        if val is None:
            return fallback

        val = val.lower()
        if val.startswith("t") or val.startswith("y") or val == "1":
            return True
        elif val.startswith("f") or val.startswith("n") or val == "0":
            return False
        else:
            return fallback


class ListFacetsView(BaseFacetingView):
    def get(self, request, *args, **kwargs):
        lang, lang_requested = self._resolve_language(request)
        add_links = self._resolve_boolean(request, PARAM_ADD_LINKS, False)
        include_topics = self._resolve_boolean(request, PARAM_INCLUDE_TOPICS, False)
        include_config = self._resolve_boolean(request, PARAM_INCLUDE_CONFIG, False)

        facets = []
        prefiltered = None

        for provider in facet_registry.get_providers():
            logger.debug("Fetching data from provider %r", provider)
            info = provider.get_info(lang=lang)

            if include_config:
                info["config"] = provider.config

            if add_links:
                link_args = {PARAM_ADD_LINKS: True}
                if lang_requested:  # only add lang param if specified in current call
                    link_args[PARAM_LANG] = lang
                info["link"] = f"{reverse('get_facet', args=[info['name']])}?{urlencode(link_args)}"

            if include_topics:
                prefiltered = prefiltered or self._prefilter_topics(request)
                info["topics"] = self._get_topics(provider, queryset=prefiltered, lang=lang, user=request.user)

            facets.append(info)

        logger.debug("Returning facets %r", facets)
        return JsonResponse({"facets": facets})


class GetFacetView(BaseFacetingView):
    def get(self, request, facet):
        logger.debug("get_facet -> %r for user '%r'", facet, request.user.username)

        # retrieve provider for the requested facet
        provider: FacetProvider = facet_registry.get_provider(facet)
        if not provider:
            return HttpResponseNotFound()

        # parse some query params
        lang, lang_requested = self._resolve_language(request)
        add_link = self._resolve_boolean(request, PARAM_ADD_LINKS, False)
        include_config = self._resolve_boolean(request, PARAM_INCLUDE_CONFIG, False)

        topic_contains = request.GET.get(PARAM_TOPIC_CONTAINS, None)
        keys = set(request.query_params.getlist("key"))

        page = int(request.GET.get(PARAM_PAGE, 0))
        page_size = int(request.GET.get(PARAM_PAGE_SIZE, DEFAULT_FACET_PAGE_SIZE))

        info = provider.get_info(lang)
        if include_config:
            info["config"] = provider.config

        qs = self._prefilter_topics(request)
        topics = self._get_topics(
            provider,
            queryset=qs,
            page=page,
            page_size=page_size,
            lang=lang,
            topic_contains=topic_contains,
            keys=keys,
            user=request.user,
        )

        if add_link:
            exist_prev = page > 0
            exist_next = topics["total"] > (page + 1) * page_size
            link = reverse("get_facet", args=[info["name"]])
            for exist, link_name, p in (
                (exist_prev, "prev", page - 1),
                (exist_next, "next", page + 1),
            ):
                link_param = {PARAM_PAGE: p, PARAM_PAGE_SIZE: page_size, PARAM_LANG: lang, PARAM_ADD_LINKS: True}
                if lang_requested:  # only add lang param if specified in current call
                    link_param[PARAM_LANG] = lang
                if topic_contains:
                    link_param[PARAM_TOPIC_CONTAINS] = topic_contains
                info[link_name] = f"{link}?{urlencode(link_param)}" if exist else None

        if topic_contains:
            # in the payload let's rmb this is a filtered output
            info["topic_contains"] = topic_contains

        info["topics"] = topics

        return JsonResponse(info)
