from __future__ import print_function

import traceback
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from geonode.contrib.basic_auth_decorator import http_basic_auth

from geonode.maps.models import Layer

from geonode.contrib.datatables.forms import TableUploadAndJoinRequestForm
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata

from geonode.contrib.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm
from geonode.contrib.dataverse_layer_metadata.layer_metadata_helper import add_dataverse_layer_metadata,\
                retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id


from geonode.contrib.datatables.views import datatable_upload_and_join_api
from geonode.contrib.msg_util import *

#from .models import DataTable, JoinTarget, TableJoin
#from .utils import process_csv_file, setup_join, create_point_col_from_lat_lon, standardize_name

import logging
logger = logging.getLogger(__name__)

"""
Connecting the Dataverse to the WorldMap's Tabular API
- APIs using GeoConnect for authentication
    (Dataverse <-> GeoConnect <-> WorldMap)
"""
from django.views.decorators.http import require_POST

@http_basic_auth
@login_required
@csrf_exempt
def view_upload_table_and_join_layer(request):
    """
    Upload a tabular file originating from Dataverse/Geoconnect and join it to a layer.

    - Check if the Dataverse Metadata is valid
        - No, error
    - Does a layer already exist for this file?
        - If yes, return it
    - Check if the Table Join POST data is valid
        - No error
    - Attempt to Join the Table
        - Fail, error
    - Create a DataverseInfo object and attach it to the layer
    """
    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=500)

    post_data_dict = request.POST.dict()

    msg('step 1')
    # -------------------------------------------
    # Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    f = DataverseLayerMetadataValidationForm(post_data_dict)
    if not f.is_valid():
        logger.error('check_for_existing_layer. failed validation')
        logger.error('Errors: %s' % f.errors)
        #raise forms.ValidationError('Failed to validate dataverse_info data')
        json_msg = MessageHelperJSON.get_json_fail_msg('Failed to validate dataverse_info data',
                                                       data_dict=form.errors)

        return HttpResponse(json_msg, mimetype="application/json", status=400)


    # -------------------------------------------
    # Does a layer already exist for this DataverseInfo?
    # -------------------------------------------
    msg('step 2')
    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**post_data_dict)

    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #   * Update the worldmap user? *
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        msg("Found existing layer!")
        logger.info("Found existing layer!")

        #update_the_layer_metadata(existing_dv_layer_metadata, post_data_dict)

        layer_metadata_obj = LayerMetadata(existing_dv_layer_metadata.map_layer)

        json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=layer_metadata_obj.get_metadata_dict())
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # Is the Upload and join post valid?
    # -------------------------------------------
    msg('step 3')

    form_upload_and_join = TableUploadAndJoinRequestForm(post_data_dict, request.FILES)
    if not form_upload_and_join.is_valid():

        json_msg = MessageHelperJSON.get_json_fail_msg(\
                        "Invalid Data for Upload and Join: %s" % form_upload_and_join.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # ----------------------------------------------------
    # Attempt to upload and join the table
    # ----------------------------------------------------
    msg('step 4')

    try:
        resp = datatable_upload_and_join_api(request)   # A bit hackish, view calling a view
        upload_response_dict = json.loads(resp.content)
        if not upload_response_dict.get('success', None) is True:
            # Note the "upload_response_dict" already contains a formatted response
            #
            return HttpResponse(json.dumps(upload_response_dict), mimetype='application/json', status=400)
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), mimetype='application/json', status=400)


    # ----------------------------------------------------
    # Get the new layer just created--in a bit of a ham-handed/long-winded way...
    # ----------------------------------------------------
    msg('step 5')

    # (1) Pull the layer name from the dict
    #
    new_layer_type_name = upload_response_dict.get('data', {}).get('layer_typename', None)
    if not new_layer_type_name:
        json_msg = MessageHelperJSON.get_json_fail_msg(
                        "Invalid Data for Upload and Join.  'layer_typename' not found: %s" % upload_response_dict)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    # (2) Get the layer from the db
    #
    try:
        new_layer = Layer.objects.get(typename=new_layer_type_name)
    except Layer.DoesNotExist:
        err_msg = "Error. Join appeared successful but the new map layer was not found: %s" % new_layer_type_name
        logger.error(err_msg)
        logger.error("Could not find data['layer_typename'] in this dict: %s" % upload_return_dict)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    # ----------------------------------------------------
    #  Make a new DataverseInfo object and attach it to the Layer
    # ----------------------------------------------------
    msg('step 6')

    dataverse_layer_metadata = add_dataverse_layer_metadata(new_layer, post_data_dict)
    if dataverse_layer_metadata is None:
        # Log the error
        err_msg = "Error.  New map layer created but failed to save Dataverse metadata (new map has been removed)."
        logger.error(err_msg)
        logger.error("New map had name/id %s/%s" % (new_layer_type_name, new_layer.id))

        # Delete the layer
        new_layer.delete()

        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # ------------------------------
    # We made it! Send back a JSON response!
    # ------------------------------
    msg('step 7')

    layer_metadata_obj = LayerMetadata(new_layer)
    msg('step 7a')

    response_params = layer_metadata_obj.get_metadata_dict()

    #TableJoinResultForm

    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=response_params)
    msg('step 7b')
    msg('json_msg: %s' % json_msg)
    return HttpResponse(status=200, content=json_msg, content_type="application/json")

