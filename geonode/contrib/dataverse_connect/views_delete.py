import sys
import logging

from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType

from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text

from geoserver.catalog import FailedRequestError

from geonode.core.models import UserObjectRoleMapping
from geonode.maps.models import Layer
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON
from geonode.contrib.dataverse_connect.forms import DataverseLayerIndentityForm
from geonode.contrib.dataverse_layer_metadata.layer_metadata_helper import\
    retrieve_dataverse_layer_metadata_by_installation_and_file_id

from geonode.contrib.basic_auth_decorator import http_basic_auth_for_api
LOGGER = logging.getLogger(__name__)


@csrf_exempt
@http_basic_auth_for_api
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
        LOGGER.error("Delete API. Error: \n%s", format_errors_as_text(delete_form))
        json_msg = MessageHelperJSON.get_json_msg(success=False\
                            , msg="Invalid data for delete request.")
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    LOGGER.info("pre existing layer check")

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_installation_and_file_id(\
                            delete_form.cleaned_data['datafile_id'],
                            delete_form.cleaned_data['dataverse_installation_name'])

    if existing_dv_layer_metadata is None:
        json_msg = MessageHelperJSON.get_json_msg(\
                                        success=False,
                                        msg="Existing layer not found.")
        return HttpResponse(status=404,
                            content=json_msg,
                            content_type="application/json")

    map_layer = existing_dv_layer_metadata.map_layer


    #if not request.user.has_perm('maps.delete_layer', obj=map_layer):
    if request.user != map_layer.owner:
        err_msg = "You are not permitted to delete this Map Layer"
        LOGGER.error(err_msg + ' (id: %s)' % map_layer.id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)


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
    LOGGER.debug("delete the Dataverse Layer Metadata")
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
    """Delete a Dataverse-created Layer object and related UserObjectRoleMapping objects

    If this is a JoinLayer, then also delete the related DataTable
    """
    assert isinstance(map_layer, Layer),\
        "map_layer must be a geonode.maps.models.Layer object"

    if not map_layer.id:
        return (False, "map layer was not saved. (no id found)")

    # Save the id for removing UserObjectRoleMapping objects
    #
    map_layer_id = map_layer.id

    # -----------------------------------------------
    # Is this a part of a join_layer?
    # If so, then delete TableJoin objects
    # -----------------------------------------------
    for table_join_obj in map_layer.join_layer.all():

        # delete the DataTable after the TableJoin object
        related_datatable = table_join_obj.datatable

        table_join_obj.delete()

        if related_datatable:
            related_datatable.delete()

    # -----------------------------------------------
    # Is this a part of a lat/lng mapping record?
    # If so, then delete LatLngTableMappingRecord objects
    # -----------------------------------------------
    for lat_lng_record in map_layer.lat_lng_records.all():

        # delete the DataTable after the TableJoin object
        related_datatable = lat_lng_record.datatable

        lat_lng_record.delete()

        if related_datatable:
            related_datatable.delete()


    try:
        Layer.objects.filter(id=map_layer_id).delete()
    except FailedRequestError as e:
        return (False, "Failed to delete the map.  Error: %s" % e.message)
    except:
        err_msg = "Unexpected error: %s" % sys.exc_info()[0]
        return (False, "ailed to delete the map. %s" % err_msg)

    # -----------------------------------------------
    # If the Layer was deleted,
    # Delete related UserObjectRoleMapping objects
    # -----------------------------------------------
    ctype = ContentType.objects.get_for_model(Layer)
    role_params = dict(object_ct=ctype,
                       object_id=map_layer_id)

    UserObjectRoleMapping.objects.filter(**role_params).delete()

    return (True, None)

"""
import requests, json
server = 'http://127.0.0.1:8000'
api_url = server + '/dataverse/delete-map-layer-test/'
params = { 'layer_id' : 103 }

r = requests.post(api_url, data=params)
print r.text
print r.status_code
"""
