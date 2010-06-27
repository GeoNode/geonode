from django.conf import settings
from django.db import models
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb
from geoserver.catalog import Catalog
from geonode.geonetwork import Catalog as GeoNetwork
from django.db.models import signals
import httplib2
import simplejson
import urllib
import uuid
from django.contrib.auth.models import User

def _(x): return x

def get_csw():
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    csw = CatalogueServiceWeb(csw_url);
    return csw

_wms = None
_csw = None
_user, _password = settings.GEOSERVER_CREDENTIALS

class LayerManager(models.Manager):
    
    def __init__(self):
        models.Manager.__init__(self)
        url = "%srest" % settings.GEOSERVER_BASE_URL
        user, password = settings.GEOSERVER_CREDENTIALS
        self.gs_catalog = Catalog(url, _user, _password)

    def slurp(self):
        cat = self.gs_catalog
        gn = GeoNetwork(settings.GEONETWORK_BASE_URL, settings.GEONETWORK_CREDENTIALS[0], settings.GEONETWORK_CREDENTIALS[1])
        gn.login()

        for resource in cat.get_resources():
            try:
                store = resource.store
                workspace = store.workspace

                layer, created = self.get_or_create(name=resource.name, defaults = {
                    "workspace": workspace.name,
                    "store": store.name,
                    "storeType": store.resource_type,
                    "typename": "%s:%s" % (workspace.name, resource.name),
                    "uuid": str(uuid.uuid4())
                })

                if layer.uuid is None:
                    layer.uuid = str(uuid.uuid4())
                    layer.save()

                record = gn.get_by_uuid(layer.uuid)
                if record is None:
                    md_link = gn.create_from_layer(layer)
                    layer.metadata_links = [("text/xml", "TC211", md_link)]
                    layer.save()
                else: 
                    gn.update(record, layer)
            finally:
                pass
        gn.logout()

class Layer(models.Model):
    """
    XXX docs strings
    """
    
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    uuid = models.CharField(max_length=36)
    typename = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, blank=True, null=True)

    def download_links(self):
        """Returns a list of (mimetype, URL) tuples for downloads of this data
        in various formats."""
 
        bbox = self.resource.latlon_bbox

        dx = float(bbox[1]) - float(bbox[0])
        dy = float(bbox[3]) - float(bbox[2])

        dataAspect = dx / dy

        height = 550
        width = int(height * dataAspect)

        # bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),

        srs = 'EPSG:4326' # bbox[4] might be None
        bbox_string = ",".join([bbox[0], bbox[2], bbox[1], bbox[3]])

        links = []        

        if self.resource.resource_type == "featureType":
            def wfs_link(mime):
                return settings.GEOSERVER_BASE_URL + "wfs?" + urllib.urlencode({
                    'service': 'WFS',
                    'request': 'GetFeature',
                    'typename': self.typename,
                    'outputFormat': mime
                })
            types = [
                ("zip", _("Zipped Shapefile"), "SHAPE-ZIP"),
                ("gml", _("GML"), "gml")
            ]
            links.extend((ext, name, wfs_link(mime)) for ext, name, mime in types)

        def wms_link(mime):
            return settings.GEOSERVER_BASE_URL + "wms?" + urllib.urlencode({
                'service': 'WMS',
                'request': 'GetMap',
                'layers': self.typename,
                'format': mime,
                'height': height,
                'width': width,
                'srs': srs,
                'bbox': bbox_string
            })

        types = [
            ("kmz", _("Zipped KML"), "application/vnd.google-earth.kmz+xml"),
            ("tiff", _("GeoTiff"), "image/geotiff"),
            ("pdf", _("PDF"), "application/pdf"),
            ("png", _("PNG"), "image/png")
        ]

        links.extend((ext, name, wms_link(mime)) for ext, name, mime in types)

        return links

    def maps(self):
        """Return a list of all the maps that use this layer"""
        local_wms = "%swms" % settings.GEOSERVER_BASE_URL
        return set([layer.map for layer in MapLayer.objects.filter(ows_url=local_wms, name=self.typename).select_related()])

    def metadata(self):
        global _wms
        if (_wms is None) or (self.typename not in _wms.contents):
            wms_url = "%swms?request=GetCapabilities" % settings.GEOSERVER_BASE_URL
            _wms = WebMapService(wms_url)
        return _wms[self.typename]

    def metadata_csw(self):
        csw = get_csw()
        csw.getrecordbyid([self.uuid], outputschema = 'http://www.isotc211.org/2005/gmd')
        return csw.records.get(self.uuid)

    @property
    def attribute_names(self):
        if self.resource.resource_type == "featureType":
            return self.resource.attributes
        elif self.resource.resource_type == "coverage":
            return [dim.name for dim in self.resource.dimensions]

    @property
    def display_type(self):
        return ({
            "dataStore" : "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    def delete_from_geoserver(self):
        layerURL = "%srest/layers/%s.xml" % (settings.GEOSERVER_BASE_URL,self.name)
        if self.storeType == "dataStore":
            featureUrl = "%srest/workspaces/%s/datastores/%s/featuretypes/%s.xml" % (settings.GEOSERVER_BASE_URL, self.workspace, self.store, self.name)
            storeUrl = "%srest/workspaces/%s/datastores/%s.xml" % (settings.GEOSERVER_BASE_URL, self.workspace, self.store)
        elif self.storeType == "coverageStore":
            featureUrl = "%srest/workspaces/%s/coveragestores/%s/coverages/%s.xml" % (settings.GEOSERVER_BASE_URL,self.workspace,self.store, self.name)
            storeUrl = "%srest/workspaces/%s/coveragestores/%s.xml" % (settings.GEOSERVER_BASE_URL,self.workspace,self.store)
        urls = (layerURL,featureUrl,storeUrl)

        # GEOSERVER_CREDENTIALS
        HTTP = httplib2.Http(".cache")
        HTTP.add_credentials(_user,_password)

        for u in urls:
            output = HTTP.request(u,"DELETE")
            if output[0]["status"][0] == '4':
                raise RuntimeError("Unable to remove from Geoserver: %s" % output[1])

    def delete_from_geonetwork(self):
        gn = GeoNetwork(settings.GEONETWORK_BASE_URL, settings.GEONETWORK_CREDENTIALS[0], settings.GEONETWORK_CREDENTIALS[1])
        gn.login()
        gn.delete_layer(self)

    def save_to_geonetwork(self):
        gn = GeoNetwork(settings.GEONETWORK_BASE_URL, settings.GEONETWORK_CREDENTIALS[0], settings.GEONETWORK_CREDENTIALS[1])
        gn.login()
        gn.update_layer(self)

    def _set_title(self, title):
        self.resource.title = title

    def _get_title(self):
        return self.resource.title

    title = property(_get_title, _set_title)

    def _set_abstract(self, abstract):
        self.resource.abstract = abstract

    def _get_abstract(self):
        return self.resource.abstract

    abstract = property(_get_abstract, _set_abstract)

    def _set_metadatalinks(self, links):
        self.resource.metadata_links = links

    def _get_metadatalinks(self):
        return self.resource.metadata_links

    metadata_links = property(_get_metadatalinks, _set_metadatalinks)

    def _set_keywords(self, keywords):
        self.resource.keywords = keywords

    def _get_keywords(self):
        return self.resource.keywords

    keywords = property(_get_keywords, _set_keywords)

    @property
    def resource(self):
        if not hasattr(self, "_resource_cache"):
            cat = Layer.objects.gs_catalog
            try:
                ws = cat.get_workspace(self.workspace)
            except AttributeError:
                # Geoserver is not running
                raise RuntimeError("Geoserver cannot be accessed, are you sure it is running in: %s" %
                                    (settings.GEOSERVER_BASE_URL))
            store = cat.get_store(self.store, ws)
            self._resource_cache = cat.get_resource(self.name, store)
        return self._resource_cache

    def _get_default_style(self):
        return self.publishing.default_style

    def _set_default_style(self, style):
        self.publishing.default_style = style

    default_style = property(_get_default_style, _set_default_style)

    def _get_styles(self):
        return self.publishing.styles

    def _set_styles(self, styles):
        self.publishing.styles = styles

    styles = property(_get_styles, _set_styles)
    
    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    @property
    def publishing(self):
        if not hasattr(self, "_publishing_cache"):
            cat = Layer.objects.gs_catalog
            self._publishing_cache = cat.get_layer(self.name)
        return self._publishing_cache

    def save_to_geoserver(self):
        if hasattr(self, "_resource_cache"):
            Layer.objects.gs_catalog.save(self._resource_cache)
        if hasattr(self, "_publishing_cache"):
            Layer.objects.gs_catalog.save(self._publishing_cache)

    def get_absolute_url(self):
        return "%sdata/%s" % (settings.SITEURL,self.typename)

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
    owner = models.ForeignKey(User, blank=True, null=True)

    def __unicode__(self):
        return '%s by %s' % (self.title, self.contact)

    @property
    def layers(self):
        layers = MapLayer.objects.filter(map=self.id)
        return  [layer for layer in layers]

    @property
    def local_layers(self): 
        return True

    @property
    def json(self):
        map_layers = MapLayer.objects.filter(map=self.id)
        layers = [] 
        for map_layer in map_layers:
            if map_layer.local():   
                layer =  Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else: 
                pass 
        map = { 
            "map" : { 
                "title" : self.title, 
                "abstract" : self.abstract,
                "author" : "The GeoNode Team",
                }, 
            "layers" : [ 
                {
                    "name" : layer.typename, 
                    "service" : layer.service_type, 
                    "metadataURL" : "http://localhost/fake/url/{name}".format(name=layer.name),
                    "serviceURL" : "http://localhost/%s" %layer.name,
                } for layer in layers ] 
            }
        return simplejson.dumps(map)

    def get_absolute_url(self):
        return '/maps/%i' % self.id


class MapLayer(models.Model):
    name = models.CharField(max_length=200)
    styles = models.CharField(max_length=200)
    opacity = models.FloatField(default=1.0)
    format = models.CharField(max_length=200)
    transparent = models.BooleanField()
    ows_url = models.URLField()
    group = models.CharField(max_length=200,blank=True)
    stack_order = models.IntegerField()
    map = models.ForeignKey(Map, related_name="layer_set")

    def local(self): 
        layer = Layer.objects.filter(typename=self.name)
        if layer.count() == 0:
            return False
        else: 
            return True

    @property
    def local_link(self): 
        if self.local():
            layer = Layer.objects.get(typename=self.name)
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),self.name)
        else: 
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)

def delete_layer(instance, sender, **kwargs): 
    """
    Removes the layer from GeoServer and GeoNetwork
    """
    instance.delete_from_geoserver()
    instance.delete_from_geonetwork()

def save_layer(instance, sender, **kwargs): 
    """
    Removes the layer from GeoServer and GeoNetwork
    """
    instance.save_to_geoserver()

signals.pre_delete.connect(delete_layer, sender=Layer)
signals.post_save.connect(save_layer, sender=Layer)
