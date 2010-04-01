from geonode.maps.models import Map, Layer, MapLayer
import geoserver
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext
from django.utils.html import escape
from django.utils.translation import ugettext as _
import json

DEFAULT_MAP_CONFIG = {
    "alignToGrid": True,
    "proxy": "/proxy/?url=",
    "about": {
        "title": "GeoNode Default Map",
        "abstract": "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the Save Map button above to contribute your map to the GeoNode community.",
        "contact": "For more information, contact OpenGeo at http://opengeo.org/"
    },
    "wms": {
        "capra": "%swms" % settings.GEOSERVER_BASE_URL
    },
    "map": {
        "layers": [ {
            "name": settings.DEFAULT_MAP_BASE_LAYER,
            "wms": "capra"
        } ],
        "center": settings.DEFAULT_MAP_CENTER,
        "zoom": settings.DEFAULT_MAP_ZOOM
    }
}

def maps(request, mapid=None):
    if request.method == 'GET' and mapid is None:
        map_configs = [{"id": map.pk, "config": build_map_config(map)} for map in Map.objects.all()]
        return HttpResponse(json.dumps({"maps": map_configs}), mimetype="application/json")
    elif request.method == 'GET' and mapid is not None:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
        return HttpResponse(json.dumps(config))
    elif request.method == 'POST':
        try: 
            map = read_json_map(request.raw_post_data)
            response = HttpResponse('', status=201)
            response['Location'] = map.id
            return response
        except:
            return HttpResponse(
                "The server could not understand your request.",
                status=400, 
                mimetype="text/plain"
            )

def mapJSON(request,mapid):
	map = Map.objects.get(pk=mapid)
	config = build_map_config(map)
	return HttpResponse(json.dumps(config))

def read_json_map(json_text):
    conf = json.loads(json_text)
    title = conf['about']['title']
    abstract = conf['about']['abstract']
    contact = conf['about']['contact']
    zoom = conf['map']['zoom']
    center_lon = conf['map']['center'][0]
    center_lat = conf['map']['center'][1]

    featured = conf['about'].get('featured', False)

    map = Map.objects.create(
        title=title, 
        abstract=abstract, 
        contact=contact, 
        zoom=zoom, 
        center_lon=center_lon, 
        center_lat=center_lat, 
        featured=featured
    )

    if 'wms' in conf and 'layers' in conf['map']:
        services = conf['wms']
        layers = conf['map']['layers']
        ordering = 0
        for l in layers:
            if 'wms' in l and l['wms'] in services:
                name = l['name']
                group = l.get('group', '')
                ows = services[l['wms']]
                map.layer_set.create(name=name, group=group, ows_url=ows, stack_order=ordering)
                ordering = ordering + 1

    return map


def newmap(request):
    '''
    View that creates a new map.  
    
    If the query argument 'copy' is given, the inital map is
    a copy of the map with the id specified, otherwise the 
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        map = get_object_or_404(Map,pk=mapid) 
        config = build_map_config(map)
        del config['id']
    else:
        query = request.META['QUERY_STRING']
        if query.startswith("layer"):
            layer_name = request.GET['layer']
            layer = Layer.objects.get(name=layer_name)
            config = DEFAULT_MAP_CONFIG
            config['map']['layers'].append({'name': "%s:%s" % (layer.workspace,layer.name), 
                                            'wms' : 'capra'})
        else:
            config = DEFAULT_MAP_CONFIG
    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config), 
        'bg': json.dumps(settings.MAP_BASELAYERS),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL
    }))


@login_required
def deletemap(request, mapid):
    '''
    '''
    # XXX transaction?
    map = get_object_or_404(Map,pk=mapid) 
    is_featured = map.featured
    layers = MapLayer.objects.filter(map=map.id) 
     
    map.delete()
    for layer in layers:
        layer.delete()
    if is_featured:
        return HttpResponseRedirect(reverse('geonode.views.curated'))
    else:
        return HttpResponseRedirect(reverse('geonode.views.community'))

def mapdetail(request,mapid): 
    '''
    The view that show details of each map
    '''
    map = get_object_or_404(Map,pk=mapid) 
    layers = MapLayer.objects.filter(map=map.id) 
    return render_to_response("maps/mapinfo.html", RequestContext(request, {
        'config': json.dumps(DEFAULT_MAP_CONFIG), 
        'bg': json.dumps(settings.MAP_BASELAYERS),
        'map': map, 
        'layers': layers
    }))

def map_controller(request, mapid):
    '''
    main view for map resources, dispatches to correct 
    view based on method and query args. 
    '''
    if 'remove' in request.GET: 
        return deletemap(request, mapid)
    else:
        return mapdetail(request, mapid)

def view(request, mapid):
    """  
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config), 'bg': json.dumps(settings.MAP_BASELAYERS),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL
    }))

def embed(request, mapid=None):
    if mapid is None:
        config = DEFAULT_MAP_CONFIG
    else:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
    return render_to_response('maps/embed.html', RequestContext(request, {
        'config': json.dumps(config),
        'bg': json.dumps(settings.MAP_BASELAYERS)
    }))


def data(request):
    return render_to_response('data.html', RequestContext(request, {
        'GEOSERVER_BASE_URL':settings.GEOSERVER_BASE_URL
    }))

def build_map_config(map):
    layers = map.layer_set.all()
    servers = list(set(l.ows_url for l in layers))
    server_mapping = {}

    for i in range(len(servers)):
        server_mapping[servers[i]] = str(i)

    config = {
        'id': map.id,
        'about': {
            'title':    escape(map.title),
            'contact':  escape(map.contact),
            'abstract': escape(map.abstract),
            'endorsed': map.endorsed
        },
        'map': { 
            'layers': [],
            'center': [map.center_lon, map.center_lat],
            'zoom': map.zoom
        }
    }

    config['wms'] = dict(zip(server_mapping.values(), server_mapping.keys()))

    for l in layers:
        config['map']['layers'].append({
            'name': l.name,
            'wms': server_mapping[l.ows_url],
            'group': l.group
        })

    return config

def view_js(request, mapid):
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return HttpResponse(json.dumps(config), mimetype="application/javascript")

class LayerDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)

def _describe_layer(request, layer):
    if request.user.is_authenticated():
        if request.method == "GET":
            resource = layer.resource
            form = LayerDescriptionForm({
                "title": resource.title,
                "abstract": resource.abstract,
                "keywords": ", ".join(resource.keywords)
            })
        elif request.method == "POST":
            form = LayerDescriptionForm(request.POST)
            if form.is_valid():
                f = form.cleaned_data
                layer.title = f['title']
                layer.abstract = f['abstract']
                layer.keywords = f['keywords'].split(", ")
                layer.save()
                return HttpResponseRedirect("/data/" + layer.typename)
        return render_to_response("maps/layer_describe.html", RequestContext(request, {
            "layer": layer,
            "form": form
        }))
    else: 
        return HttpResponse("Not allowed", status=403)

def _removeLayer(request,layer):
    if request.user.is_authenticated():
        if (request.method == 'GET'):
            return render_to_response('maps/layer_remove.html',RequestContext(request, {
                "layer": layer
            }))
        if (request.method == 'POST'):
            layer.delete()
            return HttpResponseRedirect(reverse("geonode.views.static", args=('data', )))
        else:
            return HttpResponse("Not allowed",status=403) 
    else:  
        return HttpResponse("Not allowed",status=403)

def _updateLayer(request,layer):		
	return HttpResponse("replace layer")
			
def layerController(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if (request.META['QUERY_STRING'] == "describe"):
        return _describe_layer(request,layer)
    if (request.META['QUERY_STRING'] == "remove"):
        return _removeLayer(request,layer)
    if (request.META['QUERY_STRING'] == "replace"):
        return _updateLayer(request,layer)
    else: 
        return render_to_response('maps/layer.html', RequestContext(request, {
            "layer": layer,
            "background": settings.MAP_BASELAYERS,
            "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
	    }))

@login_required
def upload_layer(request):
    if request.method == 'GET':
        return render_to_response('maps/layer_upload.html',
                                  RequestContext(request, {}))
    elif request.method == 'POST':
        layer, errors = _handle_layer_upload(request)

        if errors: 
            return render_to_response('maps/layer_upload.html',
                                      RequestContext(request, {'errors': errors}))
        else: 
            return HttpResponseRedirect('%s?describe' % reverse('geonode.maps.views.layerController', 
                                                                 args=(layer.typename,)))


def _handle_layer_upload(request, name=None):

    base_file = request.FILES.get('base_file');
    if not base_file:
        return [_("You must specify a layer data file to upload.")]
    
    if name is None:
        # XXX Give feedback instead of just replacing name
        # XXX We need a better way to remove xml-unsafe characters
        name = base_file.name[0:-4]
        name = name.replace(" ", "_")
        proposed_name = name
        count = 1
        while Layer.objects.filter(name=proposed_name).count() > 0:
            proposed_name = "%s_%d" % (name, count)
            count = count + 1
        name = proposed_name

    errors = []
    
    if not name:
        return[_("Unable to determine layer name.")]

    # shapefile upload
    elif base_file.name.lower().endswith('.shp'):
        dbf_file = request.FILES.get('dbf_file')
        shx_file = request.FILES.get('shx_file')
        prj_file = request.FILES.get('prj_file')
        
        if not dbf_file: 
            errors.append(_("You must specify a .dbf file when uploading a shapefile."))
        if not shx_file: 
            errors.append(_("You must specify a .shx file when uploading a shapefile."))

        if errors:
            return None, errors
        
        # ... bundle the files together and send them along
        cfg = {
            'shp': base_file,
            'dbf': dbf_file,
            'shx': shx_file
        }
        if prj_file:
            cfg['prj'] = prj_file

        
        try:
            cat = Layer.objects.gs_catalog
            cat.create_featurestore(name, cfg)
        except geoserver.catalog.UploadError:
            errors.append(_("An error occurred while loading the data."))
        except geoserver.catalog.ConflictingDataError:
            errors.append(_("There is already a layer with the given name."))
        
    # any other type of upload
    else:
        try:
            # ... we attempt to let geoserver figure it out ? 
            cat = Layer.objects.gs_catalog
            cat.create_coveragestore(name, base_file)
        except geoserver.catalog.UploadError:
            errors.append(_("An error occurred while loading the data."))
        except geoserver.catalog.ConflictingDataError:
            errors.append(_("There is already a layer with the given name."))

    if len(errors) == 0: 
        try:
            info = cat.get_resource(name)
            typename = info.store.workspace.name + ':' + info.name
            layer = Layer.objects.create(name=info.name, 
                                         store=info.store.name,
                                         storeType=info.store.resource_type,
                                         typename=typename,
                                         workspace=info.store.workspace.name)
            layer.save()
            return layer, errors
        except:
            errors.append(_("An error occurred creating the layer."))

    return None, errors
