from django.http import HttpResponse
import django.contrib.gis.geos as geos
from django.contrib.gis.gdal.envelope import Envelope
from django.shortcuts import render
from vectorformats.Formats import Django, GeoJSON
from geonode.maps.models import Map
from .models import MapNote
from django.views.decorators.csrf import csrf_exempt
import re


def serialize(features, properties=None):
    if not properties:
        properties = ['title', 'description', 'owner_id']
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
        geom = getattr(geos, feature.geometry['type'])(geoms)
    else:
        geomcls = getattr(geos, feature.geometry['type'])
        geom = geomcls(*feature.geometry['coordinates'])
    obj.geometry = geom
    for key, value in feature.properties.items():
        if key != 'owner_id':
            setattr(obj, key, value)
    obj.save()
    return obj


@csrf_exempt
def annotations(request, mapid, id=None):
    geoj = GeoJSON.GeoJSON()
    if id is not None:
        obj = MapNote.objects.get(pk=id)
        map_obj = Map.objects.get(id=mapid)
        if request.method == "DELETE":
            if request.user.id == obj.owner_id or request.user.has_perm('maps.change_map', obj=map_obj):
                obj.delete()
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=403)
        elif request.method != "GET":
            if request.user.id == obj.owner_id:
                features = geoj.decode(request.raw_post_data)
                obj = applyGeometry(obj, features[0])
            else:
                return HttpResponse(status=403)
        return HttpResponse(serialize([obj], ['title', 'content', 'owner_id']), status=200)
    if request.method == "GET":
        bbox = [float(n) for n in re.findall(r'[0-9\.\-]+', request.GET["bbox"])]
        features = MapNote.objects.filter(map=Map.objects.get(pk=mapid), geometry__intersects=Envelope(bbox).wkt)
    else:
        if request.user.id is not None:
            features = geoj.decode(request.body)
            created_features = []
            for feature in features:
                obj = MapNote(map=Map.objects.get(id=mapid), owner=request.user)
                obj = applyGeometry(obj, feature)
                created_features.append(obj)
            features = created_features
        else:
            return HttpResponse(status=301)
    data = serialize(features, ['title', 'content', 'owner_id'])
    if 'callback' in request:
        data = '%s(%s);' % (request['callback'], data)
        return HttpResponse(data, "text/javascript")
    return HttpResponse(data, "application/json")


@csrf_exempt
def annotation_details(request, id):
    annotation = MapNote.objects.get(pk=id)
    return render(request, 'mapnotes/annotation.html', {
        "owner_id": request.user.id,
        "annotation": annotation,
    })
