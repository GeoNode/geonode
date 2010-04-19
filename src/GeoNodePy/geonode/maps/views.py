from geonode.maps.models import Map, Layer, MapLayer
from geonode import geonetwork
import geoserver
from geoserver.resource import FeatureType, Coverage
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
import math
from django.conf import settings
import httplib2 
from urllib import urlencode
import uuid

_user, _password = settings.GEOSERVER_CREDENTIALS

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
            
            bbox = layer.resource.latlon_bbox
            
            config = DEFAULT_MAP_CONFIG
            config['map']['layers'] = [{'name': "%s:%s" % (layer.workspace,layer.name), 
                                            'wms' : 'capra'}]
            config['map']['center'] = ((float(bbox[0]) + float(bbox[1])) / 2, (float(bbox[2]) + float(bbox[3])) / 2)

            width_zoom = math.log(360 / (float(bbox[1]) - float(bbox[0])),2)
            height_zoom = math.log(360 / (float(bbox[1]) - float(bbox[0])),2)
            config['map']['zoom'] = math.floor(min(width_zoom, height_zoom))                                  
        else:
            config = DEFAULT_MAP_CONFIG
    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config), 
        'bg': json.dumps(settings.MAP_BASELAYERS),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL
    }))

h = httplib2.Http()
h.add_credentials(_user,_password)

@login_required
def map_download(request, mapid):
    """ 
    Complicated request
    XXX To do, remove layer status once progress id done 
    This should be fix because 
    """ 
    mapObject = get_object_or_404(Map,pk=mapid)
    map_status = dict()
    if request.method == 'POST': 
        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL
        resp, content = h.request(url,'POST',body=mapObject.json)
        if resp.status != 404 or 400: 
            request.session["map_status"] = eval(content)
            map_status = eval(content)
        else: 
            pass # XXX fix
    if request.method == 'GET':
        if "map_status" in request.session and type(request.session["map_status"]) == dict:
            msg = "You already started downloading a map"
        else: 
            msg = "You should download a map" 
    return render_to_response('maps/download.html', RequestContext(request, {
         "map_status" : map_status,
         "map" : mapObject
    }))

def check_download(request):
    try:
        layer = request.session["map_status"] 
        if type(layer) == dict:
            url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL,layer["id"])
            resp,content = h.request(url,'GET')
            status= resp.status
            if resp.status == 400:
                import pdb; pdb.set_trace()
                return HttpResponse(content="Something went wrong",status=status)
        else: 
            content = "Something Went wrong" 
            status  = 400 
    except ValueError:
        print "No layer_status in your session"
    return HttpResponse(content=content,status=status)


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
                layer.keywords = [kw for kw in f['keywords'].split(", ") if kw != '']
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
			
def layerController(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if (request.META['QUERY_STRING'] == "describe"):
        return _describe_layer(request,layer)
    if (request.META['QUERY_STRING'] == "remove"):
        return _removeLayer(request,layer)
    if (request.META['QUERY_STRING'] == "update"):
        return _updateLayer(request,layer)
    else: 
        metadata = layer.metadata_csw()

        return render_to_response('maps/layer.html', RequestContext(request, {
            "layer": layer,
            "metadata": metadata,
            "background": settings.MAP_BASELAYERS,
            "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
	    }))


GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

@login_required
def upload_layer(request):
    if request.method == 'GET':
        return render_to_response('maps/layer_upload.html',
                                  RequestContext(request, {}))
    elif request.method == 'POST':
        try:
            layer, errors = _handle_layer_upload(request)
        except:
            errors = [GENERIC_UPLOAD_ERROR] 
        
        result = {}
        if len(errors) > 0:
            result['success'] = False
            result['errors'] = errors
        else:
            result['success'] = True
            result['redirect_to'] = reverse('geonode.maps.views.layerController', args=(layer.typename,)) + "?describe"

        result = json.dumps(result)
        return render_to_response('json_html.html',
                                  RequestContext(request, {'json': result}))


@login_required
def _updateLayer(request, layer):
    if request.method == 'GET':
        cat = Layer.objects.gs_catalog
        info = cat.get_resource(layer.name)
        is_featuretype = info.resource_type == FeatureType.resource_type
        
        return render_to_response('maps/layer_replace.html',
                                  RequestContext(request, {'layer': layer,
                                                           'is_featuretype': is_featuretype}))
    elif request.method == 'POST':
        try:
            layer, errors = _handle_layer_upload(request, layer=layer)
        except:
            errors = [GENERIC_UPLOAD_ERROR] 

        result = {}
        if len(errors) > 0:
            result['success'] = False
            result['errors'] = errors
        else:
            result['success'] = True
            result['redirect_to'] = reverse('geonode.maps.views.layerController', args=(layer.typename,)) + "?describe"

    result = json.dumps(result)
    return render_to_response('json_html.html',
                              RequestContext(request, {'json': result}))

def _handle_layer_upload(request, layer=None):
    """
    handle upload of layer data. if specified, the layer given is 
    overwritten, otherwise a new layer is created.
    """

    base_file = request.FILES.get('base_file');
    if not base_file:
        return [_("You must specify a layer data file to upload.")]
    
    if layer is None:
        overwrite = False
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
    else:
        overwrite = True
        name = layer.name

    errors = []
    cat = Layer.objects.gs_catalog
    
    if not name:
        return[_("Unable to determine layer name.")]

    # shapefile upload
    elif base_file.name.lower().endswith('.shp'):
        # check that we are uploading the same resource 
        # type as the existing resource.
        if layer is not None:
            info = cat.get_resource(name)
            if info.resource_type != FeatureType.resource_type:
                return [_("This resource may only be replaced with raster data.")]
        
        create_store = cat.create_featurestore
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


    # any other type of upload
    else:
        if layer is not None:
            info = cat.get_resource(name)
            if info.resource_type != Coverage.resource_type:
                return [_("This resource may only be replaced with shapefile data.")]

        # ... we attempt to let geoserver figure it out, guessing it is coverage 
        create_store = cat.create_coveragestore
        cfg = base_file

    try:
        create_store(name, cfg, overwrite=overwrite)
    except geoserver.catalog.UploadError:
        errors.append(_("An error occurred while loading the data."))
    except geoserver.catalog.ConflictingDataError:
        errors.append(_("There is already a layer with the given name."))


    # if we successfully created the store in geoserver...
    if len(errors) == 0 and layer is None:
        gs_resource = None
        csw_record = None
        layer = None
        try:
            gs_resource = cat.get_resource(name)
            if gs_resource.latlon_bbox is None:
                # If GeoServer couldn't figure out the projection, we just
                # assume it's lat/lon to avoid a bad GeoServer configuration

                gs_resource.latlon_bbox = gs_resource.resource.native_bbox
                gs_resource.projection = "EPSG:4326"
                cat.save(gs_resource)

            typename = gs_resource.store.workspace.name + ':' + gs_resource.name
            
            # if we created a new store, create a new layer
            layer = Layer.objects.create(name=gs_resource.name, 
                                         store=gs_resource.store.name,
                                         storeType=gs_resource.store.resource_type,
                                         typename=typename,
                                         workspace=gs_resource.store.workspace.name,
                                         uuid=str(uuid.uuid4()))
            gn = geonetwork.Catalog(settings.GEONETWORK_BASE_URL, settings.GEONETWORK_CREDENTIALS[0], settings.GEONETWORK_CREDENTIALS[1])
            gn.login()
            md_link = gn.create_from_layer(layer)
            gn.logout()
            layer.metadata_links = [("text/xml", "ISO19115", md_link)]
            layer.save()
        except:
            # Something went wrong, let's try and back out any changes
            if gs_resource is not None:
                # no explicit link from the resource to the layer, bah
                layer = cat.get_layer(gs_resource.name) 
                store = gs_resource.store
                try:
                    cat.delete(layer)
                except:
                    pass

                try: 
                    cat.delete(gs_resource)
                except:
                    pass

                try: 
                    cat.delete(store)
                except:
                    pass
            if csw_record is not None:
                try:
                    gn.delete(csw_record)
                except:
                    pass
            if layer is not None:
                layer.delete()
            layer = None
            errors.append(GENERIC_UPLOAD_ERROR)

    return layer, errors
