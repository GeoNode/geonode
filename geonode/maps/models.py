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
import json
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.core.cache import cache

from geonode.layers.models import Layer
from geonode.compat import ensure_string
from geonode.base.models import ResourceBase, resourcebase_post_save
from geonode.maps.signals import map_changed_signal
from geonode.security.utils import remove_object_permissions
from geonode.client.hooks import hookset
from geonode.utils import (GXPMapBase,
                           GXPLayerBase,
                           layer_from_viewer_config,
                           default_map_config)

from geonode import geoserver, qgis_server  # noqa
from geonode.utils import check_ogc_backend

from deprecated import deprecated
from pinax.ratings.models import OverallRating

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

    def __str__(self):
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
        return Layer.objects.filter(alternate__in=layer_names) | \
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
                layer = Layer.objects.get(alternate=map_layer.name)
                layers.append(layer)
            else:
                pass

        if layer_filter:
            layers = [lyr for lyr in layers if layer_filter(lyr)]

        # the readme text will appear in a README file in the zip
        readme = (
            "Title: %s\nAuthor: %s\nAbstract: %s\n"
        ) % (self.title, self.poc, self.abstract)
        if self.license:
            readme += f"License: {self.license}"
            if self.license.url:
                readme += f" ({self.license.url})"
            readme += "\n"
        if self.constraints_other:
            readme += f"Additional constraints: {self.constraints_other}\n"

        def layer_json(lyr):
            return {
                "name": lyr.alternate,
                "service": lyr.service_type if hasattr(lyr, 'service_type') else "QGIS Server",
                "serviceURL": "",
                "metadataURL": ""
            }

        map_config = {
            # the title must be provided and is used for the zip file name
            "map": {"readme": readme, "title": self.title},
            "layers": [layer_json(lyr) for lyr in layers]
        }

        return json.dumps(map_config)

    def update_from_viewer(self, conf, context=None):
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.

        This method automatically persists to the database!
        """

        template_name = hookset.update_from_viewer(conf, context=context)
        if not isinstance(context, dict):
            try:
                context = json.loads(ensure_string(context))
            except Exception:
                pass

        conf = context.get("config", {})
        if not isinstance(conf, dict) or isinstance(conf, bytes):
            try:
                conf = json.loads(ensure_string(conf))
            except Exception:
                conf = {}

        about = conf.get("about", {})
        self.title = conf.get("title", about.get("title", ""))
        self.abstract = conf.get("abstract", about.get("abstract", ""))

        _map = conf.get("map", {})
        center = _map.get("center", settings.DEFAULT_MAP_CENTER)
        self.zoom = _map.get("zoom", settings.DEFAULT_MAP_ZOOM)

        if isinstance(center, dict):
            self.center_x = center.get('x')
            self.center_y = center.get('y')
        else:
            self.center_x, self.center_y = center

        projection = _map.get("projection", settings.DEFAULT_MAP_CRS)
        bbox = _map.get("bbox", None)

        if bbox:
            self.set_bounds_from_bbox(bbox, projection)
        else:
            self.set_bounds_from_center_and_zoom(
                self.center_x,
                self.center_y,
                self.zoom)

        if self.projection is None or self.projection == '':
            self.projection = projection

        if self.uuid is None or self.uuid == '':
            self.uuid = str(uuid.uuid1())

        def source_for(layer):
            try:
                return conf["sources"][layer["source"]]
            except Exception:
                if 'url' in layer:
                    return {'url': layer['url']}
                else:
                    return {}

        layers = [lyr for lyr in _map.get("layers", [])]
        layer_names = set(lyr.alternate for lyr in self.local_layers)

        self.layer_set.all().delete()
        self.keywords.add(*_map.get('keywords', []))

        for ordering, layer in enumerate(layers):
            self.layer_set.add(
                layer_from_viewer_config(
                    self.id, MapLayer, layer, source_for(layer), ordering
                ))

        self.save(notify=True)

        if layer_names != set(lyr.alternate for lyr in self.local_layers):
            map_changed_signal.send_robust(sender=self, what_changed='layers')

        return template_name

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return reverse('map_detail', None, [str(self.id)])

    def get_bbox_from_layers(self, layers):
        """
        Calculate the bbox from a given list of Layer objects

        bbox format: [xmin, xmax, ymin, ymax]
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
        self.projection = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
        self.zoom = 0
        self.center_x = 0
        self.center_y = 0

        if self.uuid is None or self.uuid == '':
            self.uuid = str(uuid.uuid1())

        DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(None)

        _layers = []
        for layer in layers:
            if not isinstance(layer, Layer):
                try:
                    layer = Layer.objects.get(alternate=layer)
                except ObjectDoesNotExist:
                    raise Exception(
                        f'Could not find layer with name {layer}')

            if not user.has_perm(
                    'base.view_resourcebase',
                    obj=layer.resourcebase_ptr):
                # invisible layer, skip inclusion or raise Exception?
                logger.error(
                    f'User {user} tried to create a map with layer {layer} without having premissions')
            else:
                _layers.append(layer)

        # Set bounding box based on all layers extents.
        # bbox format: [xmin, xmax, ymin, ymax]
        bbox = self.get_bbox_from_layers(_layers)
        self.set_bounds_from_bbox(bbox, self.projection)

        # Save the map in order to create an id in the database
        # used below for the maplayers.
        self.save()

        if _layers and len(_layers) > 0:
            index = 0
            for layer in _layers:
                MapLayer.objects.create(
                    map=self,
                    name=layer.alternate,
                    ows_url=layer.get_ows_url(),
                    stack_order=index,
                    visibility=True
                )
                index += 1

        # Save again to persist the zoom and bbox changes and
        # to generate the thumbnail.
        self.set_missing_info()
        self.save(notify=True)

    @property
    def sender(self):
        return None

    @property
    def class_name(self):
        return self.__class__.__name__

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
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.geoserver.helpers import gs_catalog, ogc_server_settings
            lg_name = '%s_%d' % (slugify(self.title), self.id)
            try:
                return {
                    'catalog': gs_catalog.get_layergroup(lg_name),
                    'ows': ogc_server_settings.ows
                }
            except Exception:
                return {
                    'catalog': None,
                    'ows': ogc_server_settings.ows
                }
        else:
            return None

    @deprecated(version='2.10.1', reason="APIs have been changed on geospatial service")
    def publish_layer_group(self):
        """
        Publishes local map layers as WMS layer group on local OWS.
        """
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
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
                layer = Layer.objects.get(alternate=ml.name)
                style = ml.styles or getattr(layer.default_style, 'name', '')
                layers.append(layer)
                lg_styles.append(style)
        lg_layers = [lyr.name for lyr in layers]

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

    map = models.ForeignKey(Map, related_name="layer_set", on_delete=models.CASCADE)
    # The map containing this layer

    stack_order = models.IntegerField(_('stack order'))
    # The z-index of this layer in the map; layers with a higher stack_order will
    # be drawn on top of others.

    format = models.TextField(
        _('format'),
        null=True,
        blank=True)
    # The content_type of the image format to use for tiles (image/png, image/jpeg,
    # image/gif...)

    name = models.TextField(_('name'), null=True)
    # The name of the layer to load.

    store = models.TextField(_('store'), null=True)

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    opacity = models.FloatField(_('opacity'), default=1.0)
    # The opacity with which to render this layer, on a scale from 0 to 1.

    styles = models.TextField(
        _('styles'),
        null=True,
        blank=True)
    # The name of the style to use for this layer (only useful for WMS layers.)

    transparent = models.BooleanField(_('transparent'), default=False)
    # A boolean value, true if we should request tiles with a transparent
    # background.

    fixed = models.BooleanField(_('fixed'), default=False)
    # A boolean value, true if we should prevent the user from dragging and
    # dropping this layer in the layer chooser.

    group = models.TextField(_('group'), null=True, blank=True)
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
            cfg = cache.get(f"layer_config{str(self.id)}_{str(0 if user is None else user.id)}")
            if cfg is not None:
                return cfg

        cfg = GXPLayerBase.layer_config(self, user=user)
        # if this is a local layer, get the attribute configuration that
        # determines display order & attribute labels
        if Layer.objects.filter(alternate=self.name).exists():
            try:
                if self.local:
                    layer = Layer.objects.get(store=self.store, alternate=self.name)
                else:
                    layer = Layer.objects.get(
                        alternate=self.name,
                        remote_service__base_url=self.ows_url)
                attribute_cfg = layer.attribute_config()
                if "ftInfoTemplate" in attribute_cfg:
                    cfg["ftInfoTemplate"] = attribute_cfg["ftInfoTemplate"]
                if "getFeatureInfo" in attribute_cfg:
                    cfg["getFeatureInfo"] = attribute_cfg["getFeatureInfo"]
                if not user.has_perm(
                        'base.view_resourcebase',
                        obj=layer.resourcebase_ptr):
                    cfg['disabled'] = True
                    cfg['visibility'] = False
            except Exception:
                # shows maplayer with pink tiles,
                # and signals that there is problem
                # TODO: clear orphaned MapLayers
                layer = None

        if self.id:
            # Create temporary cache of maplayer config, should not last too long in case
            # local layer permissions or configuration values change (default
            # is 5 minutes)
            cache.set(f"layer_config{str(self.id)}_{str(0 if user is None else user.id)}", cfg)
        return cfg

    @property
    def layer_title(self):
        title = None
        try:
            if self.local:
                if self.store:
                    title = Layer.objects.get(
                        store=self.store, alternate=self.name).title
                else:
                    title = Layer.objects.get(alternate=self.name).title
        except Exception:
            title = None
        if title is None:
            title = self.name
        return title

    @property
    def local_link(self):
        link = None
        try:
            if self.local:
                if self.store:
                    layer = Layer.objects.get(
                        store=self.store, alternate=self.name)
                else:
                    layer = Layer.objects.get(alternate=self.name)
                link = f"<a href=\"{layer.get_absolute_url()}\">{layer.title}</a>"
        except Exception:
            link = None
        if link is None:
            link = f"<span>{self.name}</span> "
        return link

    @property
    def get_legend(self):
        try:
            layer_params = json.loads(self.layer_params)

            capability = layer_params.get('capability', {})
            style_name = capability.get('style')
            if style_name:
                if ':' in style_name:
                    style_name = style_name.split(':')[1]
                href = Layer.objects.filter(title=self.layer_title).first().get_legend_url(style_name=style_name)
                return {style_name: href}
            else:
                # use the default style on layer
                layer_obj = Layer.objects.filter(alternate=self.name).first()
                if layer_obj:
                    default_style_name = layer_obj.default_style.name
                    legend_url = layer_obj.get_legend_url(style_name=default_style_name)
                    return {default_style_name: legend_url}
        except Exception as e:
            logger.exception(e)
            return None

    class Meta:
        ordering = ["stack_order"]

    def __str__(self):
        return f'{self.ows_url}?layers={self.name}'


def pre_delete_map(instance, sender, **kwrargs):
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(
        content_type=ct,
        object_id=instance.id).delete()
    remove_object_permissions(instance.get_self_resource())


signals.pre_delete.connect(pre_delete_map, sender=Map)
signals.post_save.connect(resourcebase_post_save, sender=Map)
