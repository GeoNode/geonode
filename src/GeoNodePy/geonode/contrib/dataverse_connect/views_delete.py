import sys
import json
import urllib
import logging

from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text

from geonode.contrib.dataverse_layer_metadata.models import DataverseLayerMetadata

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from geonode.contrib.dataverse_connect.forms import DataverseLayerIndentityForm

from geonode.contrib.dataverse_layer_metadata.layer_metadata_helper import retrieve_dataverse_layer_metadata_by_installation_and_file_id,\
    check_for_existing_layer
from geonode.maps.models import Layer

from geoserver.catalog import FailedRequestError
from django.contrib.auth.decorators import login_required

from geonode.contrib.basic_auth_decorator import http_basic_auth
logger = logging.getLogger(__name__)

'''
#@csrf_exempt
def test_delete(request):
    """
    Used for debugging -- do not activate this and check it in!
    
    #url(r'^delete-map-layer-test/$', 'test_delete', name='test_delete'),
    
    """
    raise Http404('nada')
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Not a POST.")        
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    Post_Data_As_Dict = request.POST.dict()

    print 'request.POST', request.POST
    print 'Post_Data_As_Dict', Post_Data_As_Dict

    if Post_Data_As_Dict.get('layer_id', None) is None:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="No layer_id.")        
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    try:
        layer = Layer.objects.get(pk=Post_Data_As_Dict['layer_id'])
    except Layer.DoesNotExist:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Layer not found for this id.")        
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    #layer.delete()

    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='Layer deleted')
    return HttpResponse(status=200, content=json_msg, content_type="application/json")
'''
"""
import requests, json
server = 'http://127.0.0.1:8000'
api_url = server + '/dataverse/delete-map-layer-test/'
params = { 'layer_id' : 103 }

r = requests.post(api_url, data=params)
print r.text
print r.status_code
"""        
    

@csrf_exempt
@http_basic_auth
@login_required
def view_delete_dataverse_map_layer(request):
    """
    Allows a Dataverse user to delete a **Dataverse-created** layer by specifying:
        - dataverse installation name
        - datafile id

    TO DO: Verify that dataverse named in the params has originated the message...

    """
    if not request.POST:
        # Not a POST, throw a 401
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Not a POST.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    
    """
    Validate the Data in the API call
    """
    delete_form = DataverseLayerIndentityForm(request.POST)
    if not delete_form.is_valid():
        #
        #   Invalid, send back an error message
        #
        logger.error("Delete API. Error: \n%s" % format_errors_as_text(delete_form))
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for delete request.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    logger.info("pre existing layer check")

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_installation_and_file_id(
                                                    delete_form.cleaned_data['datafile_id'],
                                                    delete_form.cleaned_data['dataverse_installation_name']
                                                )
    if existing_dv_layer_metadata is None:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Existing layer not found.")
        return HttpResponse(status=404, content=json_msg, content_type="application/json")
        
    map_layer = existing_dv_layer_metadata.map_layer


    if not request.user.has_perm('maps.delete_layer', obj=map_layer):
        err_msg = "You are not permitted to delete this Map Layer"
        logger.error(err_msg + ' (id: %s)' % map_layer.id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)


    #--------------------------------------
    #print "delete map_layer: %s" % map_layer
    #print "id, type", map_layer.id, type(map_layer)
    #--------------------------------------
    #map_layer.owners.clear()

    #   Note: On dev, layer not always deleting on 1st attempt, try twice
    #
    (success, err_msg) = delete_map_layer(map_layer)        # Delete Attempt #1
    if not success:
        #print 'Delete Attempt #1 failed: %s' % err_msg
        (success2, err_msg2) = delete_map_layer(map_layer)  # Delete Attempt #2
        if not success2:
            #print 'Delete Attempt #2 failed: %s' % err_msg2
            json_msg = MessageHelperJSON.get_json_msg(success=False, msg=err_msg2)
            return HttpResponse(status=400, content=json_msg, content_type="application/json")


    #--------------------------------------
    print "delete existing_dv_layer_metadata"
    #--------------------------------------

    try:
        existing_dv_layer_metadata.delete()
    except:
        err_msg = "Unexpected error:", sys.exc_info()[0]
        #print 'err_msg 1', err_msg

        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Failed to existing_dv_layer_metadata. Error: %s" % err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")



    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='Layer deleted')
    return HttpResponse(status=200, content=json_msg, content_type="application/json")
    

def delete_map_layer(map_layer):
    assert isinstance(map_layer, Layer), "map_layer must be a geonode.maps.models.Layer object"
    
    try:
        map_layer.delete()
    except FailedRequestError as e:
        return (False, "Failed to map_layer.  Error: %s" % e.message)
    except:
         err_msg = "Unexpected error: %s" % sys.exc_info()[0]
         return (False, "Failed to map_layer. %s" % err_msg)

    return (True, None)

    
