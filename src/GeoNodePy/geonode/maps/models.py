from django.conf import settings
from django.db import models
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb
from geoserver.catalog import Catalog
from geonode.geonetwork import Catalog as GeoNetwork
from django.db.models import signals
from django.utils.html import escape
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

_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.0339,
        "units": "m",
        "maxExtent": [-20037508.34,-20037508.34,20037508.34,20037508.34],
    },
    "EPSG:4326": {
        "max_resolution": (180 - (-180)) / 256,
        "units": "degrees",
        "maxExtent": [-180, -90, 180, 90]
    }
}

def _get_viewer_projection_info(srid):
    # TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})

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
                ("gml", _("GML 2.0"), "gml2")
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

    def save(self, *args, **kw):
        models.Model.save(self, *args, **kw)
        if hasattr(self, "_resource_cache"):
            Layer.objects.gs_catalog.save(self._resource_cache)
        if hasattr(self, "_publishing_cache"):
            Layer.objects.gs_catalog.save(self._publishing_cache)

    def get_absolute_url(self):
        return "%sdata/%s" % (settings.SITEURL,self.typename)

    def __str__(self):
        return "%s Layer" % self.typename


class Map(models.Model):
    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

    title = models.CharField(max_length=200)
    """
    A display name suitable for search results and page headers
    """

    abstract = models.CharField(max_length=200)
    """
    A longer description of the themes in the map.
    """

    contact = models.CharField(max_length=200)
    """
    *Deprecated* A free-form text field identifying the map's creator.  Prefer
    ``owner`` over this for new code.
    """
    
    featured = models.BooleanField()
    """
    *Deprecated* A boolean identifying this map as a candidate for display on
    the site front page.  The map on the home page is being considered for
    removal, and this flag would go with it.
    """

    endorsed = models.BooleanField()
    """
    *Deprecated* A boolean identifying this map as endorsed by the maintainers
    of the site.  This flag will be removed as ratings become a more flexible
    system for identifying high-quality maps.
    """

    # viewer configuration
    zoom = models.IntegerField()
    """
    The zoom level to use when initially loading this map.  Zoom levels start
    at 0 (most zoomed out) and each increment doubles the resolution.
    """

    projection = models.CharField(max_length=32)
    """
    The projection used for this map.  This is stored as a string with the
    projection's SRID.
    """

    center_x = models.FloatField()
    """
    The x coordinate to center on when loading this map.  Its interpretation
    depends on the projection.
    """

    center_y = models.FloatField()
    """
    The y coordinate to center on when loading this map.  Its interpretation
    depends on the projection.
    """

    owner = models.ForeignKey(User, blank=True, null=True)
    """
    The user that created/owns this map.
    """

    def __unicode__(self):
        return '%s by %s' % (self.title, self.contact)

    @property
    def center(self):
        """
        A handy shortcut for the center_x and center_y properties as a tuple
        (read only)
        """
        return (self.center_x, self.center_y)

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

    def viewer_json(self, *added_layers):
        """
        Convert this map to a nested dictionary structure matching the JSON
        configuration for GXP Viewers.

        The ``added_layers`` parameter list allows a list of extra MapLayer
        instances to append to the Map's layer list when generating the
        configuration. These are not persisted; if you want to add layers you
        should use ``.layer_set.create()``.
        """
        layers = list(self.layer_set.all()) + list(added_layers) #implicitly sorted by stack_order
        server_lookup = {}
        sources = dict()
        sources.update(settings.MAP_BASELAYERSOURCES)

        def uniqify(seq):
            """
            get a list of unique items from the input sequence.
            
            This relies only on equality tests, so you can use it on most
            things.  If you have a sequence of hashables, list(set(seq)) is
            better.
            """
            results = []
            for x in seq:
                if x not in results: results.append(x)
            return results

        i = 0
        for source in uniqify(l.source_config() for l in layers):
            while str(i) in sources: i = i + 1
            sources[str(i)] = source 
            server_lookup[simplejson.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source: return k
            return None

        def layer_config(l):
            cfg = l.layer_config()
            source = source_lookup(l.source_config())
            if source: cfg["source"] = source
            return cfg

        config = {
            'id': self.id,
            'about': {
                'title':    escape(self.title),
                'contact':  escape(self.contact),
                'abstract': escape(self.abstract),
                'endorsed': self.endorsed
            },
            'defaultSourceType': "gx_wmssource",
            'sources': sources,
            'map': {
                'layers': settings.MAP_BASELAYERS + [layer_config(l) for l in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom
            }
        }

        config["map"].update(_get_viewer_projection_info(self.projection))

        return config

    def update_from_viewer(self, conf):
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.  
        
        This method automatically persists to the database!
        """
        if isinstance(conf, basestring):
            conf = simplejson.loads(conf)

        self.title = conf['about']['title']
        self.abstract = conf['about']['abstract']
        self.contact = conf['about']['contact']

        self.zoom = conf['map']['zoom']

        self.center_x = conf['map']['center'][0]
        self.center_y = conf['map']['center'][1]

        self.projection = conf['map']['projection']

        self.featured = conf['about'].get('featured', False)

        def source_for(layer):
            return conf["sources"][layer["source"]]

        def is_wms(layer):
            if "ptype" in source_for(l):
                return source_for(l)["ptype"] == "gx_wmssource"
            else:
                return conf["defaultSourceType"] == "gx_wmssource"
       
        layers = [l for l in conf["map"]["layers"] if is_wms(l)]
        
        for layer in self.layer_set.all():
            layer.delete()

        for ordering, layer in enumerate(layers):
            self.layer_set.from_viewer_config(
                self, layer, source_for(layer), ordering
            )
        self.save()

    def get_absolute_url(self):
        return '/maps/%i' % self.id

class MapLayerManager(models.Manager):
    def from_viewer_config(self, map, layer, source, ordering):
        layer_cfg = dict(layer)
        for k in ["format", "name", "opacity", "styles", "transparent",
                  "fixed", "group", "visibility", "title", "source"]:
            if k in layer_cfg: del layer_cfg[k]

        source_cfg = dict(source)
        for k in ["url", "projection"]:
            if k in source_cfg: del source_cfg[k]

        return self.create(
            map = map,
            stack_order = ordering,
            format = layer.get("format", None),
            name = layer.get("name", None),
            opacity = layer.get("opacity", 1),
            styles = layer.get("styles", None),
            transparent = layer.get("transparent", False),
            fixed = layer.get("fixed", False),
            group = layer.get('group', ""),
            visibility = layer.get("visibility", True),
            ows_url = source.get("url", None),
            layer_params = simplejson.dumps(layer_cfg),
            source_params = simplejson.dumps(source_cfg)
        )

class MapLayer(models.Model):
    objects = MapLayerManager()

    map = models.ForeignKey(Map, related_name="layer_set")
    stack_order = models.IntegerField()

    format = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    opacity = models.FloatField(default=1.0)
    styles = models.CharField(max_length=200)
    transparent = models.BooleanField()

    fixed = models.BooleanField(default=False)
    group = models.CharField(max_length=200,blank=True)
    visibility = models.BooleanField(default=True)

    ows_url = models.URLField()

    layer_params = models.CharField(max_length=1024)
    source_params = models.CharField(max_length=1024)
    
    def local(self): 
        layer = Layer.objects.filter(typename=self.name)
        if layer.count() == 0:
            return False
        else: 
            return True
 
    def source_config(self):
        try:
            cfg = simplejson.loads(self.source_params)
        except:
            cfg = dict(ptype = "gx_wmssource")

        if self.ows_url: cfg["url"] = self.ows_url

        return cfg

    def layer_config(self):
        try:
            cfg = simplejson.loads(self.layer_params)
        except: 
            cfg = dict()

        if self.format: cfg['format'] = self.format
        if self.name: cfg["name"] = self.name
        if self.opacity: cfg['opacity'] = self.opacity
        if self.styles: cfg['styles'] = self.styles
        if self.transparent: cfg['transparent'] = True

        cfg["fixed"] = self.fixed
        if self.group: cfg["group"] = self.group
        cfg["visibility"] = self.visibility

        return cfg


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


signals.pre_delete.connect(delete_layer, sender=Layer)
