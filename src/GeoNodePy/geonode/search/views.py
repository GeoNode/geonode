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

    results = []

    for i, result in enumerate(sqs[start:start + limit]):
        data = json.loads(result.json)
        data.update({"iid": i + start})
        results.append(data)

    data = {
        "success": True,
        "total": sqs.count(),
        "rows": results,
    }

    return HttpResponse(json.dumps(data), mimetype="application/json")
