from __future__ import print_function
import logging
import sys
import json
import traceback
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from geonode.contrib.basic_auth_decorator import http_basic_auth_for_api

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from geonode.contrib.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text

from geonode.contrib.datatables.forms import JoinTargetForm,\
                                        TableUploadAndJoinRequestForm,\
                                        DataTableResponseForm,\
                                        TableJoinResultForm,\
                                        DataTableUploadFormLatLng

#from geonode.contrib.dataverse_connect.layer_metadata import LayerMetadata        # object with layer metadata
from shared_dataverse_information.worldmap_datatables.forms import MapLatLngLayerRequestForm

from geonode.contrib.msg_util import *

from .models import DataTable, JoinTarget, TableJoin, LatLngTableMappingRecord
from geonode.contrib.datatables.name_helper import standardize_column_name

from geonode.contrib.datatables.utils import attempt_tablejoin_from_request_params,\
    attempt_datatable_upload_from_request_params
#from geonode.contrib.datatables.utils_joins import drop_view_from_table_join
from geonode.contrib.datatables.utils_lat_lng import create_point_col_from_lat_lon
from geonode.contrib.datatables.db_helper import get_datastore_connection_string

from geonode.contrib.datatables.column_checker import ColumnHelper

logger = logging.getLogger(__name__)


@http_basic_auth_for_api
@csrf_exempt
def datatable_upload_api(request, is_dataverse_db=True):
    """
    API to upload a datatable -- saved as a DataTable object

    Note: For table joins: is_dataverse_db=True
          For datatables with lat/lng columns: is_dataverse_db=False
    """
    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=405)

    # Note: The User used for auth is set as the DataTable owner
    (success, data_table_or_error) = attempt_datatable_upload_from_request_params(request, request.user, is_dataverse_db)
    if not success:
        json_msg = MessageHelperJSON.get_json_fail_msg(data_table_or_error)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    return_dict = dict(datatable_id=data_table_or_error.pk,
                       datatable_name=data_table_or_error.table_name)
    json_msg = MessageHelperJSON.get_json_success_msg(msg='Success, DataTable created',
                                                      data_dict=return_dict)
    return HttpResponse(json_msg, mimetype="application/json", status=200)



@http_basic_auth_for_api
@csrf_exempt
def datatable_detail(request, dt_id):
    """
    For a given Datatable id, return the Datatable values as JSON
    """
    # get Datatable
    try:
        datatable = DataTable.objects.get(pk=dt_id)
    except DataTable.DoesNotExist:
        err_msg = 'No DataTable object found'
        logger.error(err_msg + 'for id: %s' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=404)

    # Check if the owner is making the request.
    # Note: This a simplified check for geonode 1.2
    #
    if request.user != datatable.owner:
        err_msg = "You are not permitted to view this DataTable object"
        logger.error(err_msg + ' (id: %s)' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    datatable_info = DataTableResponseForm.getDataTableAsJson(datatable)

    json_msg = MessageHelperJSON.get_json_success_msg(msg=None, data_dict=datatable_info)
    return HttpResponse(json_msg, mimetype="application/json", status=200)



@require_GET
@http_basic_auth_for_api
def jointargets(request):
    """"
    Return the JoinTarget objects in JSON format

    Filters may be applied for:
        - title
        - type
        - start_year
        - end_year

    These filters are validated through the JoinTargetForm

    Available to any WorldMap user
    """
    f = JoinTargetForm(request.GET)
    if not f.is_valid():

        err_msg = f.get_error_messages_as_html_string()
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)

        #fail_dict = dict(success=False, msg=f.get_error_messages_as_html_string())
        return HttpResponse(json_msg,
                            mimetype='application/json',
                            status=400)

    jts = JoinTarget.objects.filter(**f.get_join_target_filter_kwargs())
    json_data = [ob.as_json() for ob in jts]
    json_msg = MessageHelperJSON.get_json_success_msg(msg='', data_dict=json_data)

    return HttpResponse(json_msg,
                            mimetype='application/json',
                            status=200)


@http_basic_auth_for_api
@csrf_exempt
def tablejoin_api(request):
    """
    Join a DataTable to the Geometry of an existing layer
    """
    logger.info('tablejoin_api')
    if not request.method == 'POST':
        err_msg = "Unsupported Method"
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        logger.error(err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=405)

    # ---------------------------------
    # Attempt the table join
    # ---------------------------------
    (success, tablejoin_obj_or_err_msg) = attempt_tablejoin_from_request_params(request, request.user)

    # ---------------------------------
    # Failed, return an error message
    # ---------------------------------
    if not success:
        json_msg = MessageHelperJSON.get_json_fail_msg(tablejoin_obj_or_err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # ----------------------------------
    # Success, return TableJoin params
    # ----------------------------------
    join_result_info_dict = TableJoinResultForm.get_cleaned_data_from_table_join(tablejoin_obj_or_err_msg)
    return HttpResponse(json.dumps(join_result_info_dict), mimetype="application/json", status=200)



@http_basic_auth_for_api
@csrf_exempt
def tablejoin_detail(request, tj_id):
    """
    Return details of a TableJoin object
    """
    # -------------------------------------------------------
    # Retrieve TableJoin
    # -------------------------------------------------------
    try:
        tj = TableJoin.objects.get(pk=tj_id)
    except TableJoin.DoesNotExist:
        err_msg = 'No TableJoin object found'
        logger.error(err_msg + 'for id: %s' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=404)

    # -------------------------------------------------------
    # Check if the DataTable owner is making the request.
    # Note: This a simplified check for geonode 1.2
    # -------------------------------------------------------
    #if not request.user.has_perm('maps.view_layer', obj=tj.join_layer):
    if request.user != tj.datatable.owner:
        err_msg = "You are not permitted to view this TableJoin object"
        logger.error(err_msg + ' (id: %s)' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    results = [ob.as_json() for ob in [tj]][0]
    data = json.dumps(results)
    return HttpResponse(data)


@http_basic_auth_for_api
@csrf_exempt
def tablejoin_remove(request, tj_id):
    """
    Via the API, delete a TableJoin object
    """

    # -----------------------------------------------
    # Retrieve the TableJoin object
    # -----------------------------------------------
    try:
        tj = TableJoin.objects.get(pk=tj_id)
    except TableJoin.DoesNotExist:
        err_msg = 'No TableJoin object found'
        logger.error(err_msg + 'for id: %s' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)

        return HttpResponse(json_msg, mimetype='application/json', status=404)

    # -------------------------------------------------------
    # Check if the Layer owner is making the request.
    # Note: This a simplified check for geonode 1.2
    # -------------------------------------------------------
    #if not request.user.has_perm('maps.delete_layer', obj=tj.join_layer):
    if request.user != tj.datatable.owner:
        err_msg = "You are not permitted to delete this TableJoin object"
        logger.error(err_msg + ' (id: %s)' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)


    # -----------------------------------------------
    # Delete the view...the TableJoin "Layer"
    # -----------------------------------------------
    """
    # Not needed!
    view_dropped, err_msg = drop_view_from_table_join(tj)
    if not view_dropped:
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=400)
    """
    # -----------------------------------------------
    # Delete The DataTable, JoinLayer, and TableJoin objects!
    # -----------------------------------------------
    try:
        tj.datatable.delete()
        tj.join_layer.delete()
        tj.delete()
        return HttpResponse(json.dumps({'success':True, 'msg': ('%s removed' % (tj.view_name))}),
            mimetype='application/json', status=200)
    except:
        return HttpResponse(json.dumps({'success':False, 'msg': ('Error removing Join %s' % (sys.exc_info()[0]))}),
            mimetype='application/json', status=400)


@http_basic_auth_for_api
@csrf_exempt
def datatable_remove(request, dt_id):
    """
    Check if the user has 'delete_datatable' permissions
    """

    # -----------------------------------------------
    # Retrieve the DataTable object
    # -----------------------------------------------
    try:
        datatable = DataTable.objects.get(pk=dt_id)
    except DataTable.DoesNotExist:
        err_msg = 'No DataTable object found'
        logger.error(err_msg + ' for id: %s' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=404)

    # -----------------------------------------------
    # Check if the Layer owner is making the request.
    # Note: This a simplified check for geonode 1.2
    # -----------------------------------------------
    #if not request.user.has_perm('datatables.delete_datatable', obj=datatable):
    if request.user != datatable.owner:
        err_msg = "You are not permitted to delete this DataTable object"
        logger.error(err_msg + ' (id: %s)' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    # -----------------------------------------------
    # Delete it!
    # -----------------------------------------------
    dt_name = str(datatable)
    try:
        datatable.delete()
        success_msg = 'DataTable "%s" successfully deleted.' % (dt_name)
        logger.info(success_msg)
        json_msg = MessageHelperJSON.get_json_success_msg(success_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=200)
    except:
        err_msg = 'Failed to delete DataTable "%s" (id: %s)\nError: %s' % (dt_name, datatable.id, sys.exc_info()[0])
        logger.info(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=400)



@http_basic_auth_for_api
@csrf_exempt
def datatable_upload_and_join_api(request, is_dataverse_db=True):
    """
    Upload a Datatable and join it to an existing Layer
    """
    logger.info('datatable_upload_and_join_api')

    request_post_copy = request.POST.copy()
    join_props = request_post_copy

    f = TableUploadAndJoinRequestForm(join_props, request.FILES)
    if not f.is_valid():
        err_msg = "Form errors found. %s" % format_errors_as_text(f)#.as_json()#.as_text()
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # ----------------------------------------------------
    # Does the DataTable join column need to be char?
    #  - Check if the existing target join column is char?
    # ----------------------------------------------------
    (check_worked, force_char_convert) = ColumnHelper.is_char_column_conversion_recommended(\
                f.cleaned_data['layer_name'],\
                f.cleaned_data['layer_attribute'])
    if not check_worked:
        err_msg = 'Could not check the target column type'
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    if force_char_convert:  # It is, make sure the Datatable col will be char
        force_char_column = join_props['table_attribute']
    else:                   # Nope, let the datatable col stand, good or bad
        force_char_column = None

    # ----------------------------------------------------
    # Create a DataTable object from the file
    # ----------------------------------------------------
    (success, data_table_or_error) = attempt_datatable_upload_from_request_params(\
                                request,\
                                request.user,\
                                is_dataverse_db=is_dataverse_db,\
                                force_char_column=force_char_column)
    if not success:
        json_msg = MessageHelperJSON.get_json_fail_msg(data_table_or_error)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # ----------------------------------------------------
    # Attempt to join the new Datatable to a layer
    # ----------------------------------------------------

    # The table has been loaded, update the join properties
    # to include the new table name
    #
    join_props['table_name'] = data_table_or_error.table_name
    original_table_attribute = join_props['table_attribute']
    sanitized_table_attribute = standardize_column_name(original_table_attribute)
    join_props['table_attribute'] = sanitized_table_attribute

    (success, tablejoin_obj_or_err_msg) = attempt_tablejoin_from_request_params(join_props, request.user)
    # ---------------------------------
    # Failed, return an error message
    # ---------------------------------
    if not success:
        msg('Failed join!: %s' % tablejoin_obj_or_err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(tablejoin_obj_or_err_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    msg('Good join!')

    # ----------------------------------
    # Success, return TableJoin params
    # ----------------------------------
    join_result_info_dict = TableJoinResultForm.get_cleaned_data_from_table_join(tablejoin_obj_or_err_msg)
    return HttpResponse(json.dumps(join_result_info_dict), mimetype="application/json", status=200)


@http_basic_auth_for_api
@csrf_exempt
def datatable_upload_lat_lon_api(request):
    """
    Join a DataTable to the Geometry of an existing layer (API)
    """

    # Is it a POST?
    #
    #
    if not request.method == 'POST':
        json_msg = MessageHelperJSON.get_json_fail_msg("Unsupported Method")
        return HttpResponse(json_msg, mimetype="application/json", status=500)

    # Is the request data valid?
    # Check with the MapLatLngLayerRequestForm
    #
    #f = MapLatLngLayerRequestForm(request.POST, request.FILES)
    f = DataTableUploadFormLatLng(request.POST, request.FILES)
    if not f.is_valid():
        err_msg = "Invalid data in request: %s" % format_errors_as_text(f)
        logger.error("datatable_upload_lat_lon_api. %s" % err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    #   Set the new table/layer owner
    #
    new_table_owner = request.user

    # --------------------------------------
    # (1) Datatable Upload
    # --------------------------------------
    try:
        resp = datatable_upload_api(request, is_dataverse_db=False)
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
    # (2) Create layer using the Lat/Lng columns
    # --------------------------------------
    msg('datatable_upload_lat_lon_api 2')
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

            # Get the Layer metadata
            #layer_metadata_obj = LayerMetadata(latlng_record_or_err_msg.layer)
            #response_params = layer_metadata_obj.get_metadata_dict()

            # Addd lat/lng attributes
            layer_params = latlng_record_or_err_msg.as_json()
            msgt('layer_params: %s' % layer_params)

            json_msg = MessageHelperJSON.get_json_success_msg(msg='New layer created', data_dict=layer_params)
            return HttpResponse(json_msg, mimetype="application/json", status=200)
    except:
        traceback.print_exc(sys.exc_info())
        err_msg = 'Uncaught error ingesting Data Table'
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        logger.error(err_msg)

        return HttpResponse(json_msg, mimetype="application/json", status=400)

@http_basic_auth_for_api
@csrf_exempt
def datatable_lat_lon_remove(request, dt_id):
    """
    Check if the user has 'delete_datatable' permissions
    """

    # -----------------------------------------------
    # Retrieve the DataTable object
    # -----------------------------------------------
    try:
        lat_lng_datatable = LatLngTableMappingRecord.objects.get(pk=dt_id)
    except LatLngTableMappingRecord.DoesNotExist:
        err_msg = 'No LatLngTableMappingRecord object found'
        logger.error(err_msg + ' for id: %s' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=404)

    # -----------------------------------------------
    # Does the user have permissions to Delete it?
    # Note: This a simplified check for geonode 1.2
    # -------------------------------------------------------
    #if not request.user.has_perm('datatables.delete_latlngtablemappingrecord', obj=lat_lng_datatable):
    if request.user != lat_lng_datatable.datatable.owner:
        err_msg = "You are not permitted to delete this Latitude/Longitude layer and datatable"
        logger.error(err_msg + ' (id: %s)' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    # -----------------------------------------------
    # Delete it!
    # -----------------------------------------------
    if lat_lng_datatable.layer:
        lat_lng_datatable.layer.delete()
    if lat_lng_datatable.datatable:
        lat_lng_datatable.datatable.delete()

    dt_name = str(lat_lng_datatable)
    try:
        lat_lng_datatable.delete()
        success_msg = 'LatLngTableMappingRecord "%s" successfully deleted.' % (dt_name)
        logger.info(success_msg)
        json_msg = MessageHelperJSON.get_json_success_msg(success_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=200)
    except:
        err_msg = 'Failed to delete LatLngTableMappingRecord "%s" (id: %s)\nError: %s' % (dt_name, lat_lng_datatable.id, sys.exc_info()[0])
        logger.info(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=400)
