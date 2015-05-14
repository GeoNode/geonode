from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import smart_str
from django.contrib import messages
from django.core import serializers
from django.template import RequestContext

from pprint import pprint

from geonode.cephgeo.forms import DataInputForm, UserRegistrationForm1, UserRegistrationForm2
from geonode.cephgeo.models import CephDataObject, FTPRequest, FTPStatus, FTPRequestToObjectIndex
from geonode.tasks.ftp import process_ftp_request

from geonode.cephgeo.cart_utils import *

import client, utils, local_settings, cPickle, unicodedata, time, operator, json

# Create your views here.
@login_required
def file_list_ceph(request, sort=None):
    if request.user.is_superuser:
        if sort not in utils.SORT_TYPES and sort != None:
            return HttpResponse(status=404)
            
        cephclient = client.CephStorageClient(local_settings.CEPH_USER,local_settings.CEPH_KEY,local_settings.CEPH_URL) 
        object_list = cephclient.list_files(container_name=local_settings.DEFAULT_CONTAINER)
        sorted_list = []
        
        for ceph_object in object_list:
            ceph_object["type"] = utils.file_classifier(ceph_object["name"])
            ceph_object["uploaddate"] = ceph_object["last_modified"]
        
        ###sorting goes here
        if sort != None:
            sorted_list = utils.sort_by(sort, object_list)
            paginator = Paginator(sorted_list, 10)
        else:
            paginator = Paginator(object_list, 10)
        
        page = request.GET.get('page')
        
        try:
            paged_objects = paginator.page(page)
        except PageNotAnInteger:
            paged_objects = paginator.page(1)
        except EmptyPage:
            paged_objects = paginator.page(paginator.num_pages)
        
        return render(request, "file_list.html",
                        {"file_list"    : paged_objects, 
                        "file_types"    : utils.TYPE_TO_IDENTIFIER_DICT , 
                        "sort_types"    : utils.SORT_TYPES, 
                        "sort"          : sort})
    else:
        raise PermissionDenied()

@login_required
def file_list_geonode(request, sort=None, grid_ref=None):
    
    if sort not in utils.SORT_TYPES and sort != None:
        return HttpResponse(status=404)
    
    object_list = []
    sorted_list = []
    
    #No Grid Ref
    if grid_ref is None:
        object_list = CephDataObject.objects.all()
        
    else:
        #1 Grid Ref or Grid Ref Range
        if utils.is_valid_grid_ref(grid_ref):
            # Query files with same grid reference
            object_list = CephDataObject.objects.filter(name__startswith=grid_ref)
        else:
            return HttpResponse(status=404)
    
    if sort == 'type':
        sorted_list = sorted(object_list.order_by('name'), key=operator.attrgetter('geo_type'))
    elif sort == 'uploaddate':
        sorted_list = sorted(object_list.order_by('name'), key=operator.attrgetter('last_modified'), reverse=True)
        #~ sorted_list = object_list.order_by('-last_modified')
    elif sort == 'name':
        sorted_list = sorted(object_list, key=operator.attrgetter('name'))
    else: # default
        sorted_list = object_list
    
    paginator = Paginator(sorted_list, 10)
    
    page = request.GET.get('page')
    
    try:
        paged_objects = paginator.page(page)
    except PageNotAnInteger:
        paged_objects = paginator.page(1)
    except EmptyPage:
        paged_objects = paginator.page(paginator.num_pages)
    
    return render(request, "file_list_geonode.html",
                    {"file_list"    : paged_objects, 
                    "file_types"    : utils.TYPE_TO_IDENTIFIER_DICT , 
                    "sort_types"    : utils.SORT_TYPES, 
                    "sort"          : sort,
                    "grid_ref"      : grid_ref})
                    
@login_required
def file_list_json(request, sort=None, grid_ref=None):
    
    if sort not in utils.SORT_TYPES and sort != None:
        return HttpResponse(status=404)
    
    object_list = []
    sorted_list = []
    
    #No Grid Ref
    if grid_ref is None:
        object_list = CephDataObject.objects.all()
        
    else:
        #1 Grid Ref or Grid Ref Range
        if utils.is_valid_grid_ref(grid_ref):
            # Query files with same grid reference
            object_list = CephDataObject.objects.filter(name__startswith=grid_ref)
        else:
            return HttpResponse(status=404)
    
    if sort == 'type':
        sorted_list = sorted(object_list.order_by('name'), key=operator.attrgetter('geo_type'))
    elif sort == 'uploaddate':
        sorted_list = sorted(object_list.order_by('name'), key=operator.attrgetter('last_modified'), reverse=True)
        #~ sorted_list = object_list.order_by('-last_modified')
    elif sort == 'name':
        sorted_list = sorted(object_list, key=operator.attrgetter('name'))
    else: # default
        sorted_list = object_list
    
    response_data = {"file_list"    : serializers.serialize('json', sorted_list), 
                    "file_types"    : utils.TYPE_TO_IDENTIFIER_DICT , 
                    "sort_types"    : utils.SORT_TYPES, 
                    "sort"          : sort,
                    "grid_ref"      : grid_ref,}
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")
    
@login_required
def data_input(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            # pprint(request.POST)
            form = DataInputForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                data = form.cleaned_data['data']
                uploaded_objects = cPickle.loads(smart_str(data))
                #pprint(uploaded_objects)
                is_pickled = form.cleaned_data['pickled']
                
                #Save each ceph object
                for obj_meta_dict in uploaded_objects:
                    ceph_obj = CephDataObject(  name = obj_meta_dict['name'],
                                                #last_modified = time.strptime(obj_meta_dict['last_modified'], "%Y-%m-%d %H:%M:%S"),
                                                last_modified = obj_meta_dict['last_modified'],
                                                size_in_bytes = obj_meta_dict['bytes'],
                                                content_type = obj_meta_dict['content_type'],
                                                geo_type = utils.file_classifier(obj_meta_dict['name']),
                                                file_hash = obj_meta_dict['hash'],
                                                grid_ref = obj_meta_dict['grid_ref'])
                    ceph_obj.save()
                
                messages.success(request, "Data has been succesfully encoded. [{0}] files uploaded to Ceph.".format(len(uploaded_objects)))
                return redirect('geonode.cephgeo.views.file_list_geonode',sort='uploaddate')
            else:
                messages.error(request, "Invalid input on data form")
                return redirect('geonode.cephgeo.views.data_input')
        # if a GET (or any other method) we'll create a blank form
        else:
            form = DataInputForm()
            return render(request, 'ceph_data_input.html', {'data_input_form': form})
    else:
        #return HttpResponseForbidden(u"You do not have permission to view this page!")
        raise PermissionDenied()

@login_required
def error(request):
    return render(request, "ceph_error.html",
                    {"err_msg"  : request.error,})

@login_required
def get_cart(request):
    return render_to_response('cart.html', 
                                dict(cart=CartProxy(request)),
                                context_instance=RequestContext(request))

@login_required
def get_cart_json(request):
    cart = CartProxy(request)
    #~ json_cart = dict()
    #~ for item in cart:
        #~ json_cart[str(item.object_id)] = serializers.serialize('json', CephDataObject.objects.get(id=int(item.pk)))
    #~ return HttpResponse(json.dumps(json_cart), content_type="application/json")
    
    # TODO: debug serialization for CephDataObjects
    #~ obj_name_dict = dict()
    #~ for item in cart:
        #~ obj = CephDataObject.objects.get(id=int(item.object_id))
        #~ if obj.geo_type in obj_name_dict:
            #~ obj_name_dict[obj.geo_type.encode('utf8')].append(obj.name.encode('utf8'))
        #~ else:
            #~ obj_name_dict[obj.geo_type.encode('utf8')] = [obj.name.encode('utf8'),]
            #~ 
    obj_name_dict = [CephDataObject.objects.get(id=int(item.object_id)).name for item in cart]
    return HttpResponse(json.dumps(obj_name_dict) , content_type="application/json")

@login_required
def get_obj_ids_json(request):
    cart = CartProxy(request)
    json_cart = dict()
    ceph_objs = CephDataObject.objects.all()
    ceph_objs_by_geotype = utils.ceph_object_ids_by_geotype(ceph_objs)
    #pprint(ceph_objs_by_geotype)
    return HttpResponse(json.dumps(ceph_objs_by_geotype), content_type="application/json")

@login_required
def create_ftp_folder(request):
    cart=CartProxy(request)
    
    #[CephDataObject.objects.get(id=int(item.object_id)).name for item in cart]
    
    obj_name_dict = dict()
    total_size_in_bytes = 0
    num_tiles = 0
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.object_id))
        total_size_in_bytes += obj.size_in_bytes
        num_tiles += 1
        if obj.geo_type in obj_name_dict:
            obj_name_dict[obj.geo_type.encode('utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[obj.geo_type.encode('utf8')] = [obj.name.encode('utf8'),]
    username = request.user.get_username()
    
    # Record FTP request to database
    # DETAILS: user, request name, for item(ceph_obj) in cart, date, EULA?
    ftp_request = FTPRequest(   name = time.strftime("ftp_request-%Y_%m_%d"),
                                user = request.user)
    
    # Check for duplicates and handle accordingly
    if count_duplicate_requests(ftp_request) > 0:
        ftp_request.status = FTPStatus.DUPLICATE
    
    ftp_request.size_in_bytes = total_size_in_bytes
    ftp_request.num_tiles = num_tiles
    ftp_request.save()
    
    # Mapping of FTP Request to requested objects
    ftp_objs = []
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.object_id))
        ftp_objs.append(obj)
        ftp_obj_idx = FTPRequestToObjectIndex(  ftprequest = ftp_request, 
                                                cephobject = obj)
        ftp_obj_idx.save()
    
    
    # Call to celery
    process_ftp_request.delay(ftp_request, obj_name_dict)
    
    # Clear cart items
    delete_all_items_from_cart(request)
    
    
    return render_to_response('ftp_result.html', 
                                {   "result_msg" : "Your FTP request is being processed. A notification \
                                     will arrive via email regarding the completion of your request. The \
                                     items you requested are listed below.",
                                    "ftp_objects" : ftp_objs,
                                    "total_size" : total_size_in_bytes,},
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
        sorted_list = sorted(ftp_list.order_by('name'), key=operator.attrgetter('date_time'), reverse=True)
    elif sort == 'status':
        sorted_list = sorted(ftp_list.order_by('name'), key=operator.attrgetter('status'), reverse=True)
    elif sort == 'size':
        sorted_list = sorted(ftp_list.order_by('name'), key=operator.attrgetter('size_in_bytes'), reverse=True)
        
    else: # default
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
                    {"ftp_request_list"    : paged_list, 
                    "sort_types"    : utils.FTP_SORT_TYPES, 
                    "status_labels"    : FTPStatus.labels, 
                    "sort"          : sort,})

@login_required
def clear_cart(request):
    delete_all_items_from_cart(request)
    response = render_to_response('cart.html', 
                                dict(cart=CartProxy(request)),
                                context_instance=RequestContext(request))
    
    response.delete_cookie("cart")
    return response

def user_registration(request, page=None):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # pprint(request.POST)
        form = UserRegistrationForm1(request.POST)
        # check whether it's valid:
        if form.is_valid():
            messages.info(request, "User registration form completion success!")
            return redirect('ceph_main')
        else:
            messages.error(request, "Invalid input on user registration form")
            return redirect('ceph_main')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = UserRegistrationForm1()
        if page is '1':
            form = UserRegistrationForm1()
        elif page is '2':
            form = UserRegistrationForm2()
        return render(request, 'user_registration.html', {'user_reg_form': form})
### HELPER FUNCTIONS ###

def delete_all_items_from_cart(request, warn_user=True):
    if request.cart is not None:
        remove_all_from_cart(request) # Clear cart for this request
    user = request.user
    name = user.username
    if warn_user:
        messages.add_message(request, messages.INFO, "Cart has been emptied for user [{0}]".format(name))

def count_duplicate_requests(ftp_request):
    return len(FTPRequest.objects.filter(name=ftp_request.name,user=ftp_request.user))
