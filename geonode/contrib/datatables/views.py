import sys
import os
import json
import traceback
from django.core import serializers
from django.core.serializers.json import Serializer
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from .models import DataTable, JoinTarget, TableJoin
from .forms import UploadDataTableForm
from .utils import process_csv_file, setup_join, create_point_col_from_lat_lon

@login_required
@csrf_exempt
def datatable_upload_api(request):

    if request.method != 'POST':
        return HttpResponse("Invalid Request", content_type="text/plain", status=500)
    else:
        form = UploadDataTableForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            table_name = slugify(unicode(os.path.splitext(os.path.basename(request.FILES['uploaded_file'].name))[0])).replace('-','_')
            instance = DataTable(uploaded_file=request.FILES['uploaded_file'], table_name=table_name, title=table_name)
            delimiter = data['delimiter_type']
            no_header_row = data['no_header_row']
            instance.save()
            dt, msg = process_csv_file(instance, delimiter=delimiter, no_header_row=no_header_row)

            if dt:
                return_dict = {
                    'datatable_id': dt.pk,
                    'datatable_name': dt.table_name,
                    'success': True,
                    'msg': ""
                }
                return HttpResponse(json.dumps(return_dict), content_type="application/json", status=200)
            else:
                return_dict = {
                    'datatable_id': None,
                    'datatable_name': None,
                    'success': False,
                    'msg': msg
                }
                return HttpResponse(json.dumps(return_dict), content_type="application/json", status=400)
        else:
            return_dict = {
                'datatable_id': None,
                'datatable_name': None,
                'success': False,
                'msg': "Form Errors: " + form.errors.as_text()
            }
            return HttpResponse(json.dumps(return_dict), content_type="application/json", status=400)

@login_required
@csrf_exempt
def datatable_detail(request, dt_id):
    dt = get_object_or_404(DataTable, pk=dt_id)
    object = json.loads(serializers.serialize("json", (dt,), fields=('uploaded_file', 'table_name')))[0]
    attributes = json.loads(serializers.serialize("json", dt.attributes.all()))
    attribute_list = []
    for attribute in attributes:
        attribute_list.append({'attribute':attribute['fields']['attribute'], 'type':attribute['fields']['attribute_type']})
    object["attributes"] = attribute_list
    data = json.dumps(object)
    return HttpResponse(data)

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
                return HttpResponse(json.dumps({'success': False, 'msg':'Invalid Start Year'}), content_type="application/json")
        if request.GET.get('end_year'):
            if request.GET.get('end_year').isdigit():
                kwargs['year__lte'] = request.GET.get('end_year')
            else:
                return HttpResponse(json.dumps({'success': False, 'msg':'Invalid End Year'}), content_type="application/json")
        jts = JoinTarget.objects.filter(**kwargs)
        results = [ob.as_json() for ob in jts]
        return HttpResponse(json.dumps(results), content_type="application/json")
    else:
        jts = JoinTarget.objects.all()
        results = [ob.as_json() for ob in jts]
        return HttpResponse(json.dumps(results), content_type="application/json")

@login_required
@csrf_exempt
def tablejoin_api(request):
    if request.method == 'GET':
         return HttpResponse("Unsupported Method", content_type="application/json", status=500)
    elif request.method == 'POST':
        table_name = request.POST.get("table_name", None)
        layer_typename = request.POST.get("layer_typename", None)
        table_attribute = request.POST.get("table_attribute", None)
        layer_attribute = request.POST.get("layer_attribute", None)
        if table_name and layer_typename and table_attribute and layer_attribute:
            try:
                tj, msg = setup_join(table_name, layer_typename, table_attribute, layer_attribute)
                if tj:
                    return_dict = {
                        'join_id': tj.pk,
                        'view_name': tj.view_name,
                        'matched_records': tj.matched_records_count,
                        'unmatched_records': tj.unmatched_records_count,
                        'unmatched_records_list': tj.unmatched_records_list,
                        'datatable': tj.datatable.table_name,
                        'source_layer': tj.source_layer.typename,
                        'table_attribute': tj.table_attribute.attribute,
                        'layer_attribute': tj.layer_attribute.attribute,
                        'join_layer': tj.join_layer.typename,
                        'layer_url': tj.join_layer.get_absolute_url()
                    }
                    return HttpResponse(json.dumps(return_dict), content_type="application/json", status=200)
                else:
                    return_dict = {
                        'success': False,
                        'msg': "Error Creating Join: %s" % msg
                    }
                    return HttpResponse(json.dumps(return_dict), content_type="application/json", status=400)
            except:
                return_dict = {
                    'success': False,
                    'msg': "Error Creating Join: %s" % msg
                }
                return HttpResponse(json.dumps(return_dict), content_type="application/json", status=400)
        else:
            return HttpResponse(json.dumps({'msg':'Invalid Request', 'success':False}), content_type='application/json', status=400)

@login_required
@csrf_exempt
def tablejoin_detail(request, tj_id):
    tj = get_object_or_404(TableJoin, pk=tj_id)
    results = [ob.as_json() for ob in [tj]][0]
    data = json.dumps(results)
    return HttpResponse(data)

@login_required
@csrf_exempt
def tablejoin_remove(request, tj_id):
    # TODO: Check Permissions!!
    try:
        tj = get_object_or_404(TableJoin, pk=tj_id)
        tj.datatable.delete()
        tj.join_layer.delete()
        tj.delete()
        return HttpResponse(json.dumps({'success':True, 'msg': ('%s removed' % (tj.view_name))}), content_type='application/json', status=200)
    except:
        return HttpResponse(json.dumps({'success':False, 'msg': ('Error removing Join %s' % (sys.exc_info()[0]))}), content_type='application/json', status=400)

# @login_required
@csrf_exempt
def datatable_remove(request, dt_id):
    # TODO: Check Permissions!!
    try:
        dt = get_object_or_404(DataTable, pk=dt_id)
        dt.delete()
        return HttpResponse(json.dumps({'success':True, 'msg': ('%s removed' % (dt.table_name))}), content_type='application/json', status=200)
    except:
        return HttpResponse(json.dumps({'success':False, 'msg': ('Error removing DataTable %s' % (sys.exc_info()[0]))}), content_type='application/json', status=400)

@login_required
@csrf_exempt
def datatable_upload_and_join_api(request):
    request_post_copy = request.POST.copy()
    join_props = request_post_copy
    try:
        resp = datatable_upload_api(request)
        upload_return_dict = json.loads(resp.content)
        if upload_return_dict['success'] != True:
            return HttpResponse(json.dumps(upload_return_dict), content_type='application/json', status=400)
        join_props['table_name'] = upload_return_dict['datatable_name']
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), content_type='application/json', status=400)
    try:
        original_table_attribute = join_props['table_attribute']
        sanitized_table_attribute = slugify(unicode(original_table_attribute)).replace('-','_')
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
    try:
        resp = datatable_upload_api(request)
        upload_return_dict = json.loads(resp.content)
        if upload_return_dict['success'] != True:
            return HttpResponse(json.dumps(upload_return_dict), content_type='application/json', status=400)
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), content_type='application/json', status=400)

    try:
        layer, msg = create_point_col_from_lat_lon(upload_return_dict['datatable_name'], request.POST.get('lat_column'), request.POST.get('lon_column'))
        return HttpResponse(json.dumps(upload_return_dict), content_type='application/json', status=200)
    except:
        traceback.print_exc(sys.exc_info())
        return HttpResponse(json.dumps({'msg':'Uncaught error ingesting Data Table', 'success':False}), content_type='application/json', status=400)
