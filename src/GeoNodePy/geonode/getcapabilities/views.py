# -*- coding: utf-8 -*-
from django.conf import settings
from lxml import etree
from django.template import Context
from django.template.loader import get_template
from geonode.maps.models import Layer
from django.http import HttpResponse, HttpResponseRedirect

ONLINE_RESOURCE = "http://geoserver.org";
EPSG_CODES = [4326,900913]

capabilities_1_1_xmltemplate = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd">
    <WMT_MS_Capabilities version="1.1.1" updateSequence="0" xmlns:xlink="http://www.w3.org/1999/xlink">
      <Service>
        <Name>OGC:WMS</Name>
      </Service>
      <Capability>
        <Request>
          <GetCapabilities>
            <Format>application/vnd.ogc.wms_xml</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetCapabilities>
          <GetMap>
            <Format>image/png</Format>
            <Format>image/png8</Format>
            <Format>image/jpeg</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetMap>
          <GetFeatureInfo>
            <Format>text/plain</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xlink:type="simple"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetFeatureInfo>
        </Request>
        <Exception>
          <Format>application/vnd.ogc.se_xml</Format>
          <Format>application/vnd.ogc.se_inimage</Format>
          <Format>application/vnd.ogc.se_blank</Format>
          <Format>text/html</Format>
        </Exception>
        <Layer>
        </Layer>
      </Capability>
    </WMT_MS_Capabilities>
    """


def GetCapabilities_1_3(request, map=None, user=None, category=None):
        tpl = get_template("getcapabilities/GetCapabilities_1_3.xml")
        ctx = Context({
            'settings': settings
        })
        gc_str = tpl.render(ctx)
        gc_str = gc_str.encode("utf-8")
        root = etree.fromstring(gc_str)
          
            
        rootlayerelem = root.find('.//Capability/Layer')
        for layer in Layer.objects.all():
                layerproj = layer.srs
                layername = etree.Element('Name')
                layername.text = layer.name
#                 env = layer.envelope()
#                 llp = layerproj.inverse(Coord(env.minx, env.miny))
#                 urp = layerproj.inverse(Coord(env.maxx, env.maxy))
#                 latlonbb = etree.Element('LatLonBoundingBox')
#                 latlonbb.set('minx', str(llp.x))
#                 latlonbb.set('miny', str(llp.y))
#                 latlonbb.set('maxx', str(urp.x))
#                 latlonbb.set('maxy', str(urp.y))
#                 layerbbox = ElementTree.Element('BoundingBox')
#                 if layer.wms_srs:
#                     layerbbox.set('SRS', layer.wms_srs)
#                 else:
#                     layerbbox.set('SRS', layerproj.epsgstring())
#                 layerbbox.set('minx', str(env.minx))
#                 layerbbox.set('miny', str(env.miny))
#                 layerbbox.set('maxx', str(env.maxx))
#                 layerbbox.set('maxy', str(env.maxy))
                layere = etree.Element('Layer')
                layere.append(layername)
#                 layertitle = ElementTree.Element('Title')
#                 if hasattr(layer,'title'):
#                     layertitle.text = to_unicode(layer.title)
#                 else:
#                     layertitle.text = to_unicode(layer.name)
#                 layere.append(layertitle)
#                 layerabstract = ElementTree.Element('Abstract')
#                 if hasattr(layer,'abstract'):
#                     layerabstract.text = to_unicode(layer.abstract)
#                 else:
#                     layerabstract.text = 'no abstract'
#                 layere.append(layerabstract)
#                 if layer.queryable:
#                     layere.set('queryable', '1')
#                 layere.append(latlonbb)
#                 layere.append(layerbbox)
#                 if len(layer.wmsextrastyles) > 0:
#                     for extrastyle in [layer.wmsdefaultstyle] + list(layer.wmsextrastyles):
#                         style = ElementTree.Element('Style')
#                         stylename = ElementTree.Element('Name')
#                         stylename.text = to_unicode(extrastyle)
#                         styletitle = ElementTree.Element('Title')
#                         styletitle.text = to_unicode(extrastyle)
#                         style.append(stylename)
#                         style.append(styletitle)
#                         layere.append(style)
                rootlayerelem.append(layere)
        capabilities = etree.tostring(root,encoding='UTF-8',pretty_print=True)
        response = HttpResponse(capabilities)
        return response
