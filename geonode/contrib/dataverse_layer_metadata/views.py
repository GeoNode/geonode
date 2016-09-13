import logging
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt

from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from geonode.contrib.dataverse_layer_metadata.layer_metadata_helper import                retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id

from shared_dataverse_information.dataverse_info.forms_existing_layer import CheckForExistingLayerForm

from geonode.contrib.datatables.models import LatLngTableMappingRecord

from geonode.contrib.datatables.forms import TableJoinResultForm

logger = logging.getLogger("geonode.contrib.dataverse_layer_metadata.views")
from geonode.contrib.basic_auth_decorator import http_basic_auth_for_api


@csrf_exempt
@http_basic_auth_for_api
def get_existing_layer_data(request):
    """
    Given a POST with a 'dataverse_installation_name' and 'datafile_id'

    Check if a DataverseLayerMetadata record exists for this information.

    returns JSON
    """

    #   Is it a POST?
    #
    if not request.POST:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="The request must be a POST, not GET")
        return HttpResponse(status=401, content=json_msg, content_type="application/json")


    #   Does the request contain the correct params?
    #
    f = CheckForExistingLayerForm(request.POST)

    if not f.is_valid():
        logger.error("Unexpected form validation error in CheckForExistingLayerFormWorldmap. Errors: %s" % f.errors)
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for retrieving an existing layer.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    #   Does a DataverseLayerMetadata object exist for the given params?
    #
    dataverse_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**request.POST.dict())

    #   Nope, we are mapping a new file to the WorldMap
    #
    if dataverse_layer_metadata is None:
        json_msg = MessageHelperJSON.get_json_msg(success=False, msg="This layer does not exist")
        return HttpResponse(status=200, content=json_msg, content_type="application/json")

    # Prepare a JSON response
    #
    map_layer = dataverse_layer_metadata.map_layer
    layer_metadata_obj = LayerMetadata(map_layer)

    data_dict = layer_metadata_obj.get_metadata_dict()

    # Is this a TableJoin, if so, add more data
    if map_layer.join_layer.count() > 0:
        join_layer = map_layer.join_layer.all()[0]
        #data_dict.update(join_layer.as_json())

        data_dict.update(\
            TableJoinResultForm.get_cleaned_data_from_table_join(join_layer)\
            )

    # Was this a Datatable mapped by Lat/Lng
    if LatLngTableMappingRecord.objects.filter(layer=map_layer).count() > 0:
        latlng_record = LatLngTableMappingRecord.objects.filter(layer=map_layer).all()[0]
        data_dict.update(latlng_record.as_json())

    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True,\
                                            msg='worked',\
                                            data_dict=data_dict)

    return HttpResponse(status=200, content=json_msg, content_type="application/json")

"""
from geonode.contrib.dataverse_layer_metadata.models import *
m = DataverseLayerMetadata.objects.get(pk=45)
"""
