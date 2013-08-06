# -*- coding: utf-8 -*-
from django.conf import settings
from lxml import etree
from django.template import Context
from django.template.loader import get_template
from geonode.maps.models import Layer, Map
from django.http import HttpResponse, HttpResponseRedirect
from urlparse import urlparse
import httplib2
from django.shortcuts import redirect
import logging

logger = logging.getLogger("geonode.capabilities.views")

def get_layer_capabilities(workspace, layer):
    """
    Retrieve a layer-specific GetCapabilities document
    """
    wms_url = "http://localhost:8080/geoserver/%s/%s/wms?request=GetCapabilities&version=1.1.0" % (workspace, layer)
    http = httplib2.Http()
    response, getcap = http.request(wms_url)
    return getcap

def format_online_resource(workspace, layer, element):
    """
    Replace workspace/layer-specific OnlineResource links with the more
    generic links returned by a site-wide GetCapabilities document
    """
    layerName = element.find('.//Name')
    layerName.text = workspace + ":" + layer
    layerresources = element.findall('.//OnlineResource')
    for resource in layerresources:
        wtf = resource.attrib['{http://www.w3.org/1999/xlink}href']
        resource.attrib['{http://www.w3.org/1999/xlink}href'] = wtf.replace("/" + workspace + "/" + layer, "")  

def get_capabilities(request, user=None, mapid=None, category=None):
    """
    Compile a GetCapabilities document containing public layers 
    filtered by user, map, or category
    """
    if "REQUEST" in request.GET and request.GET["REQUEST"].lower() != "getcapabilities":
        # This should be redirected to GeoServer
        new_url = "%s%s?%s" % (settings.GEOSERVER_BASE_URL, request.GET["SERVICE"].lower(), request.META["QUERY_STRING"])
        return redirect(new_url, permanent=True)
    
    rootdoc = None
    rootlayerelem = None        
    layers = None
        
    if user is not None:
        layers = Layer.objects.filter(owner__username=user)
    elif category is not None:
        layers = Layer.objects.filter(topic_category__name=category)
    elif map is not None:
        map_obj = Map.objects.get(id=mapid)
        typenames = []
        for maplayer in map_obj.maplayers:
            if maplayer.local:
                typenames.append(maplayer.name)               
                layers = Layer.objects.filter(typename__in=typenames)
    for layer in layers:
        try:
            workspace, layername = layer.typename.split(":")
            if rootdoc is None:  # 1st one, seed with real GetCapabilities doc
                try:
                    layercap = etree.fromstring(get_layer_capabilities(workspace, layername))
                    rootdoc = etree.ElementTree(layercap)
                    rootlayerelem = rootdoc.find('.//Capability/Layer')
                    format_online_resource(workspace, layername, rootdoc)
                except Exception, e:
                    logger.error("Error occurred creating GetCapabilities for %s:%s" % (layer.typename, str(e)))
            else:  
                    # Get the required info from layer model
                    tpl = get_template("capabilities/layer.xml")
                    ctx = Context({
                        'layer': layer,
                        'settings': settings,
                        'publishing' : layer.publishing
                        })
                    gc_str = tpl.render(ctx)
                    gc_str = gc_str.encode("utf-8")
                    layerelem = etree.XML(gc_str)            
                    rootlayerelem.append(layerelem)
        except Exception, e:
                logger.error("Error occurred creating GetCapabilities for %s:%s" % (layer.typename, str(e)))
                pass
    if rootdoc is not None:
        capabilities = etree.tostring(rootdoc, xml_declaration=True, encoding='UTF-8', pretty_print=True)
        return HttpResponse(capabilities, content_type="text/xml")
    return HttpResponse(status=200)
