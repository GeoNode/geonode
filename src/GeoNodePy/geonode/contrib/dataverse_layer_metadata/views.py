import logging
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt

from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.contrib.dataverse_layer_metadata.forms import CheckForExistingLayerFormWorldmap

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

logger = logging.getLogger("geonode.contrib.dataverse_layer_metadata.views")


@csrf_exempt
def get_existing_layer_data(request):
    """
    Given a POST with a 'dataverse_installation_name' and 'datafile_id'

    Check if a DataverseLayerMetadata record exists for this information.

    returns JSON
    """
    #   -Auth now checked by CheckForExistingLayerFormWorldmap

    #   Is it a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST, not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")


    #   Does the request contain the correct params?
    #
    f = CheckForExistingLayerFormWorldmap(request.POST)

    if not f.is_valid():
        logger.error("Unexpected form validation error in CheckForExistingLayerFormWorldmap. Errors: %s" % f.errors)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for retrieving an existing layer.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    if not f.is_signature_valid_check_post(request):
        logger.error("Get existing layer API. Error: Invalid signature key")
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
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
    layer_metadata_obj = LayerMetadata(dataverse_layer_metadata.map_layer)

    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())

    return HttpResponse(status=200, content=json_msg, content_type="application/json")



# REMOVED: THE DV_USER_ID ISN'T A GOOD MEASURE.  
#   E.G. DV USER 1 MAKES MAP
#        DV USER 2 WITH EDITING PERMISSIONS MAY NOT BE SEEN AS THE LAYER CREATOR
#
#def view_get_dataverse_user_layers(request):
#    """
#    Send a POST with a 'dv_user_id'
#    
#    Check if a DataverseLayerMetadata record exists for this information.
#    """
