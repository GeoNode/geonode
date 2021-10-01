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

from geonode.layers.models import Dataset
from geonode.base.bbox_utils import BBOXHelper

# from geonode.harvesting.models import Harvester

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
                online_resource=self.parsed_service.url
            )
            # TODO: once the ArcGIS Harvester will be available
            # service_harvester = Harvester.objects.create(
            #     name=self.name,
            #     default_owner=owner,
            #     remote_url=instance.service_url,
            #     harvester_type=enumerations.HARVESTER_TYPES[self.type]
            # )
            # service_harvester.update_availability()
            # service_harvester.initiate_update_harvestable_resources()
            # instance.harvester = service_harvester

        self.geonode_service_id = instance.id
        return instance

    def get_keywords(self):
        return self.parsed_service._json_struct.get("capabilities", "").split(",")

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

    def _harvest_resource(self, dataset_meta, geonode_service):
        resource_fields = self._get_indexed_dataset_fields(dataset_meta)
        keywords = resource_fields.pop("keywords")
        existance_test_qs = Dataset.objects.filter(
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
        geonode_dataset = self._create_dataset(
            geonode_service, **resource_fields)
        self._create_dataset_service_link(geonode_service, geonode_dataset)

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
