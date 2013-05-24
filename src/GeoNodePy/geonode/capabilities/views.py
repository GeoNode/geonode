# -*- coding: utf-8 -*-
from django.conf import settings
from lxml import etree
from django.template import Context
from django.template.loader import get_template
from geonode.maps.models import Layer, Map
from django.http import HttpResponse, HttpResponseRedirect
from urlparse import urlparse
import httplib2

def get_layer_capabilities(user,workspace,layer):
    wms_url = settings.GEOSERVER_BASE_URL + "%s/%s/wms?request=GetCapabilities&version=1.1.0" % (workspace, layer)
    http = httplib2.Http()
    response, getcap = http.request(wms_url)
    return getcap

def format_online_resource(workspace,layer,element):
    layerName = element.find('.//Name')
    layerName.text = workspace + ":" + layer
    layerresources = element.findall('.//OnlineResource')
    for resource in layerresources:
        wtf = resource.attrib['{http://www.w3.org/1999/xlink}href']
        resource.attrib['{http://www.w3.org/1999/xlink}href'] = wtf.replace("/"+workspace+"/"+layer,"")  

def get_capabilities(request, user=None, mapid=None, category=None):
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
                layercap = etree.fromstring(get_layer_capabilities(request.user, workspace, layername))
                if rootdoc is None:
                    rootdoc = etree.ElementTree(layercap)
                    rootlayerelem = rootdoc.find('.//Capability/Layer')
                    format_online_resource(workspace,layername,rootlayerelem)
                else:
                    layerelem = layercap.find('.//Capability/Layer/Layer')
                    format_online_resource(workspace,layername,layerelem)               
                    rootlayerelem.append(layerelem)
            except Exception, e:
                pass
        if rootdoc is not None:
            capabilities = etree.tostring(rootdoc, xml_declaration=True, encoding='UTF-8',pretty_print=True)
            response = HttpResponse(capabilities, content_type="text/xml")
            return response
        return HttpResponse(status=200)
