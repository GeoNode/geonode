import json
import urllib
import logging

from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from geonode.dataverse_connect.dataverse_auth import has_proper_auth
from geonode.dataverse_layer_metadata.models import DataverseLayerMetadata

from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

from geonode.dataverse_layer_metadata.layer_metadata_helper import check_for_existing_layer

logger = logging.getLogger(__name__)

@csrf_exempt
def view_delete_dataverse_map_layer(request):
    """
    Allows a Dataverse user to delete a **Dataverse-created** layer.
    
    Dataverse-created layers have a DataverseLayerMetadata object
    
    """
    if not request.POST:
        # Not a POST, pretend it's not here and throw a 404
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Not a POST.")        
        return HttpResponse(status=401, content=json_msg, content_type="application/json")

    
    if not has_proper_auth(request):
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Authentication failed.")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")


    Post_Data_As_Dict = request.POST.dict()


    logger.info("pre existing layer check")

    try:
        existing_dv_layer_metadata = check_for_existing_layer(Post_Data_As_Dict)
        logger.info("found existing layer")
        print "found existing layer"
    except ValidationError as e:
        error_msg = "The dataverse information failed validation: %s" % Post_Data_As_Dict
        logger.error(error_msg)
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="(The WorldMap could not verify the data.)")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    if existing_dv_layer_metadata is None:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Existing layer not found.")        
        return HttpResponse(status=404, content=json_msg, content_type="application/json")
        
        
    map_layer = existing_dv_layer_metadata.map_layer
    
    try:
        map_layer.delete()
    except:
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                                , msg="Failed to delete layer")                                
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='Layer deleted')
    return HttpResponse(status=200, content=json_msg, content_type="application/json")
    
        
    
    
    
