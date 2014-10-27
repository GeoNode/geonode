import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from geonode.dvn.dataverse_auth import has_proper_auth
from geonode.dvn.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.dataverse_layer_metadata.forms import CheckForExistingLayerForm, CheckForDataverseUserLayersForm

from geonode.dvn.dv_utils import MessageHelperJSON          # format json response object

logger = logging.getLogger("geonode.dataverse_layer_metadata.views")


@csrf_exempt
def view_get_dataverse_user_layers(request):
    """
    Send a POST with a 'dv_user_id' 
    
    Check if a DataverseLayerMetadata record exists for this information.
    """
    #   Does it have proper auth?
    #
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #   Is it a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST, not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")
    
    #   Does the request contain the correct params?
    #
    f = CheckForDataverseUserLayersForm(request.POST)

    if not f.is_valid():
       logger.error("Unexpected form validation error in add_dataverse_layer_metadata. dvn import: %s" % f.errors)
       json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request did not validate.  Expected a 'dv_user_id'")
       return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #   Does a DataverseLayerMetadata object exist for the given params?
    #
    metadata_objects = f.get_dataverse_layer_metadata_objects()

    metadata_list = []
    for mo in metadata_objects:
        layer_metadata_obj = LayerMetadata(**{ 'geonode_layer_object' : mo.map_layer })
        metadata_list.append(layer_metadata_obj.get_metadata_dict())
    
    if len(metadata_list) == 0:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg='No map layers found')
        return HttpResponse(status=200, content=json_msg, content_type="application/json")
        
    
    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=metadata_list)
    return HttpResponse(status=200, content=json_msg, content_type="application/json")

    
    
@csrf_exempt
def get_existing_layer_data(request):
    """
    Given a POST with a 'dv_user_id' and 'datafile_id'
    
    Check if a DataverseLayerMetadata record exists for this information.
    
    returns JSON
    """
    #   Does it have proper auth?
    #
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #   Is it a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST, not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")


    #   Does the request contain the correct params?
    #
    f = CheckForExistingLayerForm(request.POST)

    if not f.is_valid():
        logger.error("Unexpected form validation error in add_dataverse_layer_metadata. dvn import: %s" % f.errors)
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request did not validate.  Expected a 'dv_user_id' and 'datafile_id'")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    #   Does a DataverseLayerMetadata object exist for the given params?
    #
    dataverse_layer_metadata = f.get_latest_dataverse_layer_metadata()

    #   Nope, we are mapping a new file to the WorldMap
    #
    if dataverse_layer_metadata is None:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="This layer does not exist")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    # Prepare a JSON response
    #
    layer_metadata_obj = LayerMetadata(**{ 'geonode_layer_object' : dataverse_layer_metadata.map_layer })

    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())

    return HttpResponse(status=200, content=json_msg, content_type="application/json")


