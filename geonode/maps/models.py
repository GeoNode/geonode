# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
import uuid

from django.conf import settings
from django.db import models
from django.db.models import signals
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.cache import cache

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, resourcebase_post_save
from geonode.maps.signals import map_changed_signal
from geonode.utils import GXPMapBase
from geonode.utils import GXPLayerBase
from geonode.utils import layer_from_viewer_config
from geonode.utils import default_map_config
from geonode.utils import num_encode
from geonode.security.models import remove_object_permissions

from agon_ratings.models import OverallRating

logger = logging.getLogger("geonode.maps.models")


class Map(ResourceBase, GXPMapBase):

    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """

    # viewer configuration
    zoom = models.IntegerField(_('zoom'))
    # The zoom level to use when initially loading this map.  Zoom levels start
    # at 0 (most zoomed out) and each increment doubles the resolution.

    projection = models.CharField(_('projection'), max_length=32)
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

    urlsuffix = models.CharField(_('Site URL'), max_length=255, blank=True)
    # Alphanumeric alternative to referencing maps by id, appended to end of
    # URL instead of id, ie http://domain/maps/someview

    featuredurl = models.CharField(
        _('Featured Map URL'),
        max_length=255,
        blank=True)
    # Full URL for featured map view, ie http://domain/someview

    def __unicode__(self):
        return '%s by %s' % (
            self.title, (self.owner.username if self.owner else "<Anonymous>"))

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
        return [layer for layer in layers]

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
                layer = Layer.objects.get(typename=map_layer.name)
                layers.append(layer)
            else:
                pass

        if layer_filter:
            layers = [l for l in layers if layer_filter(l)]

        # the readme text will appear in a README file in the zip
        readme = (
            "Title: %s\n" +
            "Author: %s\n" +
            "Abstract: %s\n"
        ) % (self.title, self.poc, self.abstract)
        if self.license:
            readme += "License: %s" % self.license
            if self.license.url:
                readme += " (%s)" % self.license.url
            readme += "\n"
        if self.constraints_other:
            readme += "Additional constraints: %s\n" % self.constraints_other

        def layer_json(lyr):
            return {
                "name": lyr.typename,
                "service": lyr.service_type,
                "serviceURL": "",
                "metadataURL": ""
            }

        map_config = {
            # the title must be provided and is used for the zip file name
            "map": {"readme": readme, "title": self.title},
            "layers": [layer_json(lyr) for lyr in layers]
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

        self.set_bounds_from_center_and_zoom(
            conf['map']['center'][0],
            conf['map']['center'][1],
            conf['map']['zoom'])

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

        self.save()

        if layer_names != set([l.typename for l in self.local_layers]):
            map_changed_signal.send_robust(sender=self, what_changed='layers')

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return reverse('geonode.maps.views.map_detail', None, [str(self.id)])

    def get_bbox_from_layers(self, layers):
        """
        Calculate the bbox from a given list of Layer objects
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

        return bbox

    def create_from_layer_list(self, user, layers, title, abstract):
        self.owner = user
        self.title = title
        self.abstract = abstract
        self.projection = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')
        self.zoom = 0
        self.center_x = 0
        self.center_y = 0
        bbox = None
        index = 0

        DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(None)

        # Save the map in order to create an id in the database
        # used below for the maplayers.
        self.save()

        for layer in layers:
            if not isinstance(layer, Layer):
                try:
                    layer = Layer.objects.get(typename=layer)
                except ObjectDoesNotExist:
                    raise Exception(
                        'Could not find layer with name %s' %
                        layer)

            if not user.has_perm(
                    'base.view_resourcebase',
                    obj=layer.resourcebase_ptr):
                # invisible layer, skip inclusion or raise Exception?
                raise Exception(
                    'User %s tried to create a map with layer %s without having premissions' %
                    (user, layer))
            MapLayer.objects.create(
                map=self,
                name=layer.typename,
                ows_url=layer.get_ows_url(),
                stack_order=index,
                visibility=True
            )

            index += 1

        # Set bounding box based on all layers extents.
        bbox = self.get_bbox_from_layers(self.local_layers)

        self.set_bounds_from_bbox(bbox)

        self.set_missing_info()

        # Save again to persist the zoom and bbox changes and
        # to generate the thumbnail.
        self.save()

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def snapshots(self):
        snapshots = MapSnapshot.objects.exclude(
            user=None).filter(
            map__id=self.map.id)
        return [snapshot for snapshot in snapshots]

    @property
    def is_public(self):
        """
        Returns True if anonymous (public) user can view map.
        """
        from guardian.shortcuts import get_anonymous_user
        user = get_anonymous_user()
        return user.has_perm(
            'base.view_resourcebase',
            obj=self.resourcebase_ptr)

    @property
    def layer_group(self):
        """
        Returns layer group name from local OWS for this map instance.
        """
        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            from geonode.geoserver.helpers import gs_catalog, ogc_server_settings
            lg_name = '%s_%d' % (slugify(self.title), self.id)
            return {
                'catalog': gs_catalog.get_layergroup(lg_name),
                'ows': ogc_server_settings.ows
                }
        else:
            return None

    def publish_layer_group(self):
        """
        Publishes local map layers as WMS layer group on local OWS.
        """
        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            from geonode.geoserver.helpers import gs_catalog
            from geoserver.layergroup import UnsavedLayerGroup as GsUnsavedLayerGroup
        else:
            raise Exception(
                'Cannot publish layer group if geonode.geoserver is not in INSTALLED_APPS')

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
        lg = self.layer_group
        if lg is None:
            lg = GsUnsavedLayerGroup(
                gs_catalog,
                lg_name,
                lg_layers,
                lg_styles,
                lg_bounds)
        else:
            lg.layers, lg.styles, lg.bounds = lg_layers, lg_styles, lg_bounds
        gs_catalog.save(lg)
        return lg_name

    class Meta(ResourceBase.Meta):
        pass


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

    format = models.CharField(
        _('format'),
        null=True,
        max_length=200,
        blank=True)
    # The content_type of the image format to use for tiles (image/png, image/jpeg,
    # image/gif...)

    name = models.CharField(_('name'), null=True, max_length=200)
    # The name of the layer to load.

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    opacity = models.FloatField(_('opacity'), default=1.0)
    # The opacity with which to render this layer, on a scale from 0 to 1.

    styles = models.CharField(
        _('styles'),
        null=True,
        max_length=200,
        blank=True)
    # The name of the style to use for this layer (only useful for WMS layers.)

    transparent = models.BooleanField(_('transparent'), default=False)
    # A boolean value, true if we should request tiles with a transparent
    # background.

    fixed = models.BooleanField(_('fixed'), default=False)
    # A boolean value, true if we should prevent the user from dragging and
    # dropping this layer in the layer chooser.

    group = models.CharField(_('group'), null=True, max_length=200, blank=True)
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

    def layer_config(self, user=None):
        # Try to use existing user-specific cache of layer config
        if self.id:
            cfg = cache.get("layer_config" +
                            str(self.id) +
                            "_" +
                            str(0 if user is None else user.id))
            if cfg is not None:
                return cfg

        cfg = GXPLayerBase.layer_config(self, user=user)
        # if this is a local layer, get the attribute configuration that
        # determines display order & attribute labels
        if Layer.objects.filter(typename=self.name).exists():
            try:
                if self.local:
                    layer = Layer.objects.get(typename=self.name)
                else:
                    layer = Layer.objects.get(
                        typename=self.name,
                        service__base_url=self.ows_url)
                attribute_cfg = layer.attribute_config()
                if "getFeatureInfo" in attribute_cfg:
                    cfg["getFeatureInfo"] = attribute_cfg["getFeatureInfo"]
                if not user.has_perm(
                        'base.view_resourcebase',
                        obj=layer.resourcebase_ptr):
                    cfg['disabled'] = True
                    cfg['visibility'] = False
            except:
                # shows maplayer with pink tiles,
                # and signals that there is problem
                # TODO: clear orphaned MapLayers
                layer = None

        if self.id:
            # Create temporary cache of maplayer config, should not last too long in case
            # local layer permissions or configuration values change (default
            # is 5 minutes)
            cache.set("layer_config" +
                      str(self.id) +
                      "_" +
                      str(0 if user is None else user.id), cfg)
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
            link = "<a href=\"%s\">%s</a>" % (
                layer.get_absolute_url(), layer.title)
        else:
            link = "<span>%s</span> " % self.name
        return link

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)


def pre_delete_map(instance, sender, **kwrargs):
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(
        content_type=ct,
        object_id=instance.id).delete()
    remove_object_permissions(instance.get_self_resource())


class MapSnapshot(models.Model):
    map = models.ForeignKey(Map, related_name="snapshot_set")
    """
    The ID of the map this snapshot was generated from.
    """

    config = models.TextField(_('JSON Configuration'))
    """
    Map configuration in JSON format
    """

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the snapshot was created.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    """
    The user who created the snapshot.
    """

    def json(self):
        return {
            "map": self.map.id,
            "created": self.created_dttm.isoformat(),
            "user": self.user.username if self.user else None,
            "url": num_encode(self.id)
        }


signals.pre_delete.connect(pre_delete_map, sender=Map)
signals.post_save.connect(resourcebase_post_save, sender=Map)
