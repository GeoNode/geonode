# Create your views here.
from django.http import HttpResponse
import django.contrib.gis.geos as geos
from django.contrib.gis.gdal.envelope import Envelope
from vectorformats.Formats import Django, GeoJSON
from geonode.maps.models import Map
from django.contrib.auth.models import User
from geonode.geoanno.models import GeoAnnotation
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
import re

import json


def serialize(features, properties=None):
    if not properties:
        properties = ['title', 'description']
    djf = Django.Django(geodjango="geometry", properties=properties) 
    geoj = GeoJSON.GeoJSON()
    jsonstring = geoj.encode(djf.decode(features))
    return jsonstring

def applyGeometry(obj, feature):
    geometry_type = feature.geometry['type']
    if geometry_type.startswith("Multi"):
        geomcls = getattr(geos, feature.geometry['type'].replace("Multi", ""))
        geoms = []
        for item in feature.geometry['coordinates']:
            geoms.append(geomcls(*item))
        geom = getattr(geos,feature.geometry['type'])(geoms)    
    else:
        geomcls = getattr(geos, feature.geometry['type'])
        geom = geomcls(*feature.geometry['coordinates'])
    obj.geometry = geom
    for key, value in feature.properties.items():
        setattr(obj, key, value)
    obj.save()    
    return obj


@csrf_exempt
def annotations(request, mapid, id=None):
    geoj = GeoJSON.GeoJSON()
    if id != None:
        obj = GeoAnnotation.objects.get(pk=id)
        if  request.method == "DELETE":
            obj.delete()
            return HttpResponse(status=200)
        elif request.method != "GET":
            features = geoj.decode(request.raw_post_data)
            obj = apply(obj, features[0])
        return HttpResponse(serialize([obj], ['title','content']))
    if request.method == "GET":
        bbox = [float(n) for n in re.findall('[0-9\.\-]+', request.GET["bbox"])]
        features = GeoAnnotation.objects.filter(map=Map.objects.get(pk=mapid),geometry__intersects=Envelope(bbox).wkt)
    else:
        features = geoj.decode(request.raw_post_data)
        created_features = []
        for feature in features:
            obj = GeoAnnotation(map=Map.objects.get(id=mapid), owner=request.user)
            obj = applyGeometry(obj, feature)
            obj.save()
            created_features.append(obj)
        features = created_features
    return HttpResponse(serialize(features, ['title','content']))

def annotation_details(request, id):
    annotation = GeoAnnotation.objects.get(pk=id)
    return render_to_response('geoanno/annotation.html', RequestContext(request, {
        "annotation": annotation
    }))

        