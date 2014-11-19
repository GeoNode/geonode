import json
import logging

from django.core.handlers import wsgi
from django.template import RequestContext

from django.http import HttpResponse, HttpRequest
from django.core.urlresolvers import reverse

from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt

from django.contrib.sites.models import Site

from dataverse_info.forms_embed_layer import EmbedLayerForm

from geonode.maps.models import Layer
from geonode.maps.views import newmap_config, snapshot_config

from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response objectRegisteredApplication, 

from geonode.dataverse_private_layer.models import RegisteredApplication, WorldMapToken


logger = logging.getLogger("geonode.dataverse_private_layer.views_request_private_layer_url")


'''
def view_quick_test(request):
    """
    http://localhost:8000/dataverse-private-layer/proxy-test/

    http://localhost:8080/geoserver/wms?LAYERS=geonode%3Abari_q1y&VERSION=1.1.1&REQUEST=DescribeLayer
    http://localhost:8080/geoserver/wms?LAYERS=geonode%3A' bari_q1y' &VERSION=1.1.1&REQUEST=DescribeLayer

    """
    from geonode.proxy.views import proxy

    layer_name = 'geonode%3Abari_q1y'
    test_url='http://localhost:8080/geoserver/wms?LAYERS=' + layer_name + '&VERSION=1.1.1&REQUEST=DescribeLayer'
    print 'test_url', test_url
    request.GET = dict(url=test_url)
    return proxy(request)
'''

'''
def view_proxy_test2(request):
    from geonode.proxy.views import internal_proxy

    layer_name = 'geonode%3Abari_q1y'
    test_url='http://localhost:8080/geoserver/wms?LAYERS=' + layer_name + '&VERSION=1.1.1&REQUEST=DescribeLayer'
    print 'test_url', test_url
    return internal_proxy(request, test_url)
'''


'''
#
# 11/19/2014 - abandoned attempt to show private layers via a temporary url
#
#
def format_embed_layer_error(request, err_msg):
    assert type(request) in (HttpRequest, wsgi.WSGIRequest), 'request must be a HttpRequest or WSGIRequest object'
    assert err_msg is not None, "err_msg cannot be None"
    
    json_msg = MessageHelperJSON.get_json_msg(success=False, msg=err_msg)
    return HttpResponse(status=200, content=json_msg, content_type="application/json")
    

    #return render_to_response('dataverse_layer_metadata/view_embed_layer_error.html'\
    #                         , dict(err_msg=err_msg)\
    #                        , context_instance=RequestContext(request))



@csrf_exempt
def view_request_private_layer_url(request):
    """
    Send an EmbedLayerForm in JSON format via POST
    
    AJAX: Return a link to an embedded map or an error message
    """
    print ('view_embedded_layer 1')

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
    #
    layer_name = f.cleaned_data.get('layer', None)
    
    print ('layer_name', layer_name)
    try:
        layer_obj = Layer.objects.get(name=layer_name)
    except Layer.DoesNotExist:
        logger.error("Layer does not exist: %s" % layer_name)
        err_msg = "The layer '%s' was not found." % layer_name
        return format_embed_layer_error(request, err_msg)
    
    print ('view_embedded_layer 6')

    # Does Layer have an associated DataverseLayerMetadata object?
    #
    if not layer_obj.dataverselayermetadata_set.exists():
        err_msg = "The layer was not from the Dataverse."
        return format_embed_layer_error(request, err_msg)

    print ('view_embedded_layer 7')
    dataverse_layer_metadata_obj = layer_obj.dataverselayermetadata_set.all()[0]
    match_dict = dict(dv_user_id=dataverse_layer_metadata_obj.dv_user_id\
                    , datafile_id=dataverse_layer_metadata_obj.datafile_id)


    print ('view_embedded_layer 8')
    #  Do attributes match between the JSON data sent and 
    #   the local DataverseLayerMetadata object?
    #       - only matching on dv_user_id and datafile_id
    #
    if not f.do_attributes_match(**match_dict):
        err_msg = "Sorry! The layer does not match this file."
        return format_embed_layer_error(request, err_msg)
    
    
    #   Create view embed layer url
    #    
    
    # Create a token
    registered_application = RegisteredApplication.objects.all()[0]
    dv_token = WorldMapToken.get_new_token(registered_application\
                                            , dataverse_layer_metadata_obj\
                                            , layer_obj)
    
    private_layer_url = reverse('view_private_layer', kwargs={ 'wm_token' : dv_token.token })
    private_layer_url = '%s%s' % (Site.objects.get_current().domain, private_layer_url)
    
    json_msg = MessageHelperJSON.get_json_msg(success=True
                                            , msg='It worked'\
                                            , data_dict=dict(private_layer_url=private_layer_url)\
                                            )
    return HttpResponse(status=200, content=json_msg, content_type="application/json")
    return HttpResponse(private_layer_url)
'''
    
