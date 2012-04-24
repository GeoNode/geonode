"""
This module is a custom tool to integrate with an online neighborhood mapping site created
by the Boston Resource Authority.  It is not necessary for standard WorldMap functionality.
"""


from django.http import HttpResponse
from django.core.urlresolvers import reverse
import httplib2
import simplejson
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
import logging
from urlparse import urlparse
import psycopg2
from geonode.maps.models import Map, LayerStats, Layer
from geonode.maps.views import *
import re

logger = logging.getLogger("geonode.hoods.views")



def get_hood_center(resource_name, block_ids):
    """
    Do a PostGIS query to calculate the center coordinates of the selected census blocks
    """
    layer = settings.HOODS_TEMPLATE_LAYER
    conn=psycopg2.connect("dbname='" + settings.DB_DATASTORE_DATABASE + "' user='" + settings.DB_DATASTORE_USER + "'  password='" + settings.DB_DATASTORE_PASSWORD + "' port=" + settings.DB_DATASTORE_PORT + " host='" + settings.DB_DATASTORE_HOST + "'")
    try:
        cur = conn.cursor()
        query = "select ST_AsGeoJSON(ST_Centroid(EXTENT(ST_Transform(the_geom,900913)))) as center from \"" + layer + "\" where \"" + settings.HOODS_TEMPLATE_ATTRIBUTE + "\" IN (" + block_ids + ")"
        cur.execute(query)
        rows = cur.fetchall()
        point = json.loads(str(rows[0][0]))
        return point['coordinates']
    except Exception, e:
        logger.error("Error retrieving bbox for PostGIS table %s:%s", resource_name, str(e))
    finally:
        conn.close()

def create_hood(request):
    """
    If logged in and census block id's are passed as a parameter:
        - Create a new map based on the template
        - Calculate the map center based on the selected blocks
        - Add a CQL_FILTER to the census block layer to only show the selected blocks
        - Display the map
    """
    if 'ids' not in request.GET:
        return HttpResponse(
            "The WorldMap Boston Neighborhood Viewer requires a list of census block id's as a parameter.",
            status=400,
            content_type="text/plain"
        )
    request.session["bra_harvard_redirect"] = request.get_full_path()
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/login?next=' + request.get_full_path())

    mapid = settings.HOODS_TEMPLATE_ID
    mapTemplate= get_object_or_404(Map,pk=mapid)
    config = mapTemplate.viewer_json(request.user)
    config['edit_map'] = True


    del config['id']

    #Are these ID's legit? Make sure.
    isLegitIdList = True
    num_ids = request.GET['ids'].split(',')
    for num in num_ids:
        if not num.isdigit():
            isLegitIdList = False

    if isLegitIdList:
        ids = "'" + "','".join(request.GET['ids'].split(',')) + "'"

        #Zoom to selected blocks
        map_center = get_hood_center(settings.HOODS_TEMPLATE_LAYER, ids)
        if map_center is not None:
            config['map']['center'] = map_center

        #default zoom level (BRA layer not visible below this due to scale-dependent rendering)
        config['map']['zoom'] = 16

        for lc in config['map']['layers']:
            if 'name' in lc and settings.HOODS_TEMPLATE_LAYER in lc['name']:
                lc['cql_filter'] = settings.HOODS_TEMPLATE_ATTRIBUTE + ' IN (' + request.GET['ids'] + ')'


    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        'maptitle': mapTemplate.title,
        }))


