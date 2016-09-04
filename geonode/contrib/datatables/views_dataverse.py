from __future__ import print_function

import traceback
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from geonode.contrib.basic_auth_decorator import http_basic_auth_for_api

from django.views.decorators.http import require_POST

from geonode.maps.models import Layer
from geonode.contrib.datatables.models import TableJoin, LatLngTableMappingRecord
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from geonode.contrib.datatables.column_checker import ColumnHelper

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
from geonode.contrib.datatables.name_helper import standardize_column_name

from geonode.contrib.datatables.utils import attempt_tablejoin_from_request_params,\
    attempt_datatable_upload_from_request_params
from geonode.contrib.datatables.utils_lat_lng import create_point_col_from_lat_lon

from geonode.contrib.msg_util import *
from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text


import logging
LOGGER = logging.getLogger(__name__)

"""
Connecting the Dataverse to the WorldMap's Tabular API
- APIs using GeoConnect for authentication
    (Dataverse <-> GeoConnect <-> WorldMap)
"""


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
    LOGGER.info('Upload a tabular file originating from Dataverse/Geoconnect and join it to a layer.')
    LOGGER.info('Step 1:  Is the Dataverse Layer Metadata valid?')
    # -------------------------------------------
    # Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    form_dv_metadata = DataverseLayerMetadataValidationForm(post_data_dict)
    if not form_dv_metadata.is_valid():
        LOGGER.error('check_for_existing_layer. failed validation')
        LOGGER.error('Errors: %s' % form_dv_metadata.errors)
        #raise forms.ValidationError('Failed to validate dataverse_info data')
        json_msg = MessageHelperJSON.get_json_fail_msg('Failed to validate dataverse_info data',
                                                       data_dict=form_dv_metadata.errors)

        return HttpResponse(json_msg, mimetype="application/json", status=400)


    # -------------------------------------------
    # Does a layer already exist for this DataverseInfo?
    # -------------------------------------------
    msg('step 2')
    LOGGER.info('Step 2:  Does a layer already exist for this DataverseInfo?')

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**post_data_dict)

    #-----------------------------------------------------------
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        msg("Found existing layer!")
        LOGGER.info("Found existing layer!")


        metadata_dict = get_layer_and_join_metadata(existing_dv_layer_metadata.map_layer)
        json_msg = MessageHelperJSON.get_json_msg(success=True,\
                        msg='A layer already exists for the join.',\
                         data_dict=metadata_dict)
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # Is the Upload and join info valid?
    # -------------------------------------------
    msg('step 3')
    LOGGER.info("Step 3: Is the Upload and join info valid?")

    form_upload_and_join = TableUploadAndJoinRequestForm(post_data_dict, request.FILES)
    if not form_upload_and_join.is_valid():

        json_msg = MessageHelperJSON.get_json_fail_msg(\
                        "Invalid Data for Upload and Join: %s" % form_upload_and_join.errors)

        return HttpResponse(status=400, content=json_msg, content_type="application/json")

    # ----------------------------------------------------
    # Does the DataTable join column need to be char?
    #  - Check if the existing target join column is char?
    # ----------------------------------------------------
    (check_worked, force_char_convert) = ColumnHelper.is_char_column_conversion_recommended(\
                form_upload_and_join.cleaned_data['layer_name'],\
                form_upload_and_join.cleaned_data['layer_attribute'])

    if not check_worked:
        err_msg = 'Could not check the target column type'
        LOGGER.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    if force_char_convert:  # It is, make sure the Datatable col will be char
        force_char_column = post_data_dict['table_attribute']
    else:                   # Nope, let the datatable col stand, good or bad
        force_char_column = None

    # ----------------------------------------------------
    # Attempt to upload the table
    # ----------------------------------------------------
    LOGGER.info("Step 4: Attempt to UPLOAD the table")
    (success, data_table_or_error) = attempt_datatable_upload_from_request_params(request,\
                                        request.user,\
                                        is_dataverse_db=True,\
                                        force_char_column=force_char_column)
    if not success:
        json_msg = MessageHelperJSON.get_json_fail_msg(data_table_or_error)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # ----------------------------------------------------
    # Attempt to join the table
    # ----------------------------------------------------
    LOGGER.info("Step 5: Prepare to JOIN the table")

    new_datatable = data_table_or_error
    join_props = request.POST.copy()

    # Update attributes for the join, including the name of the new DataTable
    #
    join_props['table_name'] = data_table_or_error.table_name
    original_table_attribute = join_props['table_attribute']
    sanitized_table_attribute = standardize_column_name(original_table_attribute)
    join_props['table_attribute'] = sanitized_table_attribute

    # ---------------------------------
    # Make the join!
    # ---------------------------------
    LOGGER.info("Step 6: Make the JOIN to the table")

    (success, tablejoin_obj_or_err_msg) = attempt_tablejoin_from_request_params(join_props, request.user)

    if not success: # FAILED!
        new_datatable.delete()  # remove the datatable

        LOGGER.error('Failed join!: %s', tablejoin_obj_or_err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(tablejoin_obj_or_err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # SUCCESS!
    #
    new_tablejoin = tablejoin_obj_or_err_msg
    new_layer = new_tablejoin.join_layer

    # ----------------------------------------------------
    #  Make a new DataverseInfo object and attach it to the Layer
    # ----------------------------------------------------
    LOGGER.info('Step 7: Make a new DataverseInfo object and attach it to the Layer')

    (object_created, err_msg_or_dv_metadata) = create_dataverse_metadata_object(new_layer, post_data_dict)
    if object_created is False:
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg_or_dv_metadata)
        return HttpResponse(status=400, content=json_msg, content_type="application/json")


    # ------------------------------
    # We made it! Send back a JSON response!
    # ------------------------------
    LOGGER.info('Step 8: We made it! Send back a JSON response!')

    layer_metadata_obj = LayerMetadata(new_layer)

    response_params = layer_metadata_obj.get_metadata_dict()
    response_params.update(TableJoinResultForm.get_cleaned_data_from_table_join(new_tablejoin))


    # Return the response!
    json_msg = MessageHelperJSON.get_json_msg(success=True, msg='worked', data_dict=response_params)
    msg('step 8b')
    LOGGER.info('Step 8a: json_msg', json_msg)

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

    LOGGER.info('Upload a lat/lng file originating from Dataverse/Geoconnect and join it to a layer.')
    LOGGER.info('Step 1:  Is the Dataverse Layer Metadata valid?')

    msg('view_upload_lat_lng_table 1')
    # -------------------------------------------
    # (1) Is the Dataverse Layer Metadata valid?
    # -------------------------------------------
    f = DataverseLayerMetadataValidationForm(post_data_dict)
    if not f.is_valid():
        LOGGER.error('check_for_existing_layer. failed validation')
        LOGGER.error('Errors: %s', f.errors)
        json_msg = MessageHelperJSON.get_json_fail_msg('Failed to validate Dataverse metadata',
                                                       data_dict=f.errors)

        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # -------------------------------------------
    # (1b) Does a layer already exist for this DataverseInfo?
    # -------------------------------------------
    msg('step 2')
    LOGGER.info('Step 2:  Does a layer already exist for this DataverseInfo?')

    existing_dv_layer_metadata = retrieve_dataverse_layer_metadata_by_kwargs_installation_and_file_id(**post_data_dict)

    #-----------------------------------------------------------
    #   A layer was found!
    #   Update the DataverseLayerMetadata and return the layer.
    #-----------------------------------------------------------
    if existing_dv_layer_metadata:
        msg("Found existing layer!")
        LOGGER.info("Found existing layer!")

        #update_the_layer_metadata(existing_dv_layer_metadata, post_data_dict)

        metadata_dict = get_layer_and_join_metadata(existing_dv_layer_metadata.map_layer)
        json_msg = MessageHelperJSON.get_json_msg(success=True,\
                        msg='A layer already exists for the join.',\
                         data_dict=metadata_dict)
        return HttpResponse(status=200, content=json_msg, content_type="application/json")


    # -------------------------------------------
    # (2) Is the Lat/Lng request data valid? Check with the MapLatLngLayerRequestForm
    # -------------------------------------------
    LOGGER.info('Step 2:  Is the Lat/Lng request data valid? Check with the MapLatLngLayerRequestForm')
    f = DataTableUploadFormLatLng(request.POST, request.FILES)
    if not f.is_valid():
        err_msg = "Invalid data in request: %s" % format_errors_as_text(f)
        LOGGER.error("datatable_upload_lat_lon_api. %s", err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    #   Set the new table/layer owner
    #
    new_table_owner = request.user


    # --------------------------------------
    # (3) Datatable Upload
    # --------------------------------------
    LOGGER.info('Step 3:  Datatable Upload')
    try:
        # Upload Lat/Lng Datatables to the Monthly table--not the Dataverse table
        #
        resp = datatable_upload_api(request, is_dataverse_db=False)
        upload_return_dict = json.loads(resp.content)
        if upload_return_dict.get('success', None) is not True:
            return HttpResponse(json.dumps(upload_return_dict), mimetype='application/json', status=400)
        else:
            pass # keep going
    except:
        err_msg = 'Uncaught error ingesting Data Table'
        LOGGER.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json_msg, mimetype='application/json', status=400)

    # --------------------------------------
    # (4) Create layer using the Lat/Lng columns
    # --------------------------------------
    LOGGER.info('Step 4: Create layer using the Lat/Lng columns')
    try:
        success, latlng_record_or_err_msg = create_point_col_from_lat_lon(new_table_owner
                        , upload_return_dict['data']['datatable_name']
                        , f.cleaned_data['lat_attribute']
                        , f.cleaned_data['lng_attribute']
                    )


        if not success:
            LOGGER.error('Failed to (2) Create layer for map lat/lng table: %s' % latlng_record_or_err_msg)

            # FAILED
            #
            json_msg = MessageHelperJSON.get_json_fail_msg(latlng_record_or_err_msg)
            return HttpResponse(json_msg, mimetype="application/json", status=400)
        else:
            # -------------------------------------------
            # Add DataverseLayerMetadata object
            # -------------------------------------------
            (object_created, err_msg_or_dv_metadata) = create_dataverse_metadata_object(\
                                        latlng_record_or_err_msg.layer,\
                                        post_data_dict)

            # -------------------------------------------
            # Failed to create DataverseLayerMetadata
            # -------------------------------------------
            if object_created is False:
                # delete LatLngTableMappingRecord
                latlng_record_or_err_msg.delete()

                json_msg = MessageHelperJSON.get_json_fail_msg(err_msg_or_dv_metadata)
                return HttpResponse(status=400, content=json_msg, content_type="application/json")

            # -------------------------------------------
            # Success!  Send user response
            # -------------------------------------------

            # Add DV info
            response_params = get_layer_metadata_dict(latlng_record_or_err_msg.layer,\
                                latlng_record_or_err_msg.as_json())

            json_msg = MessageHelperJSON.get_json_success_msg(\
                            msg='New layer created',\
                            data_dict=response_params)
            return HttpResponse(json_msg, mimetype="application/json", status=200)
    except:
        traceback.print_exc(sys.exc_info())
        err_msg = 'Uncaught error ingesting Data Table'
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        LOGGER.error(err_msg)

        return HttpResponse(json_msg, mimetype="application/json", status=400)



def create_dataverse_metadata_object(new_layer, dv_metadata):
    """
    Create a DataverseInfo object based on a layer name and dv_metadata

    success: (True, DataverseLayerMetadata)
    failed: (False, "user error message")
    """
    if new_layer is None:
        LOGGER.error("new_layer cannot be None")
        return (False, "A layer was not specified.")

    dataverse_layer_metadata = add_dataverse_layer_metadata(new_layer, dv_metadata)
    if dataverse_layer_metadata is None:
        # --------------------
        # Log the error
        # --------------------
        err_msg = "Error.  New map layer created but failed to save Dataverse metadata (new map has been removed)."
        LOGGER.error(err_msg)
        LOGGER.error("New map had name/id %s/%s" % (new_layer_type_name, new_layer.id))

        # --------------------
        # Delete the new layer
        # --------------------
        new_layer.delete()

        return (False, err_msg)

    else:
        return (True, dataverse_layer_metadata)
    #    json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
    #    return HttpResponse(status=400, content=json_msg, content_type="application/json")




def get_layer_metadata_dict(layer, additional_params=None):
    """
    Get the Layer metadata as a dict
    - Add additional parameters such as metadata from a
        table join

    In this case, we already have these objects:
        - Layer (required)
        - dict from LatLngTableMappingRecord (optional)
        - dict from TableJoin (optional)
        etc.
    """
    if not isinstance(layer, Layer):
        LOGGER.error('A Layer object must be specified, not  %s' % type(Layer))
        return None

    layer_metadata_obj = LayerMetadata(layer)

    response_params = layer_metadata_obj.get_metadata_dict()

    if additional_params and len(additional_params) > 1:
        response_params.update(additional_params)

    return response_params


def get_layer_and_join_metadata(layer):
    if not isinstance(layer, Layer):
        LOGGER.error('A Layer object must be specified, not  %s' % type(Layer))
        return None

    additional_params = None

    # Does this layer have an associated TableJoin object?
    if TableJoin.objects.filter(join_layer=layer).count() > 0:
        # Yes!  Grab the metadata
        table_join = TableJoin.objects.filter(join_layer=layer).all()[0]
        additional_params = table_join.as_json()
    elif LatLngTableMappingRecord.objects.filter(layer=layer).count() > 0:
        # Does this layer have an associated LatLngTableMappingRecord object?
        # Yes!  Grab the metadata
        lat_lng_record = LatLngTableMappingRecord.objects.filter(layer=layer).all()[0]
        additional_params = lat_lng_record.as_json()

    # Use the function above to return metadata
    return get_layer_metadata_dict(layer, additional_params)


"""
def get_layer_metadata_by_layer_name(layer_typename):
    if not layer_typename:
        return None

    try:
        layer = Layer.objects.get(typename=layer_typename)
    except Layer.DoesNotExist:
        LOGGER.error('Layer not found: %s' % layer_typename)
        return None

    layer_metadata_obj = LayerMetadata(layer)

    return layer_metadata_obj.get_metadata_dict()
"""
