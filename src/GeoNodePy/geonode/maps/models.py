from django.conf import settings
from django.db import models
from urllib import urlopen
from owslib.wms import WebMapService
from xml.etree import ElementTree

def get_layers(wms_url):
    """Retrieve layers from a given WMS URL"""
    try:
        wms = WebMapService(wms_url)
        return wms.contents
    except Exception, e:
        # TODO: Error logging
        return {}

class LayerManager(models.Manager):
    def slurp(self):
        wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
        wms = get_layers(wms_url)
        for name, layer in wms.iteritems():
            self.model(typename=name).save()

class Layer(models.Model):
    wms = get_layers("%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL)
    objects = LayerManager()
    typename = models.CharField(max_length=128)

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""
        return [
            ("SHAPE-ZIP", "%s/wfs?request=GetFeature&typename=%s&format=SHAPE-ZIP" % (settings.GEOSERVER_BASE_URL, self.typename)),
            ("application/vnd.google-earth.kml+xml", "%s/wms?request=GetMap&layers=%s&format=application/vnd.google-earth.kml+xml" % (settings.GEOSERVER_BASE_URL, self.typename)),
            ("application/pdf", "%s/wms?request=GetMap&layers=%s&format=application/pdf" % (settings.GEOSERVER_BASE_URL, self.typename)),
        ]

    def maps(self):
        """Return a list of all the maps that use this layer"""
        #return [{'absolute_url':'b', 'title': 'd'}]
        local_wms = "%swms" % settings.GEOSERVER_BASE_URL
        return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename)])

    def metadata(self): 
        if not self.typename in self.__class__.wms:
            wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
            self.__class__.wms = get_layers(wms_url)
        return self.__class__.wms[self.typename]

    def __str__(self):
        return "%s Layer" % self.typename

class Map(models.Model):
    # metadata fields
    title = models.CharField(max_length=200)
    abstract = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    featured = models.BooleanField()
    endorsed = models.BooleanField()

    # viewer configuration
    zoom = models.IntegerField()
    center_lat = models.FloatField()
    center_lon = models.FloatField()

    def __unicode__(self):
        return '%s by %s' % (self.title, self.contact)

    def get_absolute_url(self):
        return '/maps/%i' % self.id

class MapLayer(models.Model):
    name = models.CharField(max_length=200)
    ows_url = models.URLField()
    group = models.CharField(max_length=200,blank=True)
    stack_order = models.IntegerField()
    map = models.ForeignKey(Map, related_name="layer_set")

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)


