from __future__ import print_function
import logging
import sys
import os
import json
import traceback
from django.core import serializers
from django.core.serializers.json import Serializer
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from geonode.dataverse_connect.dv_utils import MessageHelperJSON          # format json response object

from shared_dataverse_information.worldmap_datatables.forms import\
                                     TableJoinRequestForm\
                                    , TableJoinResultForm\
                                    , TableUploadAndJoinRequestForm\
                                    , MapLatLngLayerRequestForm

from geonode.contrib.msg_util import *

from .models import DataTable, JoinTarget, TableJoin
from .forms import UploadDataTableForm
from .utils import process_csv_file, setup_join, create_point_col_from_lat_lon, standardize_name

logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
def datatable_upload_api(request):
    if request.method != 'POST':
        return HttpResponse("Invalid Request", mimetype="text/plain", status=500)

    # ---------------------------------------
    # Verify Request
    # ---------------------------------------
    form = UploadDataTableForm(request.POST, request.FILES)
    if not form.is_valid():
        err_msg = "Form errors found." % form.errors#.as_json()#.as_text()
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg, data_dict=form.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=400)


    data = form.cleaned_data
    table_name = standardize_name(os.path.splitext(os.path.basename(request.FILES['uploaded_file'].name))[0], is_table_name=True)
    #table_name = standardize_name(os.path.splitext(os.path.basename(csv_filename))[0], is_table_name=True)
    instance = DataTable(uploaded_file=request.FILES['uploaded_file'], table_name=table_name, title=table_name)
    delimiter = data['delimiter_type'] 
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

    # -----------------------------------------
    # Retrieve object of raise Http404
    # -----------------------------------------
    dt = get_object_or_404(DataTable, pk=dt_id)

    # -----------------------------------------
    # Serialize DataTable as JSON
    # -----------------------------------------
    fields_to_return = ('uploaded_file', 'table_name','title')

    serialized = serializers.serialize("json", (dt,), fields=fields_to_return)
    #msg('serialized: %s' % serialized)

    object = json.loads(serialized)[0]
    #msg('object: %s' % object)

    # -----------------------------------------
    # Serialize DataTable attributes as JSON
    # -----------------------------------------
    attributes = json.loads(serializers.serialize("json", dt.attributes.all()))
    attribute_list = []
    for attribute in attributes:
        attribute_list.append({'attribute':attribute['fields']['attribute'], 'type':attribute['fields']['attribute_type']})

    object["attributes"] = attribute_list
    data = json.dumps(object) 

    return HttpResponse(data, mimetype="application/json", status=200)



@login_required
def jointargets(request):
    if len(request.GET.keys()) > 0:
        kwargs = {}
        if request.GET.get('title'):
            kwargs['layer__title__icontains'] = request.GET.get('title')
        if request.GET.get('type'):
            kwargs['geocode_type__name__icontains'] = request.GET.get('type')
        if request.GET.get('start_year'):
            if request.GET.get('start_year').isdigit():
                kwargs['year__gte'] = request.GET.get('start_year')
            else:
                return HttpResponse(json.dumps({'success': False, 'msg':'Invalid Start Year'}), mimetype="application/json")
        if request.GET.get('end_year'):
            if request.GET.get('end_year').isdigit():
                kwargs['year__lte'] = request.GET.get('end_year')
            else:
                return HttpResponse(json.dumps({'success': False, 'msg':'Invalid End Year'}), mimetype="application/json")
        jts = JoinTarget.objects.filter(**kwargs) 
        results = [ob.as_json() for ob in jts] 
        return HttpResponse(json.dumps(results), mimetype="application/json")
    else:
        jts = JoinTarget.objects.all()
        results = [ob.as_json() for ob in jts] 
        return HttpResponse(json.dumps(results), mimetype="application/json")



@login_required
@csrf_exempt
def tablejoin_api(request):
    """
    Join a DataTable to the Geometry of an existing layer
    """
    logger.info(tablejoin_api)
    if not request.method == 'POST':
        return_dict = dict(success=False\
                            , msg="Unsupported Method"\
                        )
        return HttpResponse(json.dumps(return_dict), mimetype="application/json", status=500)

    # ----------------------------------
    # Validate the request
    # ----------------------------------
    f = TableJoinRequestForm(request.POST)
    if not f.is_valid():
        err_msg = "Invalid Data for TableJoinRequestForm.  Errors: %s" % f.errors
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
        new_layer_owner = new_layer_owner
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

    results = [ob.as_json() for ob in [tj]][0]
    data = json.dumps(results)
    return HttpResponse(data)

@login_required
@csrf_exempt
def tablejoin_remove(request, tj_id):
    # TODO: Check Permissions!!

    # get TableJoin
    try:
        tj = TableJoin.objects.get(pk=tj_id)
    except TableJoin.DoesNotExist:
        err_msg = 'No TableJoin object found'
        logger.error(err_msg + 'for id: %s' % tj_id)
        json_msg = MessageHelperJSON.get_json_fail_msg(err_msg)

        return HttpResponse(json_msg, mimetype='application/json', status=404)

    try:
        tj.datatable.delete()
        tj.join_layer.delete()
        tj.delete()
        return HttpResponse(json.dumps({'success':True, 'msg': ('%s removed' % (tj.view_name))}), mimetype='application/json', status=200)
    except:
        return HttpResponse(json.dumps({'success':False, 'msg': ('Error removing Join %s' % (sys.exc_info()[0]))}), mimetype='application/json', status=400)


@login_required
@csrf_exempt
def datatable_remove(request, dt_id):
    # TODO: Check Permissions!!
    try:
        dt = get_object_or_404(DataTable, pk=dt_id)
        dt.delete()
        return HttpResponse(json.dumps({'success':True, 'msg': ('%s removed' % (dt.table_name))}), mimetype='application/json', status=200)
    except:
        return HttpResponse(json.dumps({'success':False, 'msg': ('Error removing DataTable %s' % (sys.exc_info()[0]))}), mimetype='application/json', status=400)



@login_required
@csrf_exempt
def datatable_upload_and_join_api(request):
    """
    Upload a Datatable and join it to an existing Layer
    """
    logger.info('datatable_upload_and_join_api')

    request_post_copy = request.POST.copy()
    join_props = request_post_copy

    f = TableUploadAndJoinRequestForm(join_props)
    if not f.is_valid():
        err_msg = "Invalid Data for Join: %s" % f.errors
        logger.error(err_msg)
        return_dict = dict(success=False\
                         , msg=err_msg\
                    )
        return HttpResponse(json.dumps(return_dict), mimetype="application/json", status=400)


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
        json_msg = MessageHelperJSON.get_json_fail_msg("Unsupported Method", data_dict=form.errors)
        return HttpResponse(json_msg, mimetype="application/json", status=500)

    # Is the request data valid?
    # Check with the MapLatLngLayerRequestForm
    #
    form_map_lat_lng = MapLatLngLayerRequestForm(request.POST.dict())
    if not form_map_lat_lng.is_valid():
        json_msg = MessageHelperJSON.get_json_fail_msg("Invalid data in request", data_dict=form_map_lat_lng.errors)
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
        if upload_return_dict['success'] != True:
            return HttpResponse(json.dumps(upload_return_dict), mimetype='application/json', status=400)
    except:
        logger.error('Failed Datatable Upload for map lat/lng table: %s' % latlng_record_or_err_msg)

        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), mimetype='application/json', status=400)


    # --------------------------------------
    # (2) Create layer using the Lat/Lng columns
    # --------------------------------------
    msg('datatable_upload_lat_lon_api 2')
    try:
        success, latlng_record_or_err_msg = create_point_col_from_lat_lon(new_table_owner\
                        , upload_return_dict['data']['datatable_name']\
                        , form_map_lat_lng.cleaned_data['lat_attribute']\
                        , form_map_lat_lng.cleaned_data['lng_attribute']\
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
