from __future__ import print_function

import traceback
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from geonode.contrib.basic_auth_decorator import http_basic_auth_for_api

from geonode.maps.models import Layer

from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata

from geonode.contrib.dataverse_layer_metadata.forms import\
        DataverseLayerMetadataValidationForm

from geonode.contrib.datatables.forms import DataTableUploadFormLatLng

from geonode.contrib.datatables.views import datatable_upload_api
#from geonode.contrib.datatables.forms import JoinTargetForm,\
#                                        TableUploadAndJoinRequestForm,\
#                                        DataTableResponseForm,\
#                                        TableJoinResultForm,\
#                                        DataTableUploadFormLatLng
from geonode.contrib.dataverse_layer_metadata.layer_metadata_helper import add_dataverse_layer_metadata,\
                retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id



from geonode.contrib.datatables.forms import TableUploadAndJoinRequestForm,\
                                        TableJoinResultForm

from geonode.contrib.datatables.utils import create_point_col_from_lat_lon,\
    standardize_name,\
    attempt_tablejoin_from_request_params,\
    attempt_datatable_upload_from_request_params

from geonode.contrib.msg_util import *


import logging
logger = logging.getLogger(__name__)

"""
Connecting the Dataverse to the WorldMap's Tabular API
- APIs using GeoConnect for authentication
    (Dataverse <-> GeoConnect <-> WorldMap)
"""
from django.views.decorators.http import require_POST

@http_basic_auth_for_api
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
    logger.info('Upload a tabular file originating from Dataverse/Geoconnect and join it to a layer.')
    logger.info('Step 1:  Is the Dataverse Layer Metadata valid?')
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
    logger.info('Step 2:  Does a layer already exist for this DataverseInfo?')

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**post_data_dict)

    #-----------------------------------------------------------
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #-----------------------------------------------------------
    #if existing_dv_layer_metadata:
    #    msg("Found existing layer!")
    #    logger.info("Found existing layer!")

    #    #update_the_layer_metadata(existing_dv_layer_metadata, post_data_dict)

    #    layer_metadata_obj = LayerMetadata(existing_dv_layer_metadata.map_layer)

    #    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='A layer already exists for the join.', data_dict=layer_metadata_obj.get_metadata_dict())
    #    return HttpResponse(status=200, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # Is the Upload and join info valid?
    # -------------------------------------------
    msg('step 3')
    logger.info("Step 3: Is the Upload and join info valid?")

    form_upload_and_join = TableUploadAndJoinRequestForm(post_data_dict, request.FILES)
    if not form_upload_and_join.is_valid():

        json_msg = MessageHelperJSON.get_json_fail_msg(\
                        "Invalid Data for Upload and Join: %s" % form_upload_and_join.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # ----------------------------------------------------
    # Attempt to upload the table
    # ----------------------------------------------------
    logger.info("Step 4: Attempt to UPLOAD the table")
    (success, data_table_or_error) = attempt_datatable_upload_from_request_params(request, request.user)
    if not success:
        json_msg = MessageHelperJSON.get_json_fail_msg(data_table_or_error)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # ----------------------------------------------------
    # Attempt to join the table
    # ----------------------------------------------------
    logger.info("Step 5: Prepare to JOIN the table")

    new_datatable = data_table_or_error
    join_props = request.POST.copy()

    # Update attributes for the join, including the name of the new DataTable
    #
    join_props['table_name'] = data_table_or_error.table_name
    original_table_attribute = join_props['table_attribute']
    sanitized_table_attribute = standardize_name(original_table_attribute)
    join_props['table_attribute'] = sanitized_table_attribute

    # ---------------------------------
    # Make the join!
    # ---------------------------------
    logger.info("Step 6: Make the JOIN to the table")

    (success, tablejoin_obj_or_err_msg) = attempt_tablejoin_from_request_params(join_props, request.user)

    if not success: # FAILED!
        new_datatable.delete()  # remove the datatable

        msg('Failed join!: %s' % tablejoin_obj_or_err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(tablejoin_obj_or_err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # SUCCESS!
    #
    new_tablejoin = tablejoin_obj_or_err_msg
    new_layer = new_tablejoin.join_layer

    # ----------------------------------------------------
    #  Make a new DataverseInfo object and attach it to the Layer
    # ----------------------------------------------------
    logger.info('Step 7: Make a new DataverseInfo object and attach it to the Layer')

    dataverse_layer_metadata = add_dataverse_layer_metadata(new_layer, post_data_dict)
    if dataverse_layer_metadata is None:
        # Log the error
        err_msg = "Error.  New map layer created but failed to save Dataverse metadata (new map has been removed)."
        logger.error(err_msg)
        logger.error("New map had name/id %s/%s" % (new_layer_type_name, new_layer.id))

        # --------------------
        # Delete the new layer, also remove the TableJoin
        # --------------------
        new_layer.delete()

        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # ------------------------------
    # We made it! Send back a JSON response!
    # ------------------------------
    logger.info('Step 8: We made it! Send back a JSON response!')

    layer_metadata_obj = LayerMetadata(new_layer)

    response_params = layer_metadata_obj.get_metadata_dict()
    response_params.update(TableJoinResultForm.get_cleaned_data_from_table_join(new_tablejoin))


    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=response_params)
    msg('step 8b')
    logger.info('Step 8a: json_msg', json_msg)

    msg('json_msg: %s' % json_msg)
    return HttpResponse(status=200, content=json_msg, content_type="application/json")


@http_basic_auth_for_api
@csrf_exempt
def view_upload_lat_lng_table(request):

    msg('view_upload_lat_lng_table 0')
    # -------------------------------------------
    # Is it a POST?
    # -------------------------------------------
    if not request.method == 'POST':
        json_msg = MessageHelperJSON.get_json_fail_msg("Unsupported Method")
        return HttpResponse(json_msg, mimetype="application/json", status=500)


    post_data_dict = request.POST.dict()

    logger.info('Upload a lat/lng file originating from Dataverse/Geoconnect and join it to a layer.')
    logger.info('Step 1:  Is the Dataverse Layer Metadata valid?')

    msg('view_upload_lat_lng_table 1')
    # -------------------------------------------
    # (1) Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    f = DataverseLayerMetadataValidationForm(post_data_dict)
    if not f.is_valid():
        logger.error('check_for_existing_layer. failed validation')
        logger.error('Errors: %s', f.errors)
        json_msg = MessageHelperJSON.get_json_fail_msg('Failed to validate Dataverse metadata',
                                                       data_dict=f.errors)

        return HttpResponse(json_msg, mimetype="application/json", status=400)


    # -------------------------------------------
    # (1b) Does a layer already exist for this DataverseInfo?
    # -------------------------------------------
    msg('step 2')
    logger.info('Step 2:  Does a layer already exist for this DataverseInfo?')

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**post_data_dict)

    #-----------------------------------------------------------
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        msg("Found existing layer!")
        logger.info("Found existing layer!")

        #update_the_layer_metadata(existing_dv_layer_metadata, post_data_dict)

        layer_metadata_obj = LayerMetadata(existing_dv_layer_metadata.map_layer)

        json_msg = MessageHelperJSON.get_json_msg(success=True, msg='A layer already exists for the join.', data_dict=layer_metadata_obj.get_metadata_dict())
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # (2) Is the Lat/Lng request data valid? Check with the MapLatLngLayerRequestForm
    # -------------------------------------------
    logger.info('Step 2:  Is the Lat/Lng request data valid? Check with the MapLatLngLayerRequestForm')
    f = DataTableUploadFormLatLng(request.POST, request.FILES)
    if not f.is_valid():
        err_msg = "Invalid data in request: %s" % format_errors_as_text(f)
        logger.error("datatable_upload_lat_lon_api. %s", err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    #   Set the new table/layer owner
    #
    new_table_owner = request.user


    # --------------------------------------
    # (3) Datatable Upload
    # --------------------------------------
    logger.info('Step 3:  Datatable Upload')
    try:
        resp = datatable_upload_api(request)
        upload_return_dict = json.loads(resp.content)
        if upload_return_dict.get('success', None) is not True:
            return HttpResponse(json.dumps(upload_return_dict), mimetype='application/json', status=400)
        else:
            pass # keep going
    except:
        err_msg = 'Uncaught error ingesting Data Table'
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json_msg, mimetype='application/json', status=400)

    # --------------------------------------
    # (4) Create layer using the Lat/Lng columns
    # --------------------------------------
    logger.info('Step 4: Create layer using the Lat/Lng columns')
    try:
        success, latlng_record_or_err_msg = create_point_col_from_lat_lon(new_table_owner
                        , upload_return_dict['data']['datatable_name']
                        , f.cleaned_data['lat_attribute']
                        , f.cleaned_data['lng_attribute']
                    )


        if not success:
            logger.error('Failed to (2) Create layer for map lat/lng table: %s' % latlng_record_or_err_msg)

            # FAILED
            #
            json_msg = MessageHelperJSON.get_json_fail_msg(latlng_record_or_err_msg)
            return HttpResponse(json_msg, mimetype="application/json", status=400)
        else:
            # SUCCESS
            #

            json_data = latlng_record_or_err_msg.as_json()
            print ('json_data', json_data)

            # Add layer metadata
            layer_typename = json_data.get('layer_typename', None)
            print ('layer_typename', layer_typename)
            layer_metadata = get_layer_metadata(layer_typename)
            print ('layer_metadata', layer_metadata)
            if layer_metadata:
                json_data.update(layer_metadata)

            json_msg = MessageHelperJSON.get_json_success_msg(msg='New layer created', data_dict=json_data)
            return HttpResponse(json_msg, mimetype="application/json", status=200)
    except:
        traceback.print_exc(sys.exc_info())
        err_msg = 'Uncaught error ingesting Data Table'
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        logger.error(err_msg)

        return HttpResponse(json_msg, mimetype="application/json", status=400)



def get_layer_metadata(layer_typename):
    if not layer_typename:
        return None

    try:
        layer = Layer.objects.get(typename=layer_typename)
    except Layer.DoesNotExist:
        logger.error('Layer not found: %s' % layer_typename)
        return None

    layer_metadata_obj = LayerMetadata(layer)

    return layer_metadata_obj.get_metadata_dict()
