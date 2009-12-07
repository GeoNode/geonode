from django.conf import settings
from django.db import models
from urllib import urlopen
from xml.etree import ElementTree

def get_layers(wms_url):
    try:
        xlink = "{http://www.w3.org/1999/xlink}"
        dom = ElementTree.parse(urlopen(wms_url))
        layers = dict()
        for layer in dom.findall("//Layer"):
            if layer.find("Name") is None:
                continue
            atts = dict()
            attribution = layer.find("Attribution")
            if attribution is not None: 
                if attribution.find("Title") is not None:
                    atts['title'] = attribution.find("Title").text
                if attribution.find("OnlineResource") is not None:
                    atts['url'] = attribution.find("OnlineResource").get(xlink + 'href')
                if attribution.find("LogoURL") is not None:
                    logo = attribution.find("LogoURL")
                    atts['logo'] = {
                        'url': logo.find("OnlineResource").get(xlink + 'href'),
                        'size': (logo.get('width'), logo.get('height')),
                        'format': logo.find("Format").text
                    }
            layers[layer.find("Name").text] = atts
        return layers
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
