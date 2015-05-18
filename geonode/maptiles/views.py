from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse

from geonode.services.models import Service
from geonode.layers.models import Layer
from geonode.utils import resolve_object, llbbox_to_mercator

from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import default_map_config
from geonode.security.views import _perms_info_json
from geonode.cephgeo.models import CephDataObject, DataClassification
from geonode.cephgeo.cart_utils import *
from geonode.documents.models import get_related_documents

import geonode.settings as settings

from pprint import pprint

import logging

_PERMISSION_VIEW = _("You are not permitted to view this layer")
_PERMISSION_GENERIC = _('You do not have permissions for this layer.')
# Create your views here.

logger = logging.getLogger("geonode")

def _resolve_layer(request, typename, permission='base.view_resourcebase',
                   msg=_PERMISSION_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = typename.split(":", 1)
    service = Service.objects.filter(name=service_typename[0])

    if service.count() > 0:
        return resolve_object(request,
                              Layer,
                              {'service': service[0],
                               'typename': service_typename[1] if service[0].method != "C" else typename},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)
    else:
        return resolve_object(request,
                              Layer,
                              {'typename': typename,
                               'service': None},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)
@login_required
def tiled_view(request, overlay=settings.TILED_SHAPEFILE, template="maptiles/maptiles_map.html"):
    if request.method == "POST":
        pprint(request.POST)
    layer = _resolve_layer(request, overlay, "base.view_resourcebase", _PERMISSION_VIEW )
    config = layer.attribute_config()
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    srid = layer.srid

    # Transform WGS84 to Mercator.
    config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])

    config["title"] = layer.title
    config["queryable"] = True

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    #if request.user != layer.owner and not request.user.is_superuser:
    #    Layer.objects.filter(
    #        id=layer.id).update(popular_count=F('popular_count') + 1)
    
    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "data_classes": DataClassification.labels.values(),
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
    }

    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
        
    context_dict["layer"]  = settings.TILED_SHAPEFILE

    #if settings.SOCIAL_ORIGINS:
    #    context_dict["social_links"] = build_social_links(request, layer)
    #print context_dict
    
    return render_to_response(template, RequestContext(request, context_dict))

@login_required
def tiled_view2(request, overlay=settings.TILED_SHAPEFILE_TEST, template="maptiles/maptiles_map.html"):
    layer = _resolve_layer(
        request,
        overlay,
        'base.view_resourcebase',
        _PERMISSION_VIEW)
    config = layer.attribute_config()
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    srid = layer.srid

    # Transform WGS84 to Mercator.
    config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])

    config["title"] = layer.title
    config["queryable"] = True

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "data_classes": DataClassification.labels.values(),
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
    }
    
    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * ([maplayer])))
        
    context_dict["layer"]  = settings.TILED_SHAPEFILE_TEST

    return render_to_response(template, RequestContext(request, context_dict))

def process_georefs(request):
    if request.method == "POST":
        try:
            #pprint(request.POST)
            georef_area = request.POST['georef_area']
            georef_list = filter(None, georef_area.split(","))
            #spprint(georef_list)
            #TODO: find all files with these georefs and add them to cart
            count = 0
            empty_georefs = 0
            duplicates = []
            
            for georef in georef_list:      # Process each georef in list
                objects = CephDataObject.objects.filter(name__startswith=georef)
                count += len(objects)
                if len(objects) > 0:
                    for ceph_obj in objects:    # Add each Ceph object to cart
                        try:
                            add_to_cart_unique(request, ceph_obj.id)
                        except DuplicateCartItemException:  # List each duplicate object
                            duplicates.append(ceph_obj.name)
                else:
                    empty_georefs += 1
            
            #if len(duplicates) > 0:         # Warn on duplicates
            #    messages.warning(request, "WARNING: The following items are already in the cart and have not been added: \n{0}".format(str(duplicates)))
            
            if empty_georefs > 0:
                messages.error(request, "ERROR: [{0}] out of selected [{1}] georef tiles have no data! A total of [{2}] objects have been added to cart. \n".format(empty_georefs,len(georef_list),(count - len(duplicates))))
            elif len(duplicates)>0: # Inform user of the number of processed georefs and objects
                messages.info(request, "Processed [{0}] georefs tiles. [{2}] duplicate objects found in cart have been skipped. A total of [{1}] objects have been added to cart. ".format(len(georef_list),(count - len(duplicates)),len(duplicates)))
            else: # Inform user of the number of processed georefs and objects
                messages.info(request, "Processed [{0}] georefs tiles. A total of [{1}] objects have been added to cart.".format(len(georef_list),(count - len(duplicates))))
            
            return redirect('geonode.cephgeo.views.get_cart')
            
        except ValidationError:             # Redirect and inform if an invalid georef is encountered
            messages.error(request, "Invalid georefs list")
            return HttpResponseRedirect('/maptiles/')
            #return redirect('geonode.maptiles.views.tiled_view')
    
    else:   # Must process HTTP POST method from form
        raise Exception("HTTP method must be POST!")

@login_required
def georefs_validation(request):
    if request.method != 'POST':
        return HttpResponse(
            content='no data received from HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    else:
        georefs = request.POST["georefs"]
        georefs_list = filter(None, georefs.split(","))
        
        total_size = 0
        for georef in georefs_list:
            objects = CephDataObject.objects(name__startswith=georef)
            for o in objects:
                total_size += o.size_in_bytes
        
        if size > settings.SELECTION_LIMIT:            
            return HttpResponse(
                content={ "response": False, "total_size": total_size },
                status=200,
                mimetype='text/plain'
            )
        else:
            return HttpResponse(
                content={ "response": True, "total_size": total_size },
                status=200,
                mimetype='text/plain'
            )
        
