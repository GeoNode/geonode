import json

from django.conf import settings
from django.http import HttpResponse

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet


def search_api(request):
    query = request.REQUEST.get("q", "")
    start = int(request.REQUEST.get("start", 0))
    limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20)))

    sqs = SearchQuerySet()

    if query:
        sqs = sqs.filter(content=AutoQuery(query))

    data = {
        "success": True,
        "total": sqs.count(),
        "rows": [json.loads(x.json) for x in sqs[start:start + limit]],
    }

    return HttpResponse(json.dumps(data), mimetype="application/json")
