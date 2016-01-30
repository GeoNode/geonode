"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.contrib.auth.models import User

from django.test import TestCase, Client
from mock import Mock
import geonode.capabilities.models
import geonode.capabilities.views
from lxml import etree

def fake_getcap (workspace, layer):
    capxml = """
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://localhost:8080/geoserver/schemas/wms/1.1.1/WMS_MS_Capabilities.dtd">
<WMT_MS_Capabilities version="1.1.1" updateSequence="328669">
  <Service>
    <Name>geonode:POLICESTATIONS_PT_MEMA</Name>
    <Title>WorldMap</Title>
    <Abstract>WorldMap Geographic Data WMS Server</Abstract>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://geoserver.org/"/>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>application/vnd.ogc.wms_xml</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/geoserver/wms?SERVICE=WMS&amp;"/>
            </Get>
            <Post>
              <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/geoserver/wms?SERVICE=WMS&amp;"/>
            </Post>
          </HTTP>
        </DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/geoserver/wms?SERVICE=WMS&amp;"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetMap>
    </Request>
    <Layer>
      <Title>WorldMap</Title>
      <Abstract>WorldMap Geographic Data WMS Server</Abstract>
      <!--Limited list of EPSG projections:-->
      <SRS>EPSG:3857</SRS>
      <SRS>EPSG:4326</SRS>
      <SRS>EPSG:900913</SRS>
      <LatLonBoundingBox minx="-73.47629198277667" miny="41.27691903910831" maxx="-69.93391223163592" maxy="42.857326357585926"/>
      <Layer queryable="1">
        <Name>%workspace%:%layername%</Name>
        <Title>%layername%</Title>
        <Abstract>%layername%</Abstract>
        <KeywordList>
          <Keyword>%layername%</Keyword>
        </KeywordList>
        <SRS>EPSG:4326</SRS>
        <LatLonBoundingBox minx="1.0" miny="2.0" maxx="3.0" maxy="3.0"/>
        <BoundingBox SRS="EPSG:4326" minx="1.0" miny="2.0" maxx="3.0" maxy="3.0"/>
        <Attribution>
          <Title>bobby</Title>
        </Attribution>
        <MetadataURL type="TC211">
          <Format>text/xml</Format>
          <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/geonetwork/srv/en/csw?outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd&amp;service=CSW&amp;request=GetRecordById&amp;version=2.0.2&amp;elementsetname=full&amp;id=d81d2a4c-6565-43f5-9d2b-1ab8e9f3f08a"/>
        </MetadataURL>
        <Style>
          <Name>base_CA</Name>
          <Title/>
          <Abstract/>
          <LegendURL width="20" height="20">
            <Format>image/png</Format>
            <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:type="simple" xlink:href="http://localhost:8080/geoserver/wms?request=GetLegendGraphic&amp;format=image%2Fpng&amp;width=20&amp;height=20&amp;layer=POLICESTATIONS_PT_MEMA"/>
          </LegendURL>
        </Style>
      </Layer>
    </Layer>
  </Capability>
</WMT_MS_Capabilities>
"""
    return capxml.replace("%workspace%", workspace).replace("%layername%", layer)

geonode.capabilities.views.get_layer_capabilities = fake_getcap

class CapabilitiesTest(TestCase):
    fixtures = ['test_data.json', 'capabilities_data.json']


    viewer_config = """
    {
      "defaultSourceType": "gx_wmssource",
      "about": {
          "title": "Title2",
          "abstract": "Abstract2",
          "urlsuffix" : "",
          "introtext": "",
          "keywords": ""
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8001/geoserver/wms"
        }
      },
     "treeconfig": {},
      "map": {
        "groups": {},
        "projection":"EPSG:900913",
        "units":"m",
        "maxResolution":156543.0339,
        "maxExtent":[-20037508.34,-20037508.34,20037508.34,20037508.34],
        "center":[-9428760.8688778,1436891.8972581],
        "layers":[{
          "source":"base",
          "buffer":0,
          "wms":"capra",
          "name":"base:CA"
        }{
          "source":"capra",
          "buffer":0,
          "wms":"capra",
          "name":"base:CA2"
        }],
        "zoom":7
      }
    }
    """



    def test_capabilities_map(self):
        """
        Tests that a valid GetCapabilities doc is returned for a map
        """
        c = Client()
        response = c.get("/capabilities/map/1/")

        layercap = etree.fromstring(response.content)
        rootdoc = etree.ElementTree(layercap)
        layernodes = rootdoc.findall('.//Capability/Layer/Layer')
        self.assertEquals(2, len(layernodes))

        cntCA = [0,0];
        for layer in layernodes:
            if  layer.find("Name").text == "base:CA":
                cntCA[0]+=1
            elif layer.find("Name").text == "base:CA2":
                cntCA[1]+=1
            else:
                self.fail("Incorrect layers returned in GetCapabilities")
        self.assertEquals(1, cntCA[0])
        self.assertEquals(1, cntCA[1])


    def test_capabilities_user(self):
        """
        Tests that a valid GetCapabilities doc is returned for a user
        """
        user = User.objects.get(id=1)
        c = Client()
        response = c.get("/capabilities/user/%s/" % user.username)

        layercap = etree.fromstring(response.content)
        rootdoc = etree.ElementTree(layercap)
        layernodes = rootdoc.findall('.//Capability/Layer/Layer')
        self.assertEquals(3, len(layernodes))


        cntCA = [0,0,0];
        for layer in layernodes:
            if  layer.find("Name").text == "base:CA":
                cntCA[0]+=1
            elif layer.find("Name").text == "base:CA2":
                cntCA[1]+=1
            elif layer.find("Name").text == "base:CA3":
                cntCA[2]+=1
            else:
                self.fail("Incorrect layers returned in GetCapabilities")
        self.assertEquals(1, cntCA[0])
        self.assertEquals(1, cntCA[1])
        self.assertEquals(1, cntCA[2])