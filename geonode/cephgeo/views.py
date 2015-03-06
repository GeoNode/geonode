from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import client 
import utils
import local_settings

# Create your views here.
@login_required
def file_list(request, sort=None):
	
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
					{"file_list"	: paged_objects, 
					"file_types"	: utils.TYPE_TO_IDENTIFIER_DICT , 
					"sort_types"	: utils.SORT_TYPES, 
					"sort"			: sort})
