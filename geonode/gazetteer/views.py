import json
from dicttoxml import dicttoxml
from django.http import HttpResponse
from geonode.gazetteer.utils import getGazetteerResults, getGazetteerEntry, getExternalServiceResults


def search(request, place_name, map=None, layer=None, start_date=None, end_date=None, project=None, services=None, user=None, format='json'):
    """
    Search the Gazetteer and return results in JSON or XML format.
    """
    if not format:
        out_format = 'json'
    else:
        out_format = format.lower()
    if out_format not in ('xml', 'json'):
        out_format = 'json'

    if place_name.isdigit():
        posts = getGazetteerEntry(place_name)
    else:
        posts = getGazetteerResults(place_name, map, layer, start_date, end_date, project, user)
    if services is not None:
        posts.extend(getExternalServiceResults(place_name, services))
    if out_format == 'json':
        return HttpResponse(json.dumps(posts, sort_keys=True, indent=4),
                            content_type="application/json")
    elif out_format == 'xml':
        return HttpResponse(dicttoxml([{'resource': post} for post in posts], attr_type=False, custom_root='response'),
                            content_type="application/xml")
