import json
import xmlrpclib

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import serializers

from haystack.inputs import AutoQuery, Raw 
from haystack.query import SearchQuerySet, SQ
from django.db.models import Sum
from django.contrib.gis.geos import GEOSGeometry

from geonode.maps.views import default_map_config, Map, Layer

default_facets = ["map", "layer", "vector", "raster", "contact"]
fieldsets = {
	"brief": ["name", "type", "description"],
	"summary": ["name", "type", "description", "owner"],
	"full": ["name", "type", "description", "owner", "language"],
}


def search(request):
	"""
	View that drives the search page
	"""

	DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
	#DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)
	# for non-ajax requests, render a generic search page

	params = dict(request.REQUEST)

	map = Map(projection="EPSG:900913", zoom=1, center_x=0, center_y=0)

	# Default Counts to 0, JS will Load the Correct Counts
	facets = {}
	for facet in default_facets:
		facets[facet] = 0

	return render_to_response("search/search.html", RequestContext(request, {
		"init_search": json.dumps(params),
		#'viewer_config': json.dumps(map.viewer_json(added_layers=DEFAULT_BASE_LAYERS, authenticated=request.user.is_authenticated())),
		"viewer_config": json.dumps(map.viewer_json(*DEFAULT_BASE_LAYERS)),
		"GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
		"site": settings.SITEURL,
		"facets": facets,
		"keywords": Layer.objects.gn_catalog.get_all_keywords()
	}))


def search_api(request):
	"""
	View that drives the search api
	"""

	# Retrieve Query Params
	id = request.REQUEST.get("id", None)
	query = request.REQUEST.get('q',None)
	name = request.REQUEST.get("name", None)
	category = request.REQUEST.get("cat", None)
	limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20)))
	startIndex = int(request.REQUEST.get("startIndex", 0))
	startPage = int(request.REQUEST.get("startPage", 0))
	sort = request.REQUEST.get("sort", "relevance")
	order = request.REQUEST.get("order", "asc")
	type = request.REQUEST.get("type", None)
	fields = request.REQUEST.get("fields", None)
	fieldset = request.REQUEST.get("fieldset", None)
	format = request.REQUEST.get("format", "json")
	# Geospatial Elements
	bbox = request.REQUEST.get("bbox", None)

	sqs = SearchQuerySet()

	# Filter by ID
	if id:
		sqs = sqs.narrow("django_id:%s" % id)

	# Filter by Type
	if type is not None:
		if type in ["map", "layer", "contact"]:
			# Type is one of our Major Types (not a sub type)
			sqs = sqs.narrow("type:%s" % type)
		elif type in ["vector", "raster"]:
			# Type is one of our sub types
			sqs = sqs.narrow("subtype:%s" % type)

	# Filter by Query Params
	if query:
		sqs = sqs.filter(content=Raw(query))
		
	# filter by cateory
	
	if category is not None:
		sqs = sqs.narrow('category:%s' % category)

	# Apply Sort
	# TODO: Handle for Revised sort types
	# [relevance, alphabetically, rating, created, updated, popularity]
	if sort.lower() == "newest":
		sqs = sqs.order_by("-date")
	elif sort.lower() == "oldest":
		sqs = sqs.order_by("date")
	elif sort.lower() == "alphaaz":
		sqs = sqs.order_by("title")
	elif sort.lower() == "alphaza":
		sqs = sqs.order_by("-title")
		
	# Setup Search Results
	results = []
	
	#if bbox is not None:
	#	left,bottom,right,top = bbox.split(',')
	#	sqs = sqs.filter(
	#		# first check if the bbox has at least one point inside the window
	#		SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) & SQ(bbox_top__gte=bottom) & SQ(bbox_top__lte=top) | #check top_left is inside the window
	#		SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) & SQ(bbox_top__lte=top) &  SQ(bbox_top__gte=bottom) | #check top_right is inside the window
	#		SQ(bbox_bottom__gte=bottom) & SQ(bbox_bottom__lte=top) & SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) | #check bottom_right is inside the window
	#		SQ(bbox_top__lte=top) & SQ(bbox_top__gte=bottom) & SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) | #check bottom_left is inside the window
	#		# then check if the bbox is including the window
	#		SQ(bbox_left__lte=left) & SQ(bbox_right__gte=right) & SQ(bbox_bottom__lte=bottom) & SQ(bbox_top__gte=top)
	#	)
	
	for i, result in enumerate(sqs):
		if result.type == 'layer':
			if not request.user.has_perm('maps.view_layer',obj = result.object):
				sqs = sqs.exclude(id = result.id)
		if result.type == 'map':
			if not request.user.has_perm('maps.view_map',obj = result.object):
				sqs = sqs.exclude(id = result.id)

	# Build the result based on the limit
	for i, result in enumerate(sqs[startIndex:startIndex + limit]):
		data = json.loads(result.json)
		data.update({"iid": i + startIndex})
		results.append(data)
	
	# Filter Fields/Fieldsets
	if fieldset:
		if fieldset in fieldsets.keys():
			for result in results:
				for key in result.keys():
					if key not in fieldsets[fieldset]:
						del result[key]
	elif fields:
		fields = fields.split(',')
		for result in results:
			for key in result.keys():
				if key not in fields:
					del result[key]        

	# Setup Facet Counts
	sqs = sqs.facet("type").facet("subtype")
	
	sqs = sqs.facet('category')

	facets = sqs.facet_counts()

	# Prepare Search Results
	data = {
		"success": True,
		"total": sqs.count(),
		"query_info": {
			"q": query,
			"startIndex": startIndex,
			"limit": limit,
			"sort": sort,
			"type": type,
		},
		"facets": facets,
		"results": results,
		"counts": dict(facets.get("fields")['type']+facets.get('fields')['subtype']),
		"categories": [facet[0] for facet in facets.get('fields')['category']]
	}

	# Return Results
	if format:
		if format == "xml":
			return HttpResponse(xmlrpclib.dumps((data,), allow_none=True), mimetype="text/xml")
		elif format == "json":
			return HttpResponse(json.dumps(data), mimetype="application/json")
	else:
		return HttpResponse(json.dumps(data), mimetype="application/json")
