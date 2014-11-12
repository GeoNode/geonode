import math

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.template import RequestContext
from django.conf import settings

from geonode.maps.utils import forward_mercator

from geonode.dataverse_private_layer.models import WorldMapToken
from geonode.maps.models import Map, MapLayer
from geonode.maps.views import default_map_config, snapshot_config\
                            , additional_layers, category_list

from django.http import QueryDict, HttpRequest

import json

def view_data_file_metadata_base_url(request):
    # place holder in urls file
    raise Http404('not found')
    
    
def view_private_layer(request, wm_token):
    """
    Given a valid token, return metadata about a single datafile
    
    :rtype: JSON
    """
    if wm_token is None:
        raise Http404('no token')
    
    #request.GET = QueryDict('layer=hah')
    #print 'request', request
    #return HttpResponse('ok')

    try:
        worldmap_token = WorldMapToken.objects.get(token=wm_token)
    except WorldMapToken.DoesNotExist:
        raise Http404('The token was not found')
        
    if worldmap_token.has_token_expired():
        return HttpResponse('The token has expired.  Please refresh the page and/or log into dataverse again.')
   
   
    """
    from StringIO import StringIO
    from django.core.handlers.wsgi import WSGIRequest
    interim_request = WSGIRequest({
                        'REQUEST_METHOD': 'GET',
                        'PATH_INFO': '/path?%s' % 'layer=%s' % worldmap_token.map_layer.name,
                        'wsgi.input': StringIO(),\
                        'GET':QueryDict('layer=%s' % worldmap_token.map_layer.name)\
                    })
    """                
    #interim_request = HttpRequest()
    #interim_request.GET = QueryDict('layer=%s' % worldmap_token.map_layer.name)
    request.GET = QueryDict('layer=%s' % worldmap_token.map_layer.name)
    
    map_config = json.loads(build_map_config(request, worldmap_token.map_layer))
    #print ('map_config', map_config)
    #print ('view_embedded_layer 10')
    lookup = { 'config': json.dumps(map_config)\
                    }
    #if False:
    return render_to_response('maps/dataverse_embed/iframed_map.html'\
                            , lookup\
                            , RequestContext(request)\
                            )
                            
    #return HttpResponse('okay')
    
    #return render_to_response('maps/embed.html'\
    #                        , lookup\
    #                        , RequestContext(request))
    
    #return HttpResponse(json_info, content_type="application/json")
   




def build_map_config(request, map_layer):
    '''
    View that creates a new map.

    If the query argument 'copy' is given, the inital map is
    a copy of the map with the id specified, otherwise the
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()

    # (1) Make a Map object
    map_obj = Map(projection="EPSG:900913")
    #layers, groups, bbox = additional_layers(request, map_obj, [map_layer.name])
    
    # Make a MapLayer - from def additional_layers
    #
    groups = []
    bbox = map_layer.llbbox_coords()
    map_layer = MapLayer(
                map = map_obj,
                name = map_layer.typename,
                ows_url = settings.GEOSERVER_BASE_URL + "wms",
                visibility = True, #request.user.has_perm('maps.view_layer', obj=layer),
                styles='',
                #group=group,
                source_params = u'{"ptype": "gxp_gnsource"}',
                layer_params= u'{"tiled":true, "title":" '+ map_layer.title + '", "format":"image/png","queryable":true}')

    layers = [map_layer] 
    
    #
    # END: Make a MapLayer
    #layers = [map_layer]
    #print 'type(map_layer)', type(map_layer)
    #bbox = map_layer.llbbox
    #groups = []
    print 'layers:', layers

    if bbox is not None:
        minx, miny, maxx, maxy = [float(c) for c in bbox]
        x = (minx + maxx) / 2
        y = (miny + maxy) / 2

        center = forward_mercator((x, y))
        if center[1] == float('-inf'):
            center[1] = 0

        if maxx == minx:
            width_zoom = 15
        else:
            width_zoom = math.log(360 / (maxx - minx), 2)
        if maxy == miny:
            height_zoom = 15
        else:
            height_zoom = math.log(360 / (maxy - miny), 2)

        map_obj.center_x = center[0]
        map_obj.center_y = center[1]
        map_obj.zoom = math.ceil(min(width_zoom, height_zoom))

    config = map_obj.viewer_json(request.user, *(DEFAULT_BASE_LAYERS + layers))
    config['map']['groups'] = []
    #for group in groups:
    #    if group not in json.dumps(config['map']['groups']):
    #        config['map']['groups'].append({"expanded":"true", "group":group})

    config['fromLayer'] = True

    config['topic_categories'] = category_list()
    config['edit_map'] = True

    return json.dumps(config)
