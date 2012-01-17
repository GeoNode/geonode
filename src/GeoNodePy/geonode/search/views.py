import json

from django.http import HttpResponse

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet


def search_api(request):
    query = request.REQUEST.get("q", "")

    sqs = SearchQuerySet()

    if query:
        sqs = sqs.filter(content=AutoQuery(query))

    data = {
        "success": True,
        "total": sqs.count(),
        "rows": [json.loads(x.json) for x in sqs],
    }

    return HttpResponse(json.dumps(data), mimetype="application/json")
