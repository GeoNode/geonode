import json
import logging

from django.core.handlers import wsgi
from django.template import RequestContext

from django.http import HttpResponse, HttpRequest

from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from dataverse_info.forms_embed_layer import EmbedLayerForm

from geonode.maps.models import Layer
from geonode.maps.views import newmap_config, snapshot_config

from geonode.dataverse_connect.dataverse_auth import has_proper_auth
from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

logger = logging.getLogger("geonode.dataverse_layer_metadata.views_embed_layer")


def format_embed_layer_error(request, err_msg):
    assert type(request) in (HttpRequest, wsgi.WSGIRequest), 'request must be a HttpRequest or WSGIRequest object'
    assert err_msg is not None, "err_msg cannot be None"

    return render_to_response('dataverse_layer_metadata/view_embed_layer_error.html'\
                             , dict(err_msg=err_msg)\
                            , context_instance=RequestContext(request))


@csrf_exempt
def view_embedded_layer(request):
    """
    Initial pass.  Return the embedded map or an error message
    """
    return HttpResponse('in progress')
    print ('view_embedded_layer 1')
    #   Does it have proper auth?
    #
    #if not has_proper_auth(request):
    #    json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
    #    return HttpResponse(status=401, content=json_msg, content_type="application/json")
    #   Is it a POST?
    #
    if not request.POST:
        err_msg = "The request must be a POST."
        return format_embed_layer_error(request, err_msg)
    print ('view_embedded_layer 2')
        
    #   Is API data valid?  (substitute for "has_proper_auth")
    #
    f = EmbedLayerForm(request.POST)
    print ('view_embedded_layer 3')
    
    if not f.is_valid():
        logger.error("Unexpected form validation error in view_embedded_layer: %s" % f.errors)
        err_msg = "The request did not have valid data."
        return format_embed_layer_error(request, err_msg)
        
    print ('view_embedded_layer 4')
    
    #   Does API data have correct signature?  
    #
    if not f.is_signature_valid_check_post(request):
        print ('bad signature 4a: %s' % f.get_api_signature())
        logger.error("Signature did not match! expectd: %s\npost params:%s" % (f.get_api_signature(), request.POST))
        err_msg = "The request did not have a valid signature."
        print ('view_embedded_layer 4b')
        
        return format_embed_layer_error(request, err_msg)
        
    print ('view_embedded_layer 5')
        
    # Does Layer exist?
    layer_name = f.cleaned_data.get('layer', None)
    try:
        layer_obj = Layer.objects.get(name=layer_name)
    except Layer.DoesNotExist:
        logger.error("Layer does not exist: %s" % layer_name)
        err_msg = "The layer '%s' was not found." % layer_name
        return format_embed_layer_error(request, err_msg)
    print ('view_embedded_layer 6')
    
    # Does Layer have an associated DataverseLayerMetadata object?
    if not layer_obj.dataverselayermetadata_set.exists():
        err_msg = "The layer was not from the Dataverse."
        return format_embed_layer_error(request, err_msg)
    print ('view_embedded_layer 7')
    
    dv_metadata = layer_obj.dataverselayermetadata_set.all()[0]
    match_dict = dict(dv_user_id=dv_metadata.dv_user_id\
                    , datafile_id=dv_metadata.datafile_id)

    print ('view_embedded_layer 8')
    if not f.do_attributes_match(**match_dict):
        err_msg = "Sorry! The layer does not match this file."
        return format_embed_layer_error(request, err_msg)
        
    print ('view_embedded_layer 9')
        
    # Create map config and return map    
    map_config = json.loads(newmap_config(request))
        
    print ('view_embedded_layer 10')
    return render_to_response('maps/embed.html', RequestContext(request, {
        'config': json.dumps(map_config)
    }))


