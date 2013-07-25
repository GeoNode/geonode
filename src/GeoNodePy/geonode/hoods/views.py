"""
This module is a custom tool to integrate with an online neighborhood mapping site created
by the Boston Resource Authority.  It is not necessary for standard WorldMap functionality.
"""


from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
import httplib2
from django.conf import settings
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
import logging
from urlparse import urlparse
import psycopg2
from geonode.maps.models import Map, LayerStats, Layer
import re
from django.utils import simplejson as json
from django.core.cache import cache
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
        'DB_DATASTORE' : settings.DB_DATASTORE,
        'maptitle': mapTemplate.title,
        }))


def update_hood_map():
    """
    Update the neighborhood template map to be the same as the Boston Research Map
    """
    hood_map = Map.objects.get(id=settings.HOODS_TEMPLATE_ID)
    boston_map = Map.objects.get(officialurl='boston')
    cache.delete('maplayerset_' + str(hood_map.id))
    
    if hood_map is not None:
        hood_layerset = hood_map.layer_set
        boston_layerset = boston_map.layer_set
        boston_count = boston_layerset.count()
        
        groups = json.loads(boston_map.group_params)
        groups.insert(0, {"expanded": "true", "group": "My Neighborhood"})
        hood_map.group_params = json.dumps(groups)
        
        
        for layer in hood_layerset.all():
            if layer.group != 'My Neighborhood':
                layer.delete()
            else:
                layer.stack_order = boston_count
                layer.save()
                boston_count +=1 
                
        for layer in boston_layerset.all():
            layer.id = None
            layer.pk = None
            layer.map = hood_map
            layer.save()
            
        hood_map.save()