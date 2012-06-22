# -*- coding: utf-8 -*-
import logging
import math

from django.conf import settings
from django.db import models
from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import GEOSGeometry

from geonode.layers.models import Layer
from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.utils import GXPMapBase
from geonode.utils import GXPLayerBase
from geonode.utils import layer_from_viewer_config

from taggit.managers import TaggableManager

logger = logging.getLogger("geonode.maps.models")


class Map(models.Model, PermissionLevelMixin, GXPMapBase):
    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

    title = models.TextField(_('Title'))
    # A display name suitable for search results and page headers

    abstract = models.TextField(_('Abstract'))
    # A longer description of the themes in the map.

    # viewer configuration
    zoom = models.IntegerField(_('zoom'))
    # The zoom level to use when initially loading this map.  Zoom levels start
    # at 0 (most zoomed out) and each increment doubles the resolution.

    projection = models.CharField(_('projection'),max_length=32)
    # The projection used for this map.  This is stored as a string with the
    # projection's SRID.

    center_x = models.FloatField(_('center X'))
    # The x coordinate to center on when loading this map.  Its interpretation
    # depends on the projection.

    center_y = models.FloatField(_('center Y'))
    # The y coordinate to center on when loading this map.  Its interpretation
    # depends on the projection.

    owner = models.ForeignKey(User, verbose_name=_('owner'), blank=True, null=True)
    # The user that created/owns this map.

    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the map was modified.
    
    keywords = TaggableManager(_('keywords'), help_text=_("A space or comma-separated list of keywords"))

    def __unicode__(self):
        return '%s by %s' % (self.title, (self.owner.username if self.owner else "<Anonymous>"))

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

    def json(self, layer_filter):
        map_layers = MapLayer.objects.filter(map=self.id)
        layers = [] 
        for map_layer in map_layers:
            if map_layer.local():   
                layer =  Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else: 
                pass 

        if layer_filter:
            layers = [l for l in layers if layer_filter(l)]

        readme = (
            "Title: %s\n" +
            "Author: %s\n"
            "Abstract: %s\n"
        ) % (self.title, "The GeoNode Team", self.abstract)

        def layer_json(lyr):
            return {
                "name": lyr.typename,
                "service": lyr.service_type,
                "serviceURL": "",
                "metadataURL": ""
            }

        map_config = {
            "map" : { "readme": readme },
            "layers" : [layer_json(lyr) for lyr in layers]
        }

        return json.dumps(map_config)

    def update_from_viewer(self, conf):
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.  
        
        This method automatically persists to the database!
        """
        if isinstance(conf, basestring):
            conf = json.loads(conf)

        self.title = conf['about']['title']
        self.abstract = conf['about']['abstract']

        self.zoom = conf['map']['zoom']

        self.center_x = conf['map']['center'][0]
        self.center_y = conf['map']['center'][1]

        self.projection = conf['map']['projection']

        def source_for(layer):
            return conf["sources"][layer["source"]]

        layers = [l for l in conf["map"]["layers"]]
        
        for layer in self.layer_set.all():
            layer.delete()
            
        self.keywords.add(*conf['map'].get('keywords', []))

        for ordering, layer in enumerate(layers):
            self.layer_set.add(
                layer_from_viewer_config(
                    MapLayer, layer, source_for(layer), ordering
            ))
        self.save()

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return '/maps/%i' % self.id
        
    class Meta:
        # custom permissions, 
        # change and delete are standard in django
        permissions = (('view_map', 'Can view'), 
                       ('change_map_permissions', "Can change permissions"), )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ  = 'map_readonly'
    LEVEL_WRITE = 'map_readwrite'
    LEVEL_ADMIN = 'map_admin'
    
    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)    

    def create_from_layer_list(self, user, layers, title, abstract):
        self.owner = user
        self.title = title
        self.abstract = abstract
        self.projection="EPSG:900913"
        self.zoom = 0
        self.center_x = 0
        self.center_y = 0
        map_layers = []
        bbox = None
        index = 0

        DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = geonode.maps.views.default_map_config()
        
        for layer in layers:
            try:
                layer = Layer.objects.get(typename=layer)
            except ObjectDoesNotExist:
                continue # Raise exception?
            
            if not user.has_perm('maps.view_layer', obj=layer):
                # invisible layer, skip inclusion or raise Exception?
                continue # Raise Exception
            
            layer_bbox = layer.resource.latlon_bbox
            if bbox is None:
                bbox = list(layer_bbox[0:4])
            else:
                bbox[0] = min(bbox[0], layer_bbox[0])
                bbox[1] = max(bbox[1], layer_bbox[1])
                bbox[2] = min(bbox[2], layer_bbox[2])
                bbox[3] = max(bbox[3], layer_bbox[3])

            map_layers.append(MapLayer(
                map = self,
                name = layer.typename,
                ows_url = settings.GEOSERVER_BASE_URL + "wms",  
                stack_order = index,
                visibility = True
            ))
            
        
            if bbox is not None:
                minx, maxx, miny, maxy = [float(c) for c in bbox]
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2
                wkt = "POINT(" + str(x) + " " + str(y) + ")"
                center = GEOSGeometry(wkt, srid=4326)
                center.transform("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs")

                width_zoom = math.log(360 / (maxx - minx), 2)
                height_zoom = math.log(360 / (maxy - miny), 2)

                self.center_x = center.x
                self.center_y = center.y
                self.zoom = math.ceil(min(width_zoom, height_zoom))
            index += 1

        self.save()
        for bl in DEFAULT_BASE_LAYERS:
            bl.map = self
            bl.save()

        for ml in map_layers:
            ml.map = self # update map_id after saving map
            ml.save()

class MapLayer(models.Model, GXPLayerBase):
    """
    The MapLayer model represents a layer included in a map.  This doesn't just
    identify the dataset, but also extra options such as which style to load
    and the file format to use for image tiles.
    """

    map = models.ForeignKey(Map, related_name="layer_set")
    # The map containing this layer

    stack_order = models.IntegerField(_('stack order'))
    # The z-index of this layer in the map; layers with a higher stack_order will
    # be drawn on top of others.

    format = models.CharField(_('format'), null=True, max_length=200)
    # The mimetype of the image format to use for tiles (image/png, image/jpeg,
    # image/gif...)

    name = models.CharField(_('name'), null=True, max_length=200)
    # The name of the layer to load.

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    opacity = models.FloatField(_('opacity'), default=1.0)
    # The opacity with which to render this layer, on a scale from 0 to 1.

    styles = models.CharField(_('styles'), null=True,max_length=200)
    # The name of the style to use for this layer (only useful for WMS layers.)

    transparent = models.BooleanField(_('transparent'))
    # A boolean value, true if we should request tiles with a transparent background.

    fixed = models.BooleanField(_('fixed'), default=False)
    # A boolean value, true if we should prevent the user from dragging and
    # dropping this layer in the layer chooser.

    group = models.CharField(_('group'), null=True,max_length=200)
    # A group label to apply to this layer.  This affects the hierarchy displayed
    # in the map viewer's layer tree.

    visibility = models.BooleanField(_('visibility'), default=True)
    # A boolean value, true if this layer should be visible when the map loads.

    ows_url = models.URLField(_('ows URL'), null=True)
    # The URL of the OWS service providing this layer, if any exists.

    layer_params = models.TextField(_('layer params'))
    # A JSON-encoded dictionary of arbitrary parameters for the layer itself when
    # passed to the GXP viewer.

    # If this dictionary conflicts with options that are stored in other fields
    # (such as format, styles, etc.) then the fields override.

    source_params = models.TextField(_('source params'))
    # A JSON-encoded dictionary of arbitrary parameters for the GXP layer source
    # configuration for this layer.

    # If this dictionary conflicts with options that are stored in other fields
    # (such as ows_url) then the fields override.
    
    def local(self): 
        """
        Tests whether this layer is served by the GeoServer instance that is
        paired with the GeoNode site.  Currently this is based on heuristics,
        but we try to err on the side of false negatives.
        """
        if self.ows_url == (settings.GEOSERVER_BASE_URL + "wms"):
            return Layer.objects.filter(typename=self.name).count() != 0
        else: 
            return False

    @property
    def local_link(self): 
        if self.local():
            layer = Layer.objects.get(typename=self.name)
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),layer.title)
        else: 
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)
