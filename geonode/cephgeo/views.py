from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import smart_str
from django.utils import simplejson as json
from django.contrib import messages
from django.core import serializers
from django.template import RequestContext

from pprint import pprint

from geonode.cephgeo.forms import DataInputForm, DataDeleteForm
from geonode.cephgeo.models import CephDataObject, FTPRequest, FTPStatus, FTPRequestToObjectIndex, UserTiles
from geonode.cephgeo.utils import get_data_class_from_filename
from geonode.tasks.ftp import process_ftp_request
from geonode.tasks.ceph_update import ceph_metadata_remove, ceph_metadata_update

from geonode.cephgeo.cart_utils import *

import client
import utils
import cPickle
import unicodedata
import time
import operator
import json
from geonode.cephgeo.utils import get_cart_datasize
from datetime import datetime
from django.core.urlresolvers import reverse
from geonode.maptiles.models import SRS
from django.utils.text import slugify

from geonode.tasks.update import update_fhm_metadata_task, style_update, seed_layers
from geonode.tasks.update import pl2_metadata_update, sar_metadata_update
from geonode.tasks.update import layer_default_style, floodplain_keywords
from geonode.tasks.update import update_lidar_coverage_task
from geonode.base.enumerations import CHARSETS

from django.conf import settings
from geonode.layers.models import Layer

# Create your views here.


@login_required
def tile_check(request):
    user = request.user
    response = "false"
    if not request.POST:
        raise PermissionDenied

    try:
        json_tiles = UserTiles.objects.get(user=user)
    except ObjectDoesNotExist as e:
        return HttpResponse(status=404)

    georefs = map(str, request.POST.get('georefs', ''))
    reference_tiles = map(str, json.loads(json_tiles))
    valid_tiles = []
    for x in georefs:
        if x in georefs:
            valid_tiles.append(x)

    return HttpResponse(json.dumps(valid_tiles), status=200)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def file_list_ceph(request, sort=None):
    if sort not in utils.SORT_TYPES and sort != None:
        return HttpResponse(status=404)

    cephclient = client.CephStorageClient(settings.CEPH_OGW['default']['USER'], settings.CEPH_OGW[
                                          'default']['KEY'], settings.CEPH_OGW['default']['LOCATION'])
    object_list = cephclient.list_files(
        container_name=settings.CEPH_OGW['default']['CONTAINER'])
    sorted_list = []

    for ceph_object in object_list:
        ceph_object["type"] = utils.get_data_class_from_filename(ceph_object[
                                                                 "name"])
        ceph_object["uploaddate"] = ceph_object["last_modified"]

    # sorting goes here
    if sort != None:
        sorted_list = utils.sort_by(sort, object_list)
        paginator = Paginator(sorted_list, 50)
    else:
        paginator = Paginator(object_list, 50)

    page = request.GET.get('page')

    try:
        paged_objects = paginator.page(page)
    except PageNotAnInteger:
        paged_objects = paginator.page(1)
    except EmptyPage:
        paged_objects = paginator.page(paginator.num_pages)

    return render(request, "file_list.html",
                  {"file_list": paged_objects,
                   "file_types": utils.TYPE_TO_IDENTIFIER_DICT,
                   "sort_types": utils.SORT_TYPES,
                   "sort": sort})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def file_list_geonode(request, sort=None, grid_ref=None):

    if sort not in utils.SORT_TYPES and sort != None:
        return HttpResponse(status=404)

    object_list = []
    sorted_list = []

    # No Grid Ref
    if grid_ref is None:
        object_list = CephDataObject.objects.all()

    else:
        # 1 Grid Ref or Grid Ref Range
        if utils.is_valid_grid_ref(grid_ref):
            # Query files with same grid reference
            #object_list = CephDataObject.objects.filter(name__startswith=grid_ref)
            object_list = CephDataObject.objects.filter(grid_ref=grid_ref)

        else:
            return HttpResponse(status=404)

    if sort == 'type':
        sorted_list = sorted(object_list.order_by(
            'name'), key=operator.attrgetter('data_class'))
    elif sort == 'uploaddate':
        sorted_list = sorted(object_list.order_by(
            'name'), key=operator.attrgetter('last_modified'), reverse=True)
        #~ sorted_list = object_list.order_by('-last_modified')
    elif sort == 'name':
        sorted_list = sorted(object_list, key=operator.attrgetter('name'))
    else:  # default
        sorted_list = object_list

    paginator = Paginator(sorted_list, 50)

    page = request.GET.get('page')

    try:
        paged_objects = paginator.page(page)
    except PageNotAnInteger:
        paged_objects = paginator.page(1)
    except EmptyPage:
        paged_objects = paginator.page(paginator.num_pages)

    return render(request, "file_list_geonode.html",
                  {"file_list": paged_objects,
                   "file_types": utils.TYPE_TO_IDENTIFIER_DICT,
                   "sort_types": utils.SORT_TYPES,
                   "sort": sort,
                   "grid_ref": grid_ref})


@login_required
def file_list_json(request, sort=None, grid_ref=None):

    if sort not in utils.SORT_TYPES and sort != None:
        return HttpResponse(status=404)

    object_list = []
    sorted_list = []

    # No Grid Ref
    if grid_ref is None:
        object_list = CephDataObject.objects.all()

    else:
        # 1 Grid Ref or Grid Ref Range
        if utils.is_valid_grid_ref(grid_ref):
            # Query files with same grid reference
            object_list = CephDataObject.objects.filter(
                name__startswith=grid_ref)
        else:
            return HttpResponse(status=404)

    if sort == 'type':
        sorted_list = sorted(object_list.order_by(
            'name'), key=operator.attrgetter('data_class'))
    elif sort == 'uploaddate':
        sorted_list = sorted(object_list.order_by(
            'name'), key=operator.attrgetter('last_modified'), reverse=True)
        #~ sorted_list = object_list.order_by('-last_modified')
    elif sort == 'name':
        sorted_list = sorted(object_list, key=operator.attrgetter('name'))
    else:  # default
        sorted_list = object_list

    response_data = {"file_list": serializers.serialize('json', sorted_list),
                     "file_types": utils.TYPE_TO_IDENTIFIER_DICT,
                     "sort_types": utils.SORT_TYPES,
                     "sort": sort,
                     "grid_ref": grid_ref, }

    return HttpResponse(json.dumps(response_data), content_type="application/json")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def data_input(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # pprint(request.POST)
        print 'REQUEST POST', request.POST
        form = DataInputForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # Commented out until a way is figured out how to assign database writes/saves
            #   to celery without throwing a 'database locked' error
            # ceph_metadata_update.delay(uploaded_objects)
            csv_delimiter = ','
            uploaded_objects_list = smart_str(
                form.cleaned_data['data']).splitlines()
            update_grid = form.cleaned_data['update_grid']

            ceph_metadata_update.delay(uploaded_objects_list, update_grid)

            ctx = {
                'charsets': CHARSETS,
                'is_layer': True,
            }

            return render_to_response("update_task.html", RequestContext(request, ctx))
        else:
            messages.error(request, "Invalid input on data form")
            return redirect('geonode.cephgeo.views.data_input')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = DataInputForm()
        return render(request, 'ceph_data_input.html', {'data_input_form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def data_remove(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # pprint(request.POST)
        form = DataDeleteForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # Commented out until a way is figured out how to assign database writes/saves
            #   to celery without throwing a 'database locked' error
            # ceph_metadata_update.delay(uploaded_objects)
            csv_delimiter = ','
            uploaded_objects_list = smart_str(
                form.cleaned_data['data']).splitlines()
            update_grid = form.cleaned_data['update_grid']
            delete_from_ceph = form.cleaned_data['delete_from_ceph']


            ceph_metadata_remove.delay(uploaded_objects_list, update_grid, delete_from_ceph)

            ctx = {
                'charsets': CHARSETS,
                'is_layer': True,
            }

            return render_to_response("update_task.html", RequestContext(request, ctx))
        else:
            messages.error(request, "Invalid input on data form")
            return redirect('geonode.cephgeo.views.data_remove')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = DataDeleteForm()
        return render(request, 'ceph_data_delete.html', {'data_delete_form': form})


@login_required
def error(request):
    return render(request, "ceph_error.html",
                  {"err_msg": request.error, })


@login_required
def get_cart(request):
    return render_to_response('cart.html',
                              dict(cart=CartProxy(request), cartsize=get_cart_datasize(
                                  request), projections=SRS.labels.values()),
                              context_instance=RequestContext(request))


@login_required
def get_cart_json(request):
    cart = CartProxy(request)
    #~ json_cart = dict()
    #~ for item in cart:
    #~ json_cart[str(item.object_id)] = serializers.serialize('json', CephDataObject.objects.get(id=int(item.pk)))
    #~ return HttpResponse(json.dumps(json_cart), content_type="application/json")

    # TODO: debug serialization for CephDataObjects

    obj_name_dict = [CephDataObject.objects.get(
        id=int(item.object_id)).name for item in cart]
    return HttpResponse(json.dumps(obj_name_dict), content_type="application/json")


@login_required
def get_obj_ids_json(request):
    cart = CartProxy(request)
    json_cart = dict()
    ceph_objs = CephDataObject.objects.all()
    ceph_objs_by_data_class = utils.ceph_object_ids_by_data_class(ceph_objs)
    # pprint(ceph_objs_by_data_class)
    return HttpResponse(json.dumps(ceph_objs_by_data_class), content_type="application/json")


@login_required
def create_ftp_folder(request, projection=None):
    # Check time difference between this request and the next most recent request
    # If within 5 minutes/300 secs, inform the user to wait
    try:
        latest_request = FTPRequest.objects.latest('date_time')
        time_diff = datetime.now() - latest_request.date_time
        if time_diff.total_seconds() < 300:
            return render_to_response('ftp_result.html',
                                      {   "result_msg" : "There was a problem with your request. A previous FTP request \
                                         was recorded within the last 5 minutes. Please wait at least 5 minutes in \
                                         between submitting FTP requests.", },
                                      context_instance=RequestContext(request))
    except ObjectDoesNotExist:
        pass
    cart = CartProxy(request)
    #[CephDataObject.objects.get(id=int(item.object_id)).name for item in cart]

    # Get specified projection
    srs_epsg = None
    if projection is not None:
        srs_epsg = SRS.EPSG_num[projection]

    print(">>>[SRS]: " + str(projection) + "  " + str(srs_epsg))

    obj_name_dict = dict()
    total_size_in_bytes = 0
    num_tiles = 0
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.object_id))
        total_size_in_bytes += obj.size_in_bytes
        num_tiles += 1
        if DataClassification.labels[obj.data_class] in obj_name_dict:
            obj_name_dict[DataClassification.labels[obj.data_class].encode(
                'utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[DataClassification.labels[obj.data_class].encode('utf8')] = [
                obj.name.encode('utf8'), ]

    # Record FTP request to database
    # DETAILS: user, request name, for item(ceph_obj) in cart, date, EULA?
    ftp_request = FTPRequest(name=time.strftime("ftprequest_%Y-%m-%d_%H%M"),
                             user=request.user)

    ftp_request.size_in_bytes = total_size_in_bytes
    ftp_request.num_tiles = num_tiles
    ftp_request.save()

    # Mapping of FTP Request to requested objects
    ftp_objs = []
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.object_id))
        ftp_objs.append(obj)
        ftp_obj_idx = FTPRequestToObjectIndex(ftprequest=ftp_request,
                                              cephobject=obj)
        ftp_obj_idx.save()

    # Call to celery
    process_ftp_request.delay(ftp_request, obj_name_dict, srs_epsg)

    # Clear cart items
    delete_all_items_from_cart(request)

    return render_to_response('ftp_result.html',
                              {   "result_msg" : "Your FTP request is being processed. A notification \
                                     will arrive via email regarding the completion of your request. The \
                                     items you requested are listed below.",
                                  "ftp_objects": ftp_objs,
                                  "total_size": total_size_in_bytes, },
                              context_instance=RequestContext(request))


@login_required
def ftp_request_list(request, sort=None):

    if sort not in utils.FTP_SORT_TYPES and sort != None:
        return HttpResponse(status=404)

    ftp_list = []
    sorted_list = []

    # Query all ftp requests for this user
    ftp_list = FTPRequest.objects.filter(user=request.user)

    # Sort by specified attribute
    if sort == 'date':
        sorted_list = sorted(ftp_list.order_by(
            'name'), key=operator.attrgetter('date_time'), reverse=True)
    elif sort == 'status':
        sorted_list = sorted(ftp_list.order_by(
            'name'), key=operator.attrgetter('status'), reverse=True)
    elif sort == 'size':
        sorted_list = sorted(ftp_list.order_by(
            'name'), key=operator.attrgetter('size_in_bytes'), reverse=True)

    else:  # default
        sorted_list = ftp_list

    paginator = Paginator(sorted_list, 10)

    page = request.GET.get('page')

    try:
        paged_list = paginator.page(page)
    except PageNotAnInteger:
        paged_list = paginator.page(1)
    except EmptyPage:
        paged_list = paginator.page(paginator.num_pages)

    return render(request, "ftp_list.html",
                  {"ftp_request_list": paged_list,
                   "sort_types": utils.FTP_SORT_TYPES,
                   "status_labels": FTPStatus.labels,
                   "sort": sort, })


@login_required
def ftp_request_details(request, ftp_req_name=None):
    if ftp_req_name is None:
        return HttpResponse(status=404)

    ftp_request_obj = FTPRequest.objects.get(
        name=ftp_req_name, user=request.user)
    ftp_to_objects_rel = FTPRequestToObjectIndex.objects.filter(
        ftprequest=ftp_request_obj).select_related("cephobject")
    ceph_objects = []
    for i in ftp_to_objects_rel:
        ceph_objects.append(i.cephobject)

    context_dict = {
        "req_details": ftp_request_obj,
        "objects": ceph_objects,
        "num_items": len(ceph_objects)
    }

    return render(request, "ftp_details.html", context_dict)


@login_required
def tile_check(request):
    user = request.user
    response = "false"
    if not request.POST:
        raise PermissionDenied
    try:
        json_tiles = UserTiles.objects.get(user=user)
    except ObjectDoesNotExist as e:
        return HttpResponse(status=404)

    georefs = map(str, request.POST.get('georefs', ''))
    reference_tiles = map(str, json.loads(json_tiles))
    valid_tiles = []
    for x in georefs:
        if x in georefs:
            valid_tiles.append(x)

    return HttpResponse(json.dumps(valid_tiles), status=200)


@login_required
def clear_cart(request):
    delete_all_items_from_cart(request)
    response = render_to_response('cart.html',
                                  dict(cart=CartProxy(request)),
                                  context_instance=RequestContext(request))

    response.delete_cookie("cart")
    return response

### HELPER FUNCTIONS ###


def delete_all_items_from_cart(request, warn_user=True):
    if request.cart is not None:
        remove_all_from_cart(request)  # Clear cart for this request
    user = request.user
    name = user.username
    if warn_user:
        messages.add_message(request, messages.INFO,
                             "Cart has been emptied for user [{0}]".format(name))


def count_duplicate_requests(ftp_request):
    return len(FTPRequest.objects.filter(name=ftp_request.name, user=ftp_request.user))


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/', redirect_field_name='')
def management(request):
    return render_to_response('ceph_manager.html', context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_lidar_coverage(request):
    update_lidar_coverage_task.delay()
    messages.error(request, "Updating LiDAR Coverage")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_fhm_metadata(request):
    # fhm_metadata_update.delay()
    update_fhm_metadata_task.delay()
    messages.error(request, "Updating Flood Hazard Map metadata")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_pl2_metadata(request):
    pl2_metadata_update.delay()
    messages.error(request, "Updating Resource Layers Metadata")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_sar_metadata(request):
    sar_metadata_update.delay()
    messages.error(request, "Updating SAR Metadata")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def seed_fhm_layers(request):
    keyword = 'hazard'
    seed_layers.delay(keyword)
    messages.error(request, "Seeding Flood Hazard Maps")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def seed_SAR_DEM(request):
    keyword = 'SAR'
    seed_layers.delay(keyword)
    messages.error(request, "Seeding SAR DEM")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def seed_resource_layers(request):
    keyword = 'PhilLiDAR2'
    seed_layers.delay(keyword)
    messages.error(request, "Seeding Resource Layers")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def fhm_default_style(request):
    keyword = 'Hazard'
    layer_default_style.delay(keyword)
    messages.error(request, "Updating Default Style of FHMs")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def rl_default_style(request):
    keyword = 'PhilLiDAR2'
    layer_default_style.delay(keyword)
    messages.error(request, "Updating Default Style of Resource Layers")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def sar_default_style(request):
    keyword = 'SAR'
    layer_default_style.delay(keyword)
    messages.error(request, "Updating Default Style of SAR")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def dem_cov_default_style(request):
    # no keyword
    keyword = 'dem_'
    layer_default_style.delay(keyword)
    messages.error(request, "Updating Default Style of DEM Coverage")
    return HttpResponseRedirect(reverse('data_management'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def jurisdict_default_style(request):
    # no keyword
    keyword = 'jurisdict'
    layer_default_style.delay(keyword)
    messages.error(
        request, "Updating Default Style of Jurisdiction Shapefiles")
    return HttpResponseRedirect(reverse('data_management'))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_floodplain_keywords(request):
    floodplain_keywords.delay()
    messages.error(request, "Inserting FP/RB SUC keywords on layers")
    return HttpResponseRedirect(reverse('data_management'))


