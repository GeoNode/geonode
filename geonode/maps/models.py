# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb
from geoserver.catalog import Catalog
from geonode.security.models import PermissionLevelMixin
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.geonetwork import Catalog as GeoNetwork
from geonode.people.models import Contact
from geonode.maps.enumerations import COUNTRIES, ALL_LANGUAGES
from django.db.models import signals
from taggit.managers import TaggableManager
from django.utils import simplejson as json

import httplib2
import urllib
from urlparse import urlparse
import uuid
from datetime import datetime
from django.contrib.auth.models import User, Permission
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from string import lower
from StringIO import StringIO
from idios.models import ProfileBase, create_profile
from lxml import etree
from geonode.maps.gs_helpers import cascading_delete
import logging
import sys

logger = logging.getLogger("geonode.maps.models")

class GeoNodeException(Exception):
    """Base class for exceptions in this module."""
    pass

class Map(models.Model, PermissionLevelMixin):
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
        sources = {'local': settings.DEFAULT_LAYER_SOURCE }

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

        configs = [l.source_config() for l in layers]

        i = 0
        for source in uniqify(configs):
            while str(i) in sources: i = i + 1
            sources[str(i)] = source 
            server_lookup[json.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source: return k
            return None

        def layer_config(l):
            cfg = l.layer_config()
            src_cfg = l.source_config()
            source = source_lookup(src_cfg)
            if source: cfg["source"] = source
            return cfg

        config = {
            'id': self.id,
            'about': {
                'title':    self.title,
                'abstract': self.abstract
            },
            'defaultSourceType': "gxp_wmscsource",
            'sources': sources,
            'map': {
                'layers': [layer_config(l) for l in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom
            }
        }

        # Mark the last added layer as selected - important for data page
        config["map"]["layers"][len(layers)-1]["selected"] = True

        config["map"].update(_get_viewer_projection_info(self.projection))

        return config

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
                self.layer_set.from_viewer_config(
                    self, layer, source_for(layer), ordering
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



class MapLayerManager(models.Manager):
    def from_viewer_config(self, map_model, layer, source, ordering):
        """
        Parse a MapLayer object out of a parsed layer configuration from a GXP
        viewer.

        ``map`` is the Map instance to associate with the new layer
        ``layer`` is the parsed dict for the layer
        ``source`` is the parsed dict for the layer's source
        ``ordering`` is the index of the layer within the map's layer list
        """
        layer_cfg = dict(layer)
        for k in ["format", "name", "opacity", "styles", "transparent",
                  "fixed", "group", "visibility", "title", "source"]:
            if k in layer_cfg: del layer_cfg[k]

        source_cfg = dict(source)
        for k in ["url", "projection"]:
            if k in source_cfg: del source_cfg[k]

        return self.model(
            map = map_model,
            stack_order = ordering,
            format = layer.get("format", None),
            name = layer.get("name", None),
            opacity = layer.get("opacity", 1),
            styles = layer.get("styles", None),
            transparent = layer.get("transparent", False),
            fixed = layer.get("fixed", False),
            group = layer.get('group', None),
            visibility = layer.get("visibility", True),
            ows_url = source.get("url", None),
            layer_params = json.dumps(layer_cfg),
            source_params = json.dumps(source_cfg)
        )

class MapLayer(models.Model):
    """
    The MapLayer model represents a layer included in a map.  This doesn't just
    identify the dataset, but also extra options such as which style to load
    and the file format to use for image tiles.
    """

    objects = MapLayerManager()
    # see :class:`geonode.maps.models.MapLayerManager`

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
 
    def source_config(self):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = json.loads(self.source_params)
        except Exception:
            cfg = dict(ptype="gxp_wmscsource", restUrl="/gs/rest")

        if self.ows_url: cfg["url"] = self.ows_url

        return cfg

    def layer_config(self):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """
        try:
            cfg = json.loads(self.layer_params)
        except Exception: 
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
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),layer.title)
        else: 
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)
