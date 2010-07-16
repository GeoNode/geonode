from geonode.maps.models import Map, Layer, MapLayer, get_csw
from geonode.maps.forms import ContactForm, MetadataForm
from geonode import geonetwork
import geoserver
from geoserver.resource import FeatureType, Coverage
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.gis import gdal
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
import json
import math
import httplib2 
from owslib.csw import CswRecord, namespaces
from owslib.util import nspath
import re
from urllib import urlencode
from urlparse import urlparse
import uuid
from django.views.decorators.csrf import csrf_exempt

_user, _password = settings.GEOSERVER_CREDENTIALS

DEFAULT_TITLE = "GeoNode Default Map"
DEFAULT_ABSTRACT = "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the Save Map button above to contribute your map to the GeoNode community."
DEFAULT_CONTACT = "For more information, contact OpenGeo at http://opengeo.org/"
DEFAULT_MAP_CONFIG = Map(
    title=DEFAULT_TITLE, 
    abstract=DEFAULT_ABSTRACT,
    contact=DEFAULT_CONTACT,
    projection="EPSG:900913",
    max_resolution=156543.0339,
    units="m",
    center_x=-9428760.8688778,
    center_y=1436891.8972581,
    extent_max_x=20037508.34,
    extent_max_y=20037508.34,
    extent_min_x=-20037508.34,
    extent_min_y=-20037508.34,
    zoom=7
).viewer_json

def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID='+srid+';POLYGON(('+x0+' '+y0+','+x0+' '+y1+','+x1+' '+y1+','+x1+' '+y0+','+x0+' '+y0+'))'

def maps(request, mapid=None):
    if request.method == 'GET' and mapid is None:
        map_configs = [{"id": map.pk, "config": map.viewer_json} for map in Map.objects.all()]
        return HttpResponse(json.dumps({"maps": map_configs}), mimetype="application/json")
    elif request.method == 'GET' and mapid is not None:
        map = Map.objects.get(pk=mapid)
        config = map.viewer_json
        return HttpResponse(json.dumps(config))
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse(
                'You must be logged in to save new maps',
                mimetype="text/plain",
                status=401
            )
        try: 
            map = Map(owner=request.user)
            map.update_from_viewer(request.raw_post_data)
            response = HttpResponse('', status=201)
            response['Location'] = map.id
            return response
        except Exception, e:
            return HttpResponse(
                "The server could not understand your request.",
                status=400, 
                mimetype="text/plain"
            )

def mapJSON(request, mapid):
    if request.method == 'GET':
        map = get_object_or_404(Map,pk=mapid) 
    	return HttpResponse(json.dumps(map.viewer_json))
    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return HttpResponse(
                _("You must be logged in to save this map"),
                status=401,
                mimetype="text/plain"
            )
        map = get_object_or_404(Map, pk=mapid)
        try:
            map.update_from_viewer(request.raw_post_data)
            return HttpResponse(
                "Map successfully updated.", 
                mimetype="text/plain",
                status=204
            )
        except Exception, e:
            return HttpResponse(
                "The server could not understand the request.",
                mimetype="text/plain",
                status=400
            )

@csrf_exempt
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
        config = map.viewer_json
        del config['id']
    else:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        else:
            return HttpResponse(status=405)
        
        if 'layer' in params:
            bbox = None
            layers = []
            config = DEFAULT_MAP_CONFIG
            for layer_name in params.getlist('layer'):
                try:
                    layer = Layer.objects.get(typename=layer_name)
                except ObjectDoesNotExist:
                    # bad layer, skip 
                    continue

                layer_bbox = layer.resource.latlon_bbox
                if bbox is None:
                    bbox = list(layer_bbox)
                else:
                    bbox[0] = min(bbox[0], layer_bbox[0])
                    bbox[1] = max(bbox[1], layer_bbox[1])
                    bbox[2] = min(bbox[2], layer_bbox[2])
                    bbox[3] = max(bbox[3], layer_bbox[3])
                
                layers.append({'name': layer.typename,
                               'wms' : 'capra'})
                                   
            if len(layers) > 0:
                config['map']['layers'] = layers

            if bbox is not None:
                config['map']['center'] = ((float(bbox[0]) + float(bbox[1])) / 2, (float(bbox[2]) + float(bbox[3])) / 2)

                width_zoom = math.log(360 / (float(bbox[1]) - float(bbox[0])),2)
                height_zoom = math.log(360 / (float(bbox[1]) - float(bbox[0])),2)
                config['map']['zoom'] = math.floor(min(width_zoom, height_zoom))
        else:
            config = DEFAULT_MAP_CONFIG
    config["backgroundLayers"] = settings.MAP_BASELAYERS
    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config), 
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
         "map" : mapObject,
         "geoserver" : settings.GEOSERVER_BASE_URL,
         "site" : settings.SITEURL
    }))
    

def check_download(request):
    """
    this is an endpoint for monitoring map downloads
    """
    try:
        layer = request.session["map_status"] 
        if type(layer) == dict:
            url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL,layer["id"])
            resp,content = h.request(url,'GET')
            status= resp.status
            if resp.status == 400:
                return HttpResponse(content="Something went wrong",status=status)
        else: 
            content = "Something Went wrong" 
            status  = 400 
    except ValueError:
        print "No layer_status in your session"
    return HttpResponse(content=content,status=status)


@csrf_exempt
def batch_layer_download(request):
    """
    batch download a set of layers
    
    POST - begin download
    GET?id=<download_id> monitor status
    """

    # currently this just piggy-backs on the map download backend 
    # by specifying an ad hoc map that contains all layers requested
    # for download. assumes all layers are hosted locally.
    # status monitoring is handled slightly differently.
    
    if request.method == 'POST':

        def layer_son(layer):
            return {
                "name" : layer.typename, 
                "service" : layer.service_type, 
                "metadataURL" : "http://localhost/fake/url/{name}".format(name=layer.name),
                "serviceURL" : "http://localhost/%s" %layer.name,
            } 
            
        
        fake_map = { 
            "map" : { 
                "title" : "Batch Download", 
                "abstract" : "Collection of layers selected from GeoNode", 
                "author" : "The GeoNode Team",
            }, 
            "layers" : []
        }
        

        for layer_id in request.POST.getlist('layer'):
            try:
                layer = Layer.objects.get(typename=layer_id)
                
                if layer is not None:
                    fake_map['layers'].append(layer_son(layer))
            except ObjectDoesNotExist:
                # bad layer, skip 
                continue

        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL
        resp, content = h.request(url,'POST',body=json.dumps(fake_map))
        return HttpResponse(content, status=resp.status)

    
    if request.method == 'GET':
        # essentially, this just proxies back to geoserver
        download_id = request.GET.get('id', None)
        if download_id is None:
            return HttpResponse(status=404)

        url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL, download_id)
        resp,content = h.request(url,'GET')
        return HttpResponse(content, status=resp.status)


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
        return HttpResponseRedirect(reverse('geonode.views.community'))

def mapdetail(request,mapid): 
    '''
    The view that show details of each map
    '''
    map = get_object_or_404(Map,pk=mapid) 
    config = map.viewer_json
    config["backgroundLayers"] = settings.MAP_BASELAYERS
    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map.id) 
    return render_to_response("maps/mapinfo.html", RequestContext(request, {
        'config': config, 
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
    config = map.viewer_json
    config["backgroundLayers"] = settings.MAP_BASELAYERS
    return render_to_response('maps/view.html', RequestContext(request, {
        'config': json.dumps(config),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL
    }))

def embed(request, mapid=None):
    if mapid is None:
        config = DEFAULT_MAP_CONFIG
    else:
        map = Map.objects.get(pk=mapid)
        config = map.viewer_json
    config["backgroundLayers"] = settings.MAP_BASELAYERS
    return render_to_response('maps/embed.html', RequestContext(request, {
        'config': json.dumps(config)
    }))


def data(request):
    return render_to_response('data.html', RequestContext(request, {
        'GEOSERVER_BASE_URL':settings.GEOSERVER_BASE_URL
    }))

def view_js(request, mapid):
    map = Map.objects.get(pk=mapid)
    config = map.viewer_json
    return HttpResponse(json.dumps(config), mimetype="application/javascript")

def fixdate(str):
    return " ".join(str.split("T"))

class LayerDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)

@csrf_exempt
@login_required
def _describe_layer(request, layer):
    if request.user.is_authenticated():
        if request.method == "GET":
            resource = layer.resource
            meta = layer.metadata_csw()
            if meta is None:
                # It probably means GeoNetwork isn't running or the layer is not there.
                # Don't try to populate the information.
                md_form = MetadataForm()
                poc_form = ContactForm(prefix="poc")
                metadata_provider_form = ContactForm(prefix="metadata")
                return render_to_response("maps/layer_describe.html", RequestContext(request, {
                        "layer": layer,
                        "md_form": md_form,
                        "poc_form": poc_form,
                        "metadata_provider_form": metadata_provider_form
                    }))
                
                
            bbox = meta.identification.bbox
            bbox_ewkt = bbox_to_wkt(bbox.minx, bbox.maxx, bbox.miny, bbox.maxy)
            keywords = [word for word in meta.identification.keywords['list'] if isinstance(word,str)]
            if meta.referencesystem.code == 'WGS 1984':
                srs = '4326'
            else:
                # How do we translate the string that GeoNetwork provides to EPSG codes?
                # Let's fail loudly if that happens.
                assert False
            provider = get_csw().provider.contact    
            md_form = MetadataForm({
                "title": meta.identification.title, 
                "abstract": meta.identification.abstract,
                "date": fixdate(meta.datestamp),
                "date_type": "Creation",
                "constraints_use": "copyright",
                "maintenance_frequency": "annually",
                "geographic_bounding_box": bbox_ewkt,
                "language": meta.language,
                "keywords": ", ".join([word for word in meta.identification.keywords['list'] if isinstance(word,str)] )
            })
            poc_form = ContactForm(initial={
               "name": meta.contact.name,
               "organization": meta.contact.organization,
               "position": meta.contact.position,
               "voice": meta.contact.phone,
               "facsimile": meta.contact.fax,
               "country": meta.contact.country,
               "city": meta.contact.city,
               "role": meta.contact.role,
               "address": meta.contact.address,
            }, prefix="poc")
            
            metadata_provider_form = ContactForm(initial={
               "name": provider.name,
               "organization": provider.organization,
               "position": provider.position,
               "voice": provider.phone,
               "facsimile": provider.fax,
               "country": provider.country,
               "city": provider.city,
               "role": provider.role,
               "address": provider.address,
            }, prefix="metadata")
        elif request.method == "POST":
            md_form = MetadataForm(request.POST)
            poc_form = ContactForm(request.POST, prefix="poc")
            metadata_provider_form = ContactForm(request.POST, prefix="metadata")
            if md_form.is_valid():
                f = md_form.cleaned_data
                layer.title = f['title']
                layer.abstract = f['abstract']
                layer.keywords = [kw for kw in f['keywords'].split(", ") if kw != '']
                layer.save()
                return HttpResponseRedirect("/data/" + layer.typename)
        return render_to_response("maps/layer_describe.html", RequestContext(request, {
            "layer": layer,
            "md_form": md_form,
            "poc_form": poc_form,
            "metadata_provider_form": metadata_provider_form
        }))
    else: 
        return HttpResponse("Not allowed", status=403)

@csrf_exempt
def _removeLayer(request,layer):
    if request.user.is_authenticated():
        if (request.method == 'GET'):
            return render_to_response('maps/layer_remove.html',RequestContext(request, {
                "layer": layer
            }))
        if (request.method == 'POST'):
            layer.delete()
            return HttpResponseRedirect(reverse("data"))
        else:
            return HttpResponse("Not allowed",status=403) 
    else:  
        return HttpResponse("Not allowed",status=403)

@csrf_exempt
def _changeLayerDefaultStyle(request,layer):
    if request.user.is_authenticated():
        if (request.method == 'POST'):
            style_name = request.POST.get('defaultStyle')

            # would be nice to implement
            # better handling of default style switching
            # in layer model or deeper (gsconfig.py, REST API)

            old_default = layer.default_style
            if old_default.name == style_name:
                return HttpResponse("Default style for %s remains %s" % (layer.name, style_name), status=200)

            # This code assumes without checking
            # that the new default style name is included
            # in the list of possible styles.

            new_style = (style for style in layer.styles if style.name == style_name).next()

            layer.default_style = new_style
            layer.styles = [s for s in layer.styles if s.name != style_name] + [old_default]
            layer.save()
            return HttpResponse("Default style for %s changed to %s" % (layer.name, style_name),status=200)
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
    if (request.META['QUERY_STRING'] == "style"):
        return _changeLayerDefaultStyle(request,layer)
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
@csrf_exempt
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
@csrf_exempt
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

                gs_resource.latlon_bbox = gs_resource.native_bbox
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
            layer.metadata_links = [("text/xml", "TC211", md_link)]
            layer.save()
        except:
            # Something went wrong, let's try and back out any changes
            if gs_resource is not None:
                # no explicit link from the resource to the layer, bah
                gs_layer = cat.get_layer(gs_resource.name) 
                store = gs_resource.store
                try:
                    cat.delete(gs_layer)
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

def _split_query(query):
    """
    split and strip keywords, preserve space 
    separated quoted blocks.
    """

    qq = query.split(' ')
    keywords = []
    accum = None
    for kw in qq: 
        if accum is None: 
            if kw.startswith('"'):
                accum = kw[1:]
            elif kw: 
                keywords.append(kw)
        else:
            accum += ' ' + kw
            if kw.endswith('"'):
                keywords.append(accum[0:-1])
                accum = None
    if accum is not None:
        keywords.append(accum)
    return [kw.strip() for kw in keywords if kw.strip()]



DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
@csrf_exempt
def metadata_search(request):
    """
    handles a basic search for data using the 
    GeoNetwork catalog.

    the search accepts: 
    q - general query for keywords across all fields
    start - skip to this point in the results
    limit - max records to return

    for ajax requests, the search returns a json structure 
    like this: 
    
    {
    'total': <total result count>,
    'next': <url for next batch if exists>,
    'prev': <url for previous batch if exists>,
    'query_info': {
        'start': <integer indicating where this batch starts>,
        'limit': <integer indicating the batch size used>,
        'q': <keywords used to query>,
    },
    'rows': [
      {
        'name': <typename>,
        'abstract': '...',
        'keywords': ['foo', ...],
        'detail' = <link to geonode detail page>,
        'attribution': {
            'title': <language neutral attribution>,
            'href': <url>
        },
        'download_links': [
            ['pdf', 'PDF', <url>],
            ['kml', 'KML', <url>],
            [<format>, <name>, <url>]
            ...
        ],
        'metadata_links': [
           ['text/xml', 'TC211', <url>],
           [<mime>, <name>, <url>],
           ...
        ]
      },
      ...
    ]}
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
    except:
        start = 0
    try:
        limit = min(int(params.get('limit', DEFAULT_SEARCH_BATCH_SIZE)),
                    MAX_SEARCH_BATCH_SIZE)
    except: 
        limit = DEFAULT_SEARCH_BATCH_SIZE

    advanced = {}
    bbox = params.get('bbox', None)
    if bbox:
        try:
            bbox = [float(x) for x in bbox.split(',')]
            if len(bbox) == 4:
                advanced['bbox'] =  bbox
        except:
            # ignore...
            pass

    result = _metadata_search(query, start, limit, **advanced)
    result['success'] = True
    return HttpResponse(json.dumps(result), mimetype="application/json")

def _metadata_search(query, start, limit, **kw):
    
    csw = get_csw()

    keywords = _split_query(query)
    
    csw.getrecords(keywords=keywords, startposition=start+1, maxrecords=limit, bbox=kw.get('bbox', None))
    
    
    # build results 
    # XXX this goes directly to the result xml doc to obtain 
    # correct ordering and a fuller view of the result record
    # than owslib currently parses.  This could be improved by
    # improving owslib.
    results = [_build_search_result(doc) for doc in 
               csw._records.findall('//'+nspath('Record', namespaces['csw']))]

    result = {'rows': results, 
              'total': csw.results['matches']}

    result['query_info'] = {
        'start': start,
        'limit': limit,
        'q': query
    }
    if start > 0: 
        prev = max(start - limit, 0)
        params = urlencode({'q': query, 'start': prev, 'limit': limit})
        result['prev'] = reverse('geonode.maps.views.metadata_search') + '?' + params

    next = csw.results.get('nextrecord', 0) 
    if next > 0:
        params = urlencode({'q': query, 'start': next - 1, 'limit': limit})
        result['next'] = reverse('geonode.maps.views.metadata_search') + '?' + params
    
    return result

def search_result_detail(request):
    uuid = request.GET.get("uuid")
    csw = get_csw()
    csw.getrecordbyid([uuid])
    doc = csw._records.find(nspath('Record', namespaces['csw']))
    rec = _build_search_result(doc)
    return render_to_response('maps/search_result_snippet.html', RequestContext(request, {
        'rec': rec
    }))

def _build_search_result(doc):
    """
    accepts a node representing a csw result 
    record and builds a POD structure representing 
    the search result.
    """

    # Let owslib do some parsing for us...
    rec = CswRecord(doc)
    result = {}
    result['title'] = rec.title
    result['uuid'] = rec.identifier
    result['abstract'] = rec.abstract
    result['keywords'] = [x for x in rec.subjects if x]
    result['detail'] = rec.uri or ''

    # XXX needs indexing ? how
    result['attribution'] = {'title': '', 'href': ''}

    # XXX !_! pull out geonode 'typename' if there is one
    # index this directly... 
    if rec.uri:
        try:
            result['name'] = urlparse(rec.uri).path.split('/')[-1]
        except: 
            pass
    # fallback: use geonetwork uuid
    if not result.get('name', ''):
        result['name'] = rec.identifier

    # Take BBOX from GeoNetwork Result...
    # XXX this assumes all our bboxes are in this 
    # improperly specified SRS.
    if rec.bbox is not None and rec.bbox.crs == 'urn:ogc:def:crs:::WGS 1984':
        # slight workaround for ticket 530
        result['bbox'] = {
            'minx': min(rec.bbox.minx, rec.bbox.maxx),
            'maxx': max(rec.bbox.minx, rec.bbox.maxx),
            'miny': min(rec.bbox.miny, rec.bbox.maxy),
            'maxy': max(rec.bbox.miny, rec.bbox.maxy)
        }
    
    # XXX these could be exposed in owslib record...
    # locate all download links
    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")
    result['download_links'] = []
    for link_el in doc.findall(nspath('URI', namespaces['dc'])):
        if link_el.get('protocol', '') == 'WWW:DOWNLOAD-1.0-http--download':
            try:
                extension = link_el.get('name', '').split('.')[-1]
                format = format_re.match(link_el.get('description')).groups()[0]
                if 'Format' in format:
                    import pdb; pdb.set_trace()
                href = link_el.text
                result['download_links'].append((extension, format, href))
            except: 
                pass

    # construct the link to the geonetwork metadata record (not self-indexed)
    md_link = settings.GEONETWORK_BASE_URL + "srv/en/csw?" + urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "OutputSchema": "http://www.isotc211.org/2005/gmd",
            "ElementSetName": "full",
            "id": rec.identifier
        })
    result['metadata_links'] = [("text/xml", "TC211", md_link)]

    return result

def browse_data(request):
    return render_to_response('data.html', RequestContext(request, {}))

@csrf_exempt    
def search_page(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    return render_to_response('search.html', RequestContext(request, {
        'init_search': json.dumps(params or {}),
        'background': json.dumps(settings.MAP_BASELAYERS[settings.SEARCH_WIDGET_BASELAYER_INDEX]),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
         "site" : settings.SITEURL
    }))
