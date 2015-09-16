from __future__ import print_function
import logging
import sys
from os.path import basename, splitext
import json
import traceback
from django.conf import settings
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object
from shared_dataverse_information.shared_form_util.format_form_errors import format_errors_as_text

from geonode.contrib.datatables.forms import JoinTargetForm
from shared_dataverse_information.worldmap_datatables.forms import\
    DataTableUploadForm,\
    TableJoinRequestForm,\
    TableJoinResultForm,\
    TableUploadAndJoinRequestForm,\
    MapLatLngLayerRequestForm

from geonode.contrib.msg_util import msg, msgt, msgn, msgx

from .models import DataTable, JoinTarget, TableJoin
from .utils import process_csv_file, setup_join, create_point_col_from_lat_lon, standardize_name, get_unique_tablename
from .db_helper import CHOSEN_DB_SETTING
logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
def datatable_upload_api(request):
    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=500)

    # ---------------------------------------
    # Verify Request
    # ---------------------------------------
    form = DataTableUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        err_msg = "Form errors found. %s" % format_errors_as_text(form)#.as_json()#.as_text()
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=form.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)


    data = form.cleaned_data

    table_name = get_unique_tablename(splitext(basename(request.FILES['uploaded_file'].name))[0])


    instance = DataTable(uploaded_file=request.FILES['uploaded_file'],
                         table_name=table_name,
                         tablespace=CHOSEN_DB_SETTING,
                         title=data['title'],
                         abstract=data['abstract'],
                         delimiter=data['delimiter'],
                         owner=request.user)
    delimiter = data['delimiter']
    no_header_row = data['no_header_row']

    # save DataTable object
    instance.save()

    dt, result_msg = process_csv_file(instance, delimiter=delimiter, no_header_row=no_header_row)

    # -----------------------------------------
    #  Success, DataTable created
    # -----------------------------------------
    if dt:
        return_dict = dict(datatable_id=dt.pk, datatable_name=dt.table_name)
        json_msg = MessageHelperJSON.get_json_success_msg(msg='', data_dict=return_dict)
        return HttpResponse(json_msg, mimetype="application/json", status=200)

    else:
        # -----------------------------------------
        #  Failed, DataTable not created
        # -----------------------------------------
        json_msg = MessageHelperJSON.get_json_fail_msg(result_msg)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

       

@login_required
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

    if not request.user.has_perm('datatables.view_datatable', obj=datatable):
        err_msg = "You are not permitted to view this TableJoin object"
        logger.error(err_msg + ' (id: %s)' % dt_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    json_msg = MessageHelperJSON.get_json_success_msg(msg=None, data_dict=datatable.as_json())
    return HttpResponse(json_msg, mimetype="application/json", status=200)


"""
from contrib.datatables.forms import JoinTargetForm
d = {}
f = JoinTargetForm(d)
f.is_valid()
"""
@require_GET
@login_required
def jointargets(request):
    """"
    Return the JoinTarget objects in JSON formats

    Filters may be applied for:
        - title
        - type
        - start_year
        - end_year
    These filters are validated through the JoinTargetForm
    """"
    f = JoinTargetForm(request.GET)
    if not f.is_valid():
        fail_dict = dict(success=False, msg=f.get_error_messages_as_html_string())
        return HttpResponse(json.dumps(fail_dict), mimetype='application/json')

    jts = JoinTarget.objects.filter(**f.get_join_target_filter_kwargs())
    results = [ob.as_json() for ob in jts]
    return HttpResponse(json.dumps(results), mimetype="application/json")



@login_required
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
        return HttpResponse(json_msg, mimetype="application/json", status=500)

    # ----------------------------------
    # Validate the request
    # ----------------------------------
    f = TableJoinRequestForm(request.POST, request.FILES)
    if not f.is_valid():
        err_msg = "Form errors found. %s" % format_errors_as_text(f)#.as_json()#.as_text()
        logger.error(err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    # DataTable and join attribute
    table_name = f.cleaned_data['table_name']
    table_attribute = f.cleaned_data['table_attribute']

    # Layer and join attribute
    layer_typename = f.cleaned_data['layer_typename']
    layer_attribute = f.cleaned_data['layer_attribute']

    # Set the owner
    if isinstance(f.cleaned_data.get('new_layer_owner', None), User):
        new_layer_owner = f.cleaned_data['new_layer_owner']
    else:
        new_layer_owner = request.user


    try:
        tj, result_msg = setup_join(new_layer_owner, table_name, layer_typename, table_attribute, layer_attribute)
        if tj:
            # Successful Join
            #
            join_result_info_dict = TableJoinResultForm.get_cleaned_data_from_table_join(tj)
            return HttpResponse(json.dumps(join_result_info_dict), mimetype="application/json", status=200)

        else:
            # Error!
            #
            err_msg = "Error Creating Join: %s" % result_msg
            json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
            return HttpResponse(json_msg, mimetype="application/json", status=400)
    except:

        traceback.print_exc(sys.exc_info())
        err_msg = "Error Creating Join: %s" % str(sys.exc_info()[0])
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)

        return HttpResponse(json_msg, mimetype="application/json", status=400)



@login_required
@csrf_exempt
def tablejoin_detail(request, tj_id):

    # get TableJoin
    try:
        tj = TableJoin.objects.get(pk=tj_id)
    except TableJoin.DoesNotExist:
        err_msg = 'No TableJoin object found'
        logger.error(err_msg + 'for id: %s' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=404)

    if not request.user.has_perm('maps.view_layer', obj=tj.join_layer):
        err_msg = "You are not permitted to view this TableJoin object"
        logger.error(err_msg + ' (id: %s)' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    results = [ob.as_json() for ob in [tj]][0]
    data = json.dumps(results)
    return HttpResponse(data)


@login_required
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

    # -----------------------------------------------
    # Does the user have permissions to Delete it?
    # -----------------------------------------------
    if not request.user.has_perm('maps.delete_layer', obj=tj.join_layer):
        err_msg = "You are not permitted to delete this TableJoin object"
        logger.error(err_msg + ' (id: %s)' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        return HttpResponse(json_msg, mimetype='application/json', status=401)

    # -----------------------------------------------
    # Delete it!
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


@login_required
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
    # Does the user have permissions to Delete it?
    # -----------------------------------------------
    if not request.user.has_perm('datatables.delete_datatable', obj=datatable):
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



@login_required
@csrf_exempt
def datatable_upload_and_join_api(request):
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
    # Create a DataTable object from the file
    # ----------------------------------------------------
    try:
        resp = datatable_upload_api(request)
        upload_return_dict = json.loads(resp.content)
        if not upload_return_dict.get('success', None) is True:
            # ERROR
            return HttpResponse(json.dumps(upload_return_dict), mimetype='application/json', status=400)

        print('upload_return_dict', upload_return_dict)
        join_props['table_name'] = upload_return_dict['data']['datatable_name']
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), mimetype='application/json', status=400)


    # ----------------------------------------------------
    # Attempt to join the new Datatable to a layer
    # ----------------------------------------------------
    try:
        original_table_attribute = join_props['table_attribute']
        sanitized_table_attribute = standardize_name(original_table_attribute)
        join_props['table_attribute'] = sanitized_table_attribute
        request.POST = join_props
        resp = tablejoin_api(request)
        return resp 
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse("Not yet")


@login_required
@csrf_exempt
def datatable_upload_lat_lon_api(request):
    """
    Join a DataTable to the Geometry of an existing layer
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
    f = MapLatLngLayerRequestForm(request.POST, request.FILES)
    if not f.is_valid():
        err_msg = "Invalid data in request: %s" % format_errors_as_text(f)
        logger.error("datatable_upload_lat_lon_api. %s" % err_msg)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=f.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)

    #   Set the new table/layer owner
    #
    new_table_owner = request.user
    msg('datatable_upload_lat_lon_api 1')

    # --------------------------------------
    # (1) Datatable Upload
    # --------------------------------------
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
    # (2) Create layer using the Lat/Lng columns
    # --------------------------------------
    msg('datatable_upload_lat_lon_api 2')
    try:
        success, latlng_record_or_err_msg = create_point_col_from_lat_lon(new_table_owner
                        , upload_return_dict['data']['datatable_name']
                        , form_map_lat_lng.cleaned_data['lat_attribute']
                        , form_map_lat_lng.cleaned_data['lng_attribute']
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
            json_msg = MessageHelperJSON.get_json_success_msg(msg='New layer created', data_dict=json_data)
            return HttpResponse(json_msg, mimetype="application/json", status=200)
    except:
        traceback.print_exc(sys.exc_info())
        err_msg = 'Uncaught error ingesting Data Table'
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)
        logger.error(err_msg)

        return HttpResponse(json_msg, mimetype="application/json", status=400)
