from django.conf import settings
from django.db import models
from owslib.wms import WebMapService
from geoserver.catalog import Catalog

_wms = None

class LayerManager(models.Manager):
    def slurp(self):
        url = "%srest" % settings.GEOSERVER_BASE_URL 
        cat = Catalog(url,"admin","geoserver")
        stores = cat.getStores()
        for store in stores:
            resources = store.getResources()
            for resource in resources:
                if resource.name is not None and self.filter(name=resource.name).count() == 0:
                    typename = "%s:%s" % (store.workspace.name,resource.name)
                    self.model(workspace=store.workspace.name,
                               store=store.name,
                               storeType=store.resourceType,
			       name=resource.name,
			       typename=typename).save()


class Layer(models.Model):
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    typename = models.CharField(max_length=128)

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""
        #TODO: This function is just a stub
        return [
            ("SHAPE-ZIP", "%swfs?request=GetFeature&typename=%s&format=SHAPE-ZIP" % (settings.GEOSERVER_BASE_URL, self.typename)),
            ("application/vnd.google-earth.kml+xml", "%swms?request=GetMap&layers=%s&format=application/vnd.google-earth.kml+xml" % (settings.GEOSERVER_BASE_URL, self.typename)),
            ("application/pdf", "%swms?request=GetMap&layers=%s&format=application/pdf" % (settings.GEOSERVER_BASE_URL, self.typename)),
        ]

    def metadata_links(self):
        """Returns a list of (type, URL) tuples for known metadata documents
        about this data"""
        #TODO: This function is just a stub
        return [("GeoNode Listing", ".")]

    def maps(self):
        """Return a list of all the maps that use this layer"""
        local_wms = "%swms" % settings.GEOSERVER_BASE_URL
        return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename).select_related()])

    def styles(self):
        """Return a list of known styles applicable to this layer"""
        return self.metadata().styles

    def metadata(self): 
        global _wms
        if (_wms is None) or (self.typename not in _wms.contents):
            wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
            _wms = WebMapService(wms_url)
        return _wms[self.typename]

    def get_absolute_url(self):
        return "/data/%s" % self.typename


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
