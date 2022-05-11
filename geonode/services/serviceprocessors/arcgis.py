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
import logging
import traceback

from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify, safe

from geonode import GeoNodeException
from geonode.base.bbox_utils import BBOXHelper
from geonode.harvesting.models import Harvester

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

    def __init__(self, url, geonode_service_id=None):
        base.ServiceHandlerBase.__init__(self, url, geonode_service_id)
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

    def probe(self):
        try:
            return True if len(self.parsed_service._json_struct) > 0 else False
        except Exception:
            return False

    def create_cascaded_store(self, service):
        return None

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance

        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile

        """
        with transaction.atomic():
            instance = models.Service.objects.create(
                uuid=str(uuid4()),
                base_url=self.url,
                type=self.service_type,
                method=self.indexing_method,
                owner=owner,
                metadata_only=True,
                version=str(self.parsed_service._json_struct.get("currentVersion", 0.0)).encode("utf-8", "ignore").decode('utf-8'),
                name=self.name,
                title=self.title,
                abstract=str(self.parsed_service._json_struct.get("serviceDescription")).encode("utf-8", "ignore").decode('utf-8') or _(
                    "Not provided")
            )
            service_harvester = Harvester.objects.create(
                name=self.name,
                default_owner=owner,
                scheduling_enabled=False,
                remote_url=instance.service_url,
                delete_orphan_resources_automatically=True,
                harvester_type=enumerations.HARVESTER_TYPES[self.service_type],
                harvester_type_specific_configuration=self.get_harvester_configuration_options()
            )
            if service_harvester.update_availability():
                service_harvester.initiate_update_harvestable_resources()
            else:
                logger.exception(GeoNodeException("Could not reach remote endpoint."))
            instance.harvester = service_harvester

        self.geonode_service_id = instance.id
        return instance

    def get_keywords(self):
        return self.parsed_service._json_struct.get("capabilities", "").split(",")

    def get_harvester_configuration_options(self):
        return {
            "harvest_map_services": True,
            "harvest_image_services": False
        }

    def _parse_datasets(self, layers):
        map_datasets = []
        for lyr in layers:
            map_datasets.append(self._dataset_meta(lyr))
            map_datasets.extend(self._parse_datasets(lyr.subLayers))
        return map_datasets

    def _dataset_meta(self, layer):
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

    def _offers_geonode_projection(self, srs):
        geonode_projection = getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857")
        return geonode_projection in f"EPSG:{srs}"

    def _get_indexed_dataset_fields(self, dataset_meta):
        srs = f"EPSG:{dataset_meta.extent.spatialReference.wkid}"
        bbox = utils.decimal_encode([dataset_meta.extent.xmin,
                                     dataset_meta.extent.ymin,
                                     dataset_meta.extent.xmax,
                                     dataset_meta.extent.ymax])
        typename = slugify(f"{dataset_meta.id}-{''.join(c for c in dataset_meta.title if ord(c) < 128)}")
        return {
            "name": dataset_meta.title,
            "store": self.name,
            "subtype": "remote",
            "workspace": "remoteWorkspace",
            "typename": typename,
            "alternate": f"{slugify(self.url)}:{dataset_meta.id}",
            "title": dataset_meta.title,
            "abstract": dataset_meta.abstract,
            "bbox_polygon": BBOXHelper.from_xy([bbox[0], bbox[2], bbox[1], bbox[3]]).as_polygon(),
            "srid": srs,
            "keywords": ['ESRI', 'ArcGIS REST MapServer', dataset_meta.title],
        }


class ArcImageServiceHandler(ArcMapServiceHandler):
    """Remote service handler for ESRI:ArcGIS:ImageService services"""

    service_type = enumerations.REST_IMG

    def __init__(self, url):
        ArcMapServiceHandler.__init__(self, url)
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

    def get_harvester_configuration_options(self):
        return {
            "harvest_map_services": False,
            "harvest_image_services": True
        }
