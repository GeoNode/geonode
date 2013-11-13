# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging
import math
import errno
import uuid
import httplib2
from urlparse import urlparse
import urllib

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.utils import simplejson as json
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save, resourcebase_post_delete
from geonode.maps.signals import map_changed_signal
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.utils import GXPMapBase
from geonode.utils import GXPLayerBase
from geonode.utils import layer_from_viewer_config
from geonode.utils import default_map_config
from geonode.utils import forward_mercator
from geonode.utils import http_client, ogc_server_settings

from geoserver.catalog import Catalog
from geoserver.layer import Layer as GsLayer
from geoserver.layergroup import UnsavedLayerGroup as GsUnsavedLayerGroup
from agon_ratings.models import OverallRating

logger = logging.getLogger("geonode.maps.models")

_user, _password = ogc_server_settings.credentials

class Map(ResourceBase, GXPMapBase):
    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

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

    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the map was modified.

    popular_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

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
        layer_names = MapLayer.objects.filter(map__id=self.id).values('name')
        return Layer.objects.filter(typename__in=layer_names) | \
               Layer.objects.filter(name__in=layer_names)

    def json(self, layer_filter):
        """
        Get a JSON representation of this map suitable for sending to geoserver
        for creating a download of all layers
        """
        map_layers = MapLayer.objects.filter(map=self.id)
        layers = []
        for map_layer in map_layers:
            if map_layer.local:
                layer =  Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else:
                pass

        if layer_filter:
            layers = [l for l in layers if layer_filter(l)]

        # the readme text will appear in a README file in the zip
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
            # the title must be provided and is used for the zip file name
            "map" : { "readme": readme, "title": self.title },
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

        if self.uuid is None or self.uuid == '':
            self.uuid = str(uuid.uuid1())

        def source_for(layer):
            return conf["sources"][layer["source"]]

        layers = [l for l in conf["map"]["layers"]]
        layer_names = set([l.typename for l in self.local_layers])

        for layer in self.layer_set.all():
            layer.delete()

        self.keywords.add(*conf['map'].get('keywords', []))

        for ordering, layer in enumerate(layers):
            self.layer_set.add(
                layer_from_viewer_config(
                    MapLayer, layer, source_for(layer), ordering
            ))

        self.set_bounds_from_layers(self.local_layers)

        self.save()

        if layer_names != set([l.typename for l in self.local_layers]):
            map_changed_signal.send_robust(sender=self,what_changed='layers')

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return reverse('geonode.maps.views.map_detail', None, [str(self.id)])

    def update_thumbnail(self, save=True):
        if len(self.layers) == 0:
            return
        if self.thumbnail == None:
            self.save_thumbnail(self._thumbnail_url(width=240, height=180), save)
                

    def _render_thumbnail(self, spec):
        http = httplib2.Http()
        url = "%srest/printng/render.png" % ogc_server_settings.LOCATION
        hostname = urlparse(settings.SITEURL).hostname
        params = dict(width=240, height=180, auth="%s,%s,%s" % (hostname, _user, _password))
        url = url + "?" + urllib.urlencode(params)
        http.add_credentials(_user, _password)
        netloc = urlparse(url).netloc
        http.authorizations.append(
        httplib2.BasicAuthentication(
            (_user,_password),
            netloc,
            url,
            {},
            None,
            None,
            http
        ))
        # @todo annoying but not critical
        # openlayers controls posted back contain a bad character. this seems
        # to come from a &minus; entity in the html, but it gets converted
        # to a unicode en-dash but is not uncoded properly during transmission
        # 'ignore' the error for now as controls are not being rendered...
        data = spec 
        if type(data) == unicode:
            # make sure any stored bad values are wiped out
            # don't use keyword for errors - 2.6 compat
            # though unicode accepts them (as seen below)
            data = data.encode('ASCII','ignore')
        data = unicode(data, errors='ignore').encode('UTF-8')
        try:
            resp, content = http.request(url,"POST",data,{
                'Content-type':'text/html'
            })
        except Exception:
            logging.warning('Error generating thumbnail')
            return 
        if resp.status < 200 or resp.status > 299:
            logging.warning('Error generating thumbnail %s',content)
            return 
        if len(content) == 0:
            logging.warning('Empty thumb content %s',content)
            return
        return content

    def _thumbnail_url(self, width=20, height=None):
        """ Generate a URL representing thumbnail of the layer """

        local_layers = []
        for layer in self.layers:
            if layer.local:
                local_layers.append(Layer.objects.get(typename=layer.name).typename)

        params = {
            'layers': ",".join(local_layers),
            'format': 'image/png8',
            'width': width,
        }
        if height is not None:
            params['height'] = height

        # Avoid using urllib.urlencode here because it breaks the url.
        # commas and slashes in values get encoded and then cause trouble
        # with the WMS parser.
        p = "&".join("%s=%s"%item for item in params.items())

        return '<img src="%s"/>' % (ogc_server_settings.public_url + "wms/reflect?" + p)

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

    def get_extent(self):
        """Generate minx/miny/maxx/maxy of map extent"""

        return self.bbox

    def set_bounds_from_layers(self, layers):
        """
        Calculate the bounds from a given list of Layer objects
        """
        bbox = None
        for layer in layers:

            layer_bbox = layer.bbox
            if bbox is None:
                bbox = list(layer_bbox[0:4])
            else:
                bbox[0] = min(bbox[0], layer_bbox[0])
                bbox[1] = max(bbox[1], layer_bbox[1])
                bbox[2] = min(bbox[2], layer_bbox[2])
                bbox[3] = max(bbox[3], layer_bbox[3])

        if bbox is not None:
            self.bbox_x0 = bbox[0]
            self.bbox_x1 = bbox[1]
            self.bbox_y0 = bbox[2]
            self.bbox_y1 = bbox[3]

        return bbox

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

        DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()

        layer_objects = []
        for layer in layers:
            try:
                layer = Layer.objects.get(typename=layer)
            except ObjectDoesNotExist:
                continue # Raise exception?

            if not user.has_perm('maps.view_layer', obj=layer):
                # invisible layer, skip inclusion or raise Exception?
                continue # Raise Exception

            layer_objects.append(layer)

            map_layers.append(MapLayer(
                map = self,
                name = layer.typename,
                ows_url = ogc_server_settings.public_url + "wms",
                stack_order = index,
                visibility = True
            ))

            bbox = self.set_bounds_from_layers(layer_objects)

            if bbox is not None:
                minx, miny, maxx, maxy = [float(c) for c in bbox]
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2
                (self.center_x,self.center_y) = forward_mercator((x,y))

                width_zoom = math.log(360 / (maxx - minx), 2)
                height_zoom = math.log(360 / (maxy - miny), 2)

                self.zoom = math.ceil(min(width_zoom, height_zoom))
            index += 1

        self.save()
        for bl in DEFAULT_BASE_LAYERS:
            bl.map = self
            #bl.save()

        for ml in map_layers:
            ml.map = self # update map_id after saving map
            ml.save()

        self.set_default_permissions()

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def is_public(self):
        """
        Returns True if anonymous (public) user can view map.
        """
        user = AnonymousUser()
        return user.has_perm('maps.view_map', obj=self)

    @property
    def layer_group(self):
        """
        Returns layer group name from local OWS for this map instance.
        """
        cat = Catalog(ogc_server_settings.rest, _user, _password)
        lg_name = '%s_%d' % (slugify(self.title), self.id)
        return cat.get_layergroup(lg_name)
 
    def publish_layer_group(self):
        """
        Publishes local map layers as WMS layer group on local OWS.
        """
        # temporary permission workaround: 
        # only allow public maps to be published
        if not self.is_public:
            return 'Only public maps can be saved as layer group.'

        map_layers = MapLayer.objects.filter(map=self.id)
        
        # Local Group Layer layers and corresponding styles
        layers = []
        lg_styles = []
        for ml in map_layers:
            if ml.local:
                layer = Layer.objects.get(typename=ml.name)
                style = ml.styles or getattr(layer.default_style, 'name', '')
                layers.append(layer)
                lg_styles.append(style)
        lg_layers = [l.name for l in layers]

        # Group layer bounds and name             
        lg_bounds = [str(coord) for coord in self.bbox] 
        lg_name = '%s_%d' % (slugify(self.title), self.id)

        # Update existing or add new group layer
        cat = Catalog(ogc_server_settings.rest, _user, _password)
        lg = self.layer_group
        if lg is None:
            lg = GsUnsavedLayerGroup(cat, lg_name, lg_layers, lg_styles, lg_bounds)
        else:
            lg.layers, lg.styles, lg.bounds = lg_layers, lg_styles, lg_bounds
        cat.save(lg)
        return lg_name


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

    format = models.CharField(_('format'), null=True, max_length=200, blank=True)
    # The mimetype of the image format to use for tiles (image/png, image/jpeg,
    # image/gif...)

    name = models.CharField(_('name'), null=True, max_length=200)
    # The name of the layer to load.

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    opacity = models.FloatField(_('opacity'), default=1.0)
    # The opacity with which to render this layer, on a scale from 0 to 1.

    styles = models.CharField(_('styles'), null=True,max_length=200, blank=True)
    # The name of the style to use for this layer (only useful for WMS layers.)

    transparent = models.BooleanField(_('transparent'))
    # A boolean value, true if we should request tiles with a transparent background.

    fixed = models.BooleanField(_('fixed'), default=False)
    # A boolean value, true if we should prevent the user from dragging and
    # dropping this layer in the layer chooser.

    group = models.CharField(_('group'), null=True,max_length=200, blank=True)
    # A group label to apply to this layer.  This affects the hierarchy displayed
    # in the map viewer's layer tree.

    visibility = models.BooleanField(_('visibility'), default=True)
    # A boolean value, true if this layer should be visible when the map loads.

    ows_url = models.URLField(_('ows URL'), null=True, blank=True)
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

    local = models.BooleanField(default=False)
    # True if this layer is served by the local geoserver

    def layer_config(self):
        cfg = GXPLayerBase.layer_config(self)

        # if this is a local layer, get the attribute configuration that
        # determines display order & attribute labels
        if self.local:
            if Layer.objects.filter(typename=self.name).exists():
                layer = Layer.objects.get(typename=self.name)
                attribute_cfg = layer.attribute_config()
                if "getFeatureInfo" in attribute_cfg:
                    cfg["getFeatureInfo"] = attribute_cfg["getFeatureInfo"]
            else:
                # shows maplayer with pink tiles, 
                # and signals that there is problem
                # TODO: clear orphaned MapLayers
                layer = None
        return cfg

    @property
    def layer_title(self):
        if self.local:
            title = Layer.objects.get(typename=self.name).title
        else:
            title = self.name
        return title

    @property
    def local_link(self):
        if self.local:
            layer = Layer.objects.get(typename=self.name)
            link = "<a href=\"%s\">%s</a>" % (layer.get_absolute_url(),layer.title)
        else:
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)

def pre_save_maplayer(instance, sender, **kwargs):
    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get('raw', False):
        return

    try:
        c = Catalog(ogc_server_settings.internal_rest, _user, _password)
        instance.local = isinstance(c.get_layer(instance.name),GsLayer)
    except EnvironmentError, e:
        if e.errno == errno.ECONNREFUSED:
            msg = 'Could not connect to catalog to verify if layer %s was local' % instance.name
            logger.warn(msg, e)
        else:
            raise e

def pre_delete_map(instance, sender, **kwrargs):
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(content_type = ct, object_id = instance.id).delete()

def pre_save_map(instance, sender, **kwargs):
    instance.update_thumbnail(save=False)

signals.pre_save.connect(pre_save_maplayer, sender=MapLayer)
signals.pre_delete.connect(pre_delete_map, sender=Map)
signals.pre_save.connect(pre_save_map, sender=Map)
signals.post_save.connect(resourcebase_post_save, sender=Map)
signals.post_delete.connect(resourcebase_post_delete, sender=Map)
