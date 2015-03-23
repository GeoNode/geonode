from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import smart_str
from django.contrib import messages
from django.http import HttpResponseRedirect,HttpResponse
from django.core import serializers
from django.template import RequestContext

from pprint import pprint

from geonode.cephgeo.forms import DataInputForm
from geonode.cephgeo.models import CephDataObject
from geonode.tasks.ftp import process_ftp_request

from changuito import CartProxy
from changuito.proxy import ItemDoesNotExist

from sqlite3 import OperationalError

import client, utils, local_settings, cPickle, unicodedata, time, operator, json

# Create your views here.
@login_required
def file_list_ceph(request, sort=None):
    
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
    else: # nosort
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
    else: # nosort
        sorted_list = object_list
    
    response_data = {"file_list"    : serializers.serialize('json', sorted_list), 
                    "file_types"    : utils.TYPE_TO_IDENTIFIER_DICT , 
                    "sort_types"    : utils.SORT_TYPES, 
                    "sort"          : sort,
                    "grid_ref"      : grid_ref,}
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")
    
@login_required
def data_input(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
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
            
            messages.success(request, "Data has been succesfully encoded!")
            return HttpResponseRedirect('/ceph/list/nosort/')
        else:
            messages.error(request, "Invalid input on data form")
            return HttpResponseRedirect('/ceph/input/')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = DataInputForm()

    return render(request, 'ceph_data_input.html', {'data_input_form': form})

@login_required
def error(request):
    return render(request, "ceph_error.html",
                    {"err_msg"  : request.error,})

@login_required
def get_cart(request):
    # DEBUG CALLS
    cart=CartProxy(request)
    if not cart.is_empty():
        remove_all_from_cart(request) # Clear cart for this user
        
    for ceph_obj in CephDataObject.objects.all():
        print("Adding [{0}] to cart...".format(ceph_obj.name))
        add_to_cart_unique(request, ceph_obj.id)
        #add_to_cart(request, ceph_obj.id)
    
    # END DEBUG
    return render_to_response('cart.html', 
                                dict(cart=CartProxy(request)),
                                context_instance=RequestContext(request))

@login_required
def get_cart_json(request):
    cart = CartProxy(request)
    #~ json_cart = dict()
    #~ for item in cart:
        #~ json_cart[str(item.pk)] = serializers.serialize('json', CephDataObject.objects.get(id=int(item.pk)))
    #~ return HttpResponse(json.dumps(json_cart), content_type="application/json")
    obj_name_dict = dict()
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.pk))
        if obj.geo_type in obj_name_dict:
            obj_name_dict[obj.geo_type.encode('utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[obj.geo_type.encode('utf8')] = [obj.name.encode('utf8'),]
    obj_name_dict = [CephDataObject.objects.get(id=int(item.pk)).name for item in cart]
    return HttpResponse(json.dumps(obj_name_dict) , content_type="application/json")

@login_required
def get_obj_ids_json(request):
    cart = CartProxy(request)
    json_cart = dict()
    ceph_objs = CephDataObject.objects.all()
    ceph_objs_by_geotype = utils.ceph_object_ids_by_geotype(ceph_objs)
    pprint(ceph_objs_by_geotype)
    return HttpResponse(json.dumps(ceph_objs_by_geotype), content_type="application/json")

@login_required
def create_ftp_folder(request):
    cart=CartProxy(request)
    if cart.is_empty():
        messages.add_message(request, messages.ERROR, "ERROR: Cart is empty, cannot process an empty FTP request!")
        return render_to_response('cart.html', 
                                    dict(cart=CartProxy(request)),
                                    context_instance=RequestContext(request))
    #[CephDataObject.objects.get(id=int(item.pk)).name for item in cart]
    
    obj_name_dict = dict()
    for item in cart:
        obj = CephDataObject.objects.get(id=int(item.pk))
        if obj.geo_type in obj_name_dict:
            obj_name_dict[obj.geo_type.encode('utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[obj.geo_type.encode('utf8')] = [obj.name.encode('utf8'),]
    username = request.user.get_username()
    
    #Debug Step
    if username == "admin":
        username = "test-ftp-user"
    email = request.user.email
    request_name=time.strftime("ftp_request-%Y_%m_%d")
    
    # Call to celery
    process_ftp_request.delay(username, email, request_name, obj_name_dict)
    messages.add_message(request, messages.INFO, "FTP request is being processed")
    
    #~ tojson = (username, email, request_name, obj_name_dict)
    #~ return HttpResponse(json.dumps(tojson), content_type="application/json")
    return render_to_response('cart.html', 
                                dict(cart=CartProxy(request)),
                                context_instance=RequestContext(request))

###
# CART UTILS
###
@login_required
def add_to_cart(request, ceph_obj_id, quantity=1):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = request.cart 
    cart.add(product, utils.compute_price(product.geo_type), quantity)

@login_required
def add_to_cart_unique(request, ceph_obj_id):
    product = CephDataObject.objects.get(id=ceph_obj_id)
    cart = request.cart 
    try:
        cart.get_item(ceph_obj_id)
    except ItemDoesNotExist:
        cart.add(product, utils.compute_price(product.geo_type), 1)

@login_required
def remove_from_cart(request, ceph_obj_id):
    cart = request.cart 
    cart.remove_item(ceph_obj_id)
    
@login_required
def remove_all_from_cart(request):
    cart = request.cart 
    if request.user.is_authenticated():
        cart.delete_old_cart(request.user)
    
