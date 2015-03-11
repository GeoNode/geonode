from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.encoding import smart_str
from django.contrib import messages
from django.http import HttpResponseRedirect,HttpResponse
from django.core import serializers

from pprint import pprint

from geonode.cephgeo.forms import DataInputForm
from geonode.cephgeo.models import CephDataObject

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
            return HttpResponseRedirect('/cephgeo/list/nosort/')
        else:
            messages.error(request, "Invalid input on data form")
            return HttpResponseRedirect('/cephgeo/input/')
    # if a GET (or any other method) we'll create a blank form
    else:
        form = DataInputForm()

    return render(request, 'ceph_data_input.html', {'data_input_form': form})

@login_required
def error(request):
    return render(request, "ceph_error.html",
                    {"err_msg"  : request.error,})
