import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet

from geonode.maps.views import default_map_config, Map, Layer


def search(request):
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
    #DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)
    # for non-ajax requests, render a generic search page

    params = dict(request.REQUEST)

    map = Map(projection="EPSG:900913", zoom=1, center_x=0, center_y=0)

    # Default Counts to 0, JS will Load the Correct Counts
    counts = {"map": 0, "layer": 0, "vector": 0, "raster": 0, "contact": 0}

    return render_to_response("search/search.html", RequestContext(request, {
        "init_search": json.dumps(params),
        #'viewer_config': json.dumps(map.viewer_json(added_layers=DEFAULT_BASE_LAYERS, authenticated=request.user.is_authenticated())),
        "viewer_config": json.dumps(map.viewer_json(*DEFAULT_BASE_LAYERS)),
        "GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
        "site": settings.SITEURL,
        "counts": counts,
        "keywords": Layer.objects.gn_catalog.get_all_keywords()
    }))


def search_api(request):
    query = request.REQUEST.get("q", "")
    start = int(request.REQUEST.get("start", 0))
    limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20)))
    sort = request.REQUEST.get("sort", "relevance")
    type = request.REQUEST.get("bytype")

    sqs = SearchQuerySet()

    if type is not None:
        if type in ["map", "layer", "contact"]:
            # Type is one of our Major Types (not a sub type)
            sqs = sqs.narrow("type:%s" % type)
        elif type in ["vector", "raster"]:
            # Type is one of our sub types
            sqs = sqs.narrow("subtype:%s" % type)

    if query:
        sqs = sqs.filter(content=AutoQuery(query))

    sqs = sqs.facet("type").facet("subtype")

    if sort.lower() == "newest":
        sqs = sqs.order_by("-date")
    elif sort.lower() == "oldest":
        sqs = sqs.order_by("date")
    elif sort.lower() == "alphaaz":
        sqs = sqs.order_by("title")
    elif sort.lower() == "alphaza":
        sqs = sqs.order_by("-title")

    results = []

    for i, result in enumerate(sqs[start:start + limit]):
        data = json.loads(result.json)
        data.update({"iid": i + start})
        results.append(data)

    facets = sqs.facet_counts()
    counts = {"map": 0, "layer": 0, "vector": 0, "raster": 0, "contact": 0}

    for t, c in facets.get("fields", {}).get("type", []):
        counts[t] = c

    for t, c in facets.get("fields", {}).get("subtype", []):
        counts[t] = c

    data = {
        "success": True,
        "total": sqs.count(),
        "rows": results,
        "counts": counts,
    }

    return HttpResponse(json.dumps(data), mimetype="application/json")
