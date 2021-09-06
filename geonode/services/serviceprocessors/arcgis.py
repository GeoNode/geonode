#########################################################################
#
# Copyright (C) 2018 OSGeo
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
"""Utilities for enabling ESRI:ArcGIS:MapServer and ESRI:ArcGIS:ImageServer remote services in geonode."""
import os
import re
import logging
import traceback

from uuid import uuid4

from django.conf import settings
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify, safe

from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.base.bbox_utils import BBOXHelper

from arcrest import MapService as ArcMapService, ImageService as ArcImageService

from .. import enumerations
from ..enumerations import INDEXED
from .. import models
from .. import utils
from . import base

from collections import namedtuple

logger = logging.getLogger(__name__)


MapLayer = namedtuple("MapLayer",
                      "id, \
                      title, \
                      abstract, \
                      type, \
                      geometryType, \
                      copyrightText, \
                      extent, \
                      fields, \
                      minScale, \
                      maxScale")


class ArcMapServiceHandler(base.ServiceHandlerBase):
    """Remote service handler for ESRI:ArcGIS:MapServer services"""

    service_type = enumerations.REST_MAP

    def __init__(self, url):
        base.ServiceHandlerBase.__init__(self, url)
        self.proxy_base = None
        self.url = url
        extent, srs = utils.get_esri_extent(self.parsed_service)
        try:
            _sname = utils.get_esri_service_name(self.url)
            _title_safe = safe(os.path.basename(os.path.normpath(_sname)))
            _title = _title_safe.replace('_', ' ').strip()
        except Exception:
            traceback.print_exc()
            _title = self.parsed_service.mapName
        if len(_title) == 0:
            _title = utils.get_esri_service_name(self.url)
        # wkt_geometry = utils.bbox2wktpolygon([
        #     extent['xmin'],
        #     extent['ymin'],
        #     extent['xmax'],
        #     extent['ymax']
        # ])

        self.indexing_method = INDEXED
        self.name = slugify(self.url)[:255]
        self.title = str(_title).encode("utf-8", "ignore").decode('utf-8')

    @property
    def parsed_service(self):
        return ArcMapService(self.url)

    def create_cascaded_store(self, service):
        return None

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance

        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile

        """
        instance = models.Service(
            uuid=str(uuid4()),
            base_url=self.url,
            proxy_base=self.proxy_base,
            type=self.service_type,
            method=self.indexing_method,
            owner=owner,
            parent=parent,
            metadata_only=True,
            version=str(self.parsed_service._json_struct.get("currentVersion", 0.0)).encode("utf-8", "ignore").decode('utf-8'),
            name=self.name,
            title=self.title,
            abstract=str(self.parsed_service._json_struct.get("serviceDescription")).encode("utf-8", "ignore").decode('utf-8') or _(
                "Not provided"),
            online_resource=self.parsed_service.url,
        )
        return instance

    def get_keywords(self):
        return self.parsed_service._json_struct.get("capabilities", "").split(",")

    def get_resource(self, resource_id):
        ll = None
        try:
            ll = self.parsed_service.layers[int(resource_id)]
        except Exception as e:
            logger.exception(e)
            for layer in self.parsed_service.layers:
                try:
                    if int(layer.id) == int(resource_id):
                        ll = layer
                        break
                except Exception as e:
                    logger.exception(e)

        return self._layer_meta(ll) if ll else None

    def get_resources(self):
        """Return an iterable with the service's resources.

        For WMS we take into account that some layers are just logical groups
        of metadata and do not return those.

        """
        try:
            return self._parse_layers(self.parsed_service.layers)
        except Exception:
            traceback.print_exc()
            return None

    def _parse_layers(self, layers):
        map_layers = []
        for lyr in layers:
            map_layers.append(self._layer_meta(lyr))
            map_layers.extend(self._parse_layers(lyr.subLayers))
        return map_layers

    def _layer_meta(self, layer):
        _ll_keys = [
            'id',
            'title',
            'abstract',
            'type',
            'geometryType',
            'copyrightText',
            'extent',
            'fields',
            'minScale',
            'maxScale'
        ]
        _ll = {}
        if isinstance(layer, dict):
            for _key in _ll_keys:
                _ll[_key] = layer[_key] if _key in layer else None
        else:
            for _key in _ll_keys:
                _ll[_key] = getattr(layer, _key, None)
        if not _ll['title'] and getattr(layer, 'name'):
            _ll['title'] = getattr(layer, 'name')
        return MapLayer(**_ll)

    def _harvest_resource(self, layer_meta, geonode_service):
        resource_fields = self._get_indexed_layer_fields(layer_meta)
        keywords = resource_fields.pop("keywords")
        existance_test_qs = Layer.objects.filter(
            name=resource_fields["name"],
            store=resource_fields["store"],
            workspace=resource_fields["workspace"]
        )
        if existance_test_qs.exists():
            raise RuntimeError(
                f"Resource {resource_fields['name']} has already been harvested")
        resource_fields["keywords"] = keywords
        resource_fields["is_approved"] = True
        resource_fields["is_published"] = True
        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            resource_fields["is_approved"] = False
            resource_fields["is_published"] = False
        geonode_layer = self._create_layer(
            geonode_service, **resource_fields)
        self._create_layer_service_link(geonode_layer)

    def harvest_resource(self, resource_id, geonode_service):
        """Harvest a single resource from the service

        This method will try to create new ``geonode.layers.models.Layer``
        instance (and its related objects too).

        :arg resource_id: The resource's identifier
        :type resource_id: str
        :arg geonode_service: The already saved service instance
        :type geonode_service: geonode.services.models.Service

        """
        layer_meta = self.get_resource(resource_id)
        if layer_meta:
            self._harvest_resource(layer_meta, geonode_service)
        else:
            raise RuntimeError(
                f"Resource {resource_id} cannot be harvested")

    def has_resources(self):
        try:
            return True if len(self.parsed_service.layers) > 0 else False
        except Exception:
            traceback.print_exc()
            return False

    def _offers_geonode_projection(self, srs):
        geonode_projection = getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857")
        return geonode_projection in f"EPSG:{srs}"

    def _get_indexed_layer_fields(self, layer_meta):
        srs = f"EPSG:{layer_meta.extent.spatialReference.wkid}"
        bbox = utils.decimal_encode([layer_meta.extent.xmin,
                                     layer_meta.extent.ymin,
                                     layer_meta.extent.xmax,
                                     layer_meta.extent.ymax])
        typename = slugify(f"{layer_meta.id}-{''.join(c for c in layer_meta.title if ord(c) < 128)}")
        return {
            "name": layer_meta.title,
            "store": self.name,
            "storeType": "remoteStore",
            "workspace": "remoteWorkspace",
            "typename": typename,
            "alternate": f"{slugify(self.url)}:{layer_meta.id}",
            "title": layer_meta.title,
            "abstract": layer_meta.abstract,
            "bbox_polygon": BBOXHelper.from_xy([bbox[0], bbox[2], bbox[1], bbox[3]]).as_polygon(),
            "srid": srs,
            "keywords": ['ESRI', 'ArcGIS REST MapServer', layer_meta.title],
        }

    def _create_layer(self, geonode_service, **resource_fields):
        # bear in mind that in ``geonode.layers.models`` there is a
        # ``pre_save_layer`` function handler that is connected to the
        # ``pre_save`` signal for the Layer model. This handler does a check
        # for common fields (such as abstract and title) and adds
        # sensible default values
        keywords = resource_fields.pop("keywords") or []
        geonode_layer = Layer(
            owner=geonode_service.owner,
            remote_service=geonode_service,
            uuid=str(uuid4()),
            **resource_fields
        )
        srid = geonode_layer.srid
        bbox_polygon = geonode_layer.bbox_polygon
        geonode_layer.full_clean()
        geonode_layer.save(notify=True)
        geonode_layer.keywords.add(*keywords)
        geonode_layer.set_default_permissions()
        if bbox_polygon and srid:
            try:
                # Dealing with the BBOX: this is a trick to let GeoDjango storing original coordinates
                Layer.objects.filter(id=geonode_layer.id).update(
                    bbox_polygon=bbox_polygon, srid='EPSG:4326')
                match = re.match(r'^(EPSG:)?(?P<srid>\d{4,6})$', str(srid))
                bbox_polygon.srid = int(match.group('srid')) if match else 4326
                Layer.objects.filter(id=geonode_layer.id).update(
                    ll_bbox_polygon=bbox_polygon, srid=srid)
            except Exception as e:
                logger.error(e)

            # Refresh from DB
            geonode_layer.refresh_from_db()
        return geonode_layer

    def _create_layer_thumbnail(self, geonode_layer):
        """Create a thumbnail with a WMS request."""
        # The thumbnail generation implementation relies on WMS image retrieval, which fails for layers from ESRI
        # services (not all of them support GetCapabilities or GetCapabilities path is different from the service's
        # URL); in order to create a thumbnail for ESRI layer, a user must upload one.
        logger.debug("Skipping thumbnail execution for layer from ESRI service.")

    def _create_layer_service_link(self, geonode_layer):
        Link.objects.get_or_create(
            resource=geonode_layer.resourcebase_ptr,
            url=geonode_layer.ows_url,
            name=f"ESRI {geonode_layer.remote_service.type}: {geonode_layer.store} Service",
            defaults={
                "extension": "html",
                "name": f"ESRI {geonode_layer.remote_service.type}: {geonode_layer.store} Service",
                "url": geonode_layer.ows_url,
                "mime": "text/html",
                "link_type": f"ESRI:{geonode_layer.remote_service.type}",
            }
        )


class ArcImageServiceHandler(ArcMapServiceHandler):
    """Remote service handler for ESRI:ArcGIS:ImageService services"""

    service_type = enumerations.REST_IMG

    def __init__(self, url):
        ArcMapServiceHandler.__init__(self, url)
        self.proxy_base = None
        self.url = url
        extent, srs = utils.get_esri_extent(self.parsed_service)
        try:
            _sname = utils.get_esri_service_name(self.url)
            _title_safe = safe(os.path.basename(os.path.normpath(_sname)))
            _title = _title_safe.replace('_', ' ').strip()
        except Exception:
            traceback.print_exc()
            _title = self.parsed_service.mapName
        if len(_title) == 0:
            _title = utils.get_esri_service_name(self.url)
        # wkt_geometry = utils.bbox2wktpolygon([
        #     extent['xmin'],
        #     extent['ymin'],
        #     extent['xmax'],
        #     extent['ymax']
        # ])

        self.indexing_method = INDEXED
        self.name = slugify(self.url)[:255]
        self.title = _title

    @property
    def parsed_service(self):
        return ArcImageService(self.url)
