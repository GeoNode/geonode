from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse

from geonode.services.models import Service
from geonode.layers.models import Layer
from geonode.layers.utils import is_vector, get_bbox
from geonode.utils import resolve_object, llbbox_to_mercator
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import default_map_config

from geonode.security.views import _perms_info_json
from geonode.cephgeo.models import CephDataObject, DataClassification, FTPRequest
from geonode.cephgeo.cart_utils import *
from geonode.documents.models import get_related_documents
from geonode.registration.models import Province, Municipality 

import geonode.settings as settings

from pprint import pprint
from datetime import datetime, timedelta

import logging

from geonode.cephgeo.utils import get_cart_datasize

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
def tiled_view(request, overlay=settings.TILED_SHAPEFILE, template="maptiles/maptiles_map.html", interest=None, test_mode=False):
    if request.method == "POST":
        pprint(request.POST)
    
    layer = {}
    try:
        layer = _resolve_layer(request, overlay, "base.view_resourcebase", _PERMISSION_VIEW )
    except Exception as e:
        layer = _resolve_layer(request, settings.MUNICIPALITY_SHAPEFILE, _PERMISSION_VIEW)
        overlay = settings.MUNICIPALITY_SHAPEFILE
            
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

    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "data_classes": DataClassification.labels.values(),
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
    }
    
    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
        
    context_dict["layer"]  = overlay
    
    #context_dict["geoserver"] = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
    context_dict["geoserver"] = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
    context_dict["siteurl"] = settings.SITEURL
    
    if interest is not None:
        context_dict["interest"]=interest
        
    context_dict["feature_municipality"]  = settings.MUNICIPALITY_SHAPEFILE.split(":")[1]
    context_dict["feature_tiled"] = overlay.split(":")[1]
    context_dict["test_mode"]=test_mode
    
    return render_to_response(template, RequestContext(request, context_dict))

def process_georefs(request):
    if request.method == "POST":
        try:
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
    """
    Note: does not check yet if tiles to be added are unique (or are not yet included in the cart)
    """
    if request.method != 'POST':
        return HttpResponse(
            content='no data received from HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    else:
        georefs = request.POST["georefs"]
        georefs_list = filter(None, georefs.split(","))
        cart_total_size = get_cart_datasize(request)
        
        yesterday = datetime.now() -  timedelta(days=1)
        
        requests_last24h = FTPRequest.objects.filter(date_time__gt=yesterday, user=request.user)
        
        total_size = 0
        for georef in georefs_list:
            objects = CephDataObject.objects.filter(name__startswith=georef)
            for o in objects:
                total_size += o.size_in_bytes
                
        request_size_last24h = 0
        
        for r in requests_last24h:
            request_size_last24h += r.size_in_bytes
        
        if total_size + cart_total_size + request_size_last24h > settings.SELECTION_LIMIT:            
            return HttpResponse(
               content=json.dumps({ "response": False, "total_size": total_size, "cart_size":cart_total_size, "recent_requests_size": request_size_last24h }),
                status=200,
                #mimetype='text/plain'
                content_type="application/json"
            )
        else:
            return HttpResponse(
                content=json.dumps({ "response": True, "total_size": total_size, "cart_size": cart_total_size }),
                status=200,
                #mimetype='text/plain'
                content_type="application/json"
            )

@login_required
def province_lookup(request, province=""):
    if province=="":
        provinces = []
        for p in Province.objects.all():
            p.append(p.province_name)
            
        return HttpResponse(
            content=json.dumps({"provinces":provinces}),
            status=200,
            content_type="application/json"
        )
    else:
        provinceObject = Province.objects.get(province_name=province)
        municipalities = []
        for m in Municipality.objects.filter(province__province_name="province"):
            m.append(m.municipality_name)
            
        return HTTPResponse(
            content=json.dumps({"province":province, "municipalities": municipalities }),
            status=200,
            content_type="application/json",
        )
    

    
