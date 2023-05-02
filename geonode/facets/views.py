import logging
from urllib.parse import urlencode
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes

from django.http import HttpResponseNotFound, JsonResponse
from django.urls import reverse

from geonode.base.models import ResourceBase
from geonode.facets.apps import registered_facets
from geonode.facets.models import FacetProvider, DEFAULT_FACET_TOPICS_LIMIT
from geonode.security.utils import get_visible_resources

logger = logging.getLogger(__name__)


def list_facets(request, **kwargs):
    lang = _resolve_language(request)
    add_links = _resolve_boolean(request, "add_links", False)
    include_topics = _resolve_boolean(request, "include_topics", False)

    facets = []

    for provider in registered_facets.values():
        logger.debug("Fetching data from provider %r", provider)
        info = provider.get_info(lang=lang)
        if add_links:
            info["link"] = f"{reverse('get_facet', args=[info['name']])}?{urlencode({'add_links': True})}"

        if include_topics:
            content = provider.get_facet_items(queryset=_prefilter_topics(request))
            info["topics"] = content

        facets.append(info)

    logger.debug("Returning facets %r", facets)
    return JsonResponse({"facets": facets})


@api_view(["GET"])
@authentication_classes([SessionAuthentication, BasicAuthentication])
def get_facet(request, facet):
    logger.debug("get_facet -> %r", facet)
    lang = _resolve_language(request)
    add_link = _resolve_boolean(request, "add_links", False)

    provider: FacetProvider = registered_facets.get(facet)
    if not provider:
        return HttpResponseNotFound()

    page = int(request.GET.get("page", 0))
    limit = int(request.GET.get("limit", DEFAULT_FACET_TOPICS_LIMIT))

    info = provider.get_info(lang)
    info["user"] = request.user.username

    qs = _prefilter_topics(request)
    content = provider.get_facet_items(queryset=qs, lang=lang, page=page, limit=limit)

    if add_link:
        exist_prev = page > 0
        exist_next = content["total"] > (page + 1) * limit
        link = reverse("get_facet", args=[info["name"]])
        info["prev"] = f'{link}?{urlencode({"limit": limit, "page": page-1, "add_links":True})}' if exist_prev else None
        info["next"] = f'{link}?{urlencode({"limit": limit, "page": page+1, "add_links":True})}' if exist_next else None

    info["topics"] = content

    return JsonResponse(info)


def _prefilter_topics(request):
    return get_visible_resources(ResourceBase.objects, request.user)


def _resolve_language(request):
    # first try with an explicit request using params
    if lang := request.GET.get("lang", None):
        return lang
    # 2nd try: use LANGUAGE_CODE
    return request.LANGUAGE_CODE.split("-")[0]


def _resolve_boolean(request, name, fallback=None):
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
