#########################################################################
#
# Copyright (C) 2021 OSGeo
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

"""Harvesters for ArcGIS based remote servers."""
import abc
import enum
import json
import logging
import typing
import uuid
from urllib.error import (
    HTTPError,
    URLError,
)
import urllib.parse

import arcrest
import requests
from django.contrib.gis import geos

from geonode.layers.models import Dataset

from .. import (
    models,
    resourcedescriptor,
)

from . import base

logger = logging.getLogger(__name__)


class ArcgisRestApiLayerType(enum.Enum):
    GROUP_LAYER = "Group Layer"
    FEATURE_LAYER = "Feature Layer"


class ArcgisServiceType(enum.Enum):
    MAP_SERVICE = "MapServer"
    IMAGE_SERVICE = "ImageServer"
    FEATURE_SERVICE = "FeatureServer"


class ArcgisServiceResourceExtractor(abc.ABC):

    def __init__(self, service):
        self.service = service

    @abc.abstractmethod
    def get_num_resources(self) -> int:
        """Return the number of resources that can be extracted from the service."""

    @abc.abstractmethod
    def list_resources(self) -> typing.List[base.BriefRemoteResource]:
        """Return a list of BriefRemoteResource with the resources exposed by the service"""

    @abc.abstractmethod
    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource
    ) -> base.HarvestedResourceInfo:
        """Parse the remote resource into a HarvestedResourceInfo"""


class ArcgisMapServiceResourceExtractor(ArcgisServiceResourceExtractor):
    service: arcrest.MapService
    http_session: requests.Session
    _cached_resources: typing.Optional[typing.List[base.BriefRemoteResource]]

    def __init__(self, service: arcrest.MapService):
        super().__init__(service)
        self.http_session = requests.Session()
        self._cached_resources = None

    def get_num_resources(self) -> int:
        if self._cached_resources is None:
            self._cached_resources = self._extract_resources()
        return len(self._cached_resources)

    def list_resources(
            self,
    ) -> typing.List[base.BriefRemoteResource]:
        if self._cached_resources is None:
            self._cached_resources = self._extract_resources()
        return self._cached_resources

    def get_resource(self, harvestable_resource: models.HarvestableResource):
        url = f"{harvestable_resource.harvester.remote_url}/{harvestable_resource.unique_identifier}/"
        response = self.http_session.get(url, params={"f": "json"})
        result = None
        if response.status_code == requests.codes.ok:
            try:
                response_payload = response.json()
            except json.JSONDecodeError:
                logger.exception("Could not decode response payload as valid JSON")
            else:
                resource_descriptor = self._get_resource_descriptor(response_payload, harvestable_resource)
                result = base.HarvestedResourceInfo(
                    resource_descriptor=resource_descriptor,
                    additional_information=None
                )
        else:
            logger.error(
                f"Could not retrieve remote resource with unique "
                f"identifier {harvestable_resource.unique_identifier!r}"
            )
        return result

    def _extract_resources(self) -> typing.List[base.BriefRemoteResource]:
        result = []
        try:
            for arc_layer in self.service.layers:
                if arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value:
                    result.append(self._parse_brief_layer(arc_layer))
                result.extend(_list_sub_layers(arc_layer))
        except HTTPError:
            logger.exception(msg="Could not list resources")
        return result

    def _get_resource_descriptor(
            self,
            layer_representation: typing.Dict,
            harvestable_resource: models.HarvestableResource
    ) -> resourcedescriptor.RecordDescription:
        if harvestable_resource.geonode_resource is None:
            resource_uuid = uuid.uuid4()
        else:
            resource_uuid = uuid.UUID(harvestable_resource.geonode_resource.uuid)
        name = layer_representation["name"]
        epsg_code, spatial_extent = _parse_spatial_extent(layer_representation["extent"])
        return resourcedescriptor.RecordDescription(
            uuid=resource_uuid,
            point_of_contact=None,
            author=None,
            date_stamp=None,
            identification=resourcedescriptor.RecordIdentification(
                name=name,
                title=name,
                date=None,
                date_type=None,
                originator=None,
                graphic_overview_uri=None,
                place_keywords=None,
                other_keywords=None,
                license=None,
                abstract=layer_representation.get("description", ""),
                purpose=None,
                status=None,
                native_format=None,
                other_constraints=layer_representation.get("copyrightTest", ""),
                topic_category=None,
                supplemental_information=None,
                spatial_extent=spatial_extent,
                temporal_extent=None
            ),
            distribution=resourcedescriptor.RecordDistribution(
                link_url=f"{self.remote_url}/{layer_representation['id']}",
                wms_url=None,
                wfs_url=None,
                wcs_url=None,
                thumbnail_url=None,
                download_url=None,
                embed_url=None
            ),
            reference_systems=[epsg_code, ],
            data_quality=None,
            additional_parameters=None,
            language=None,
            character_set=None,
        )

    def _parse_brief_layer(self, arc_layer: arcrest.MapLayer) -> base.BriefRemoteResource:
        base_url = urllib.parse.urlparse(self.service.url)
        layer_path = "/".join((base_url.path.rstrip("/"), str(arc_layer.id)))
        layer_url = urllib.parse.urlunparse(
            (base_url.scheme, base_url.netloc, layer_path, "", "", ""))
        return base.BriefRemoteResource(
            unique_identifier=layer_url,
            title=arc_layer.name,
            resource_type=arc_layer.type,
        )


class ArcgisImageServiceResourceExtractor(ArcgisServiceResourceExtractor):
    service: arcrest.ImageService

    def __init__(self, service: arcrest.ImageService):
        super().__init__(service)

    def get_num_resources(self) -> int:
        return 1

    def list_resources(self) -> typing.List[base.BriefRemoteResource]:
        name = self._get_resource_name()
        unique_id = self.service.url.rpartition("?")[0].rstrip("/")
        return [
            base.BriefRemoteResource(
                unique_identifier=unique_id,
                title=name,
                resource_type="raster",
            )
        ]

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource
    ) -> base.HarvestedResourceInfo:
        pass

    def _get_resource_name(self):
        return self.service.url.rpartition("/rest/services/")[-1].partition("/ImageServer")[0]





# here are some test servers for development:
# https://pro-ags2.dfs.un.org/arcgis/rest/services/UNMISS/UNMISS_Road_Rehabilitation/MapServer
# http://sit.cittametropolitana.na.it/arcgis/rest/services/CTR2011/MapServer/
# https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer
# https://carto.nationalmap.gov/arcgis/rest/services/transportation/MapServer
# https://sampleserver6.arcgisonline.com/arcgis/rest/services/

class ArcgisRestServiceHarvesterWorker(base.BaseHarvesterWorker):
    http_session: requests.Session
    _arc_catalog: typing.Optional[arcrest.Catalog]
    _relevant_services: typing.Optional[
        typing.List[
            typing.Union[ArcgisMapServiceResourceExtractor, ArcgisImageServiceResourceExtractor]
        ]
    ]
    _supported_service_types = {
        ArcgisServiceType.MAP_SERVICE: ArcgisMapServiceResourceExtractor,
        ArcgisServiceType.IMAGE_SERVICE: ArcgisImageServiceResourceExtractor,
    }

    def __init__(self, remote_url: str, harvester_id: int) -> None:
        super().__init__(remote_url, harvester_id)
        self.remote_url = self.remote_url.rstrip("/")
        self.http_session = requests.Session()
        self._arc_catalog = None
        self._relevant_services = None

    @property
    def arc_catalog(self):
        if self._arc_catalog is None:
            try:
                self._arc_catalog = arcrest.Catalog(self.remote_url)
            except (json.JSONDecodeError, URLError, HTTPError):
                logger.exception(f"Could not connect to ArcGIS REST server at {self.remote_url!r}")
        return self._arc_catalog

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, harvester: "Harvester"):
        return cls(
            remote_url=harvester.remote_url,
            harvester_id=harvester.pk
        )

    def get_relevant_services(self) -> typing.List[
        typing.Union[
            ArcgisMapServiceResourceExtractor,
            ArcgisImageServiceResourceExtractor
        ]
    ]:
        if self._relevant_services is None:
            result = []
            for service in self.arc_catalog.services:
                try:
                    type_ = ArcgisServiceType(service.__service_type__)
                except ValueError:
                    logger.debug(f"Unrecognized service type: {service.__service_type__!r}")
                    continue
                else:
                    try:
                        extractor_class = self._supported_service_types[type_]
                    except KeyError:
                        logger.debug(f"Unsupported service type: {type_}")
                        continue
                    else:
                        result.append(extractor_class(service))
            self._relevant_services = result
        return self._relevant_services

    def get_num_available_resources(self) -> int:
        result = 0
        for service_extractor in self.get_relevant_services():
            result += service_extractor.get_num_resources()
        return result

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        result = []
        for service_extractor in self.get_relevant_services():
            result.extend(service_extractor.list_resources())
        return result

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        return self.arc_catalog is not None

    def get_geonode_resource_type(self, remote_resource_type: str) -> typing.Type:
        return Dataset

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        found_it = False
        resource_info = None
        for service_extractor in self.get_relevant_services():
            for existing_resource in service_extractor.list_resources():
                if existing_resource.unique_identifier == harvestable_resource.unique_identifier:
                    resource_info = service_extractor.get_resource(harvestable_resource)
                    found_it = True
                    break
            if found_it:
                break
        return resource_info




# ArcGIS REST APIs define different service types. The ones we are supporting are:
# - Map Service - Provides access to contents of a map hosted on a server
# - Image Service - Provides access to raster data

class ArcgisMapServiceHarvesterWorker(base.BaseHarvesterWorker):
    _arc_mapservice: typing.Optional[arcrest.MapService]
    _cached_resources: typing.List[base.BriefRemoteResource]
    http_session: requests.Session

    def __init__(self, remote_url: str, harvester_id: int) -> None:
        super().__init__(remote_url, harvester_id)
        self.remote_url = self.remote_url.rstrip("/")
        self.http_session = requests.Session()
        self._arc_mapservice = None
        self._cached_resources = []

    @property
    def arc_mapservice(self):
        if self._arc_mapservice is None:
            self._arc_mapservice = arcrest.MapService(self.remote_url)
        return self._arc_mapservice

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, harvester: "Harvester"):
        return cls(
            remote_url=harvester.remote_url,
            harvester_id=harvester.pk
        )

    def get_num_available_resources(self) -> int:
        if len(self._cached_resources) == 0:
            self.list_resources()
        return len(self._cached_resources)

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        result = []
        try:
            for arc_layer in self.arc_mapservice.layers:
                if arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value:
                    result.append(_parse__brief_layer(arc_layer))
                result.extend(_list_sub_layers(arc_layer))
        except HTTPError:
            logger.exception(msg="Could not list resources")
        self._cached_resources = result
        return result

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        try:
            self.arc_mapservice.description
        except HTTPError:
            logger.exception("Could not contact remote service")
            result = False
        else:
            result = True
        return result

    def get_geonode_resource_type(self, remote_resource_type: str) -> typing.Type:
        return Dataset

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        url = f"{self.remote_url}/{harvestable_resource.unique_identifier}/"
        response = self.http_session.get(url, params={"f": "json"})
        result = None
        if response.status_code == requests.codes.ok:
            try:
                response_payload = response.json()
            except json.JSONDecodeError:
                logger.exception("Could not decode response payload as valid JSON")
            else:
                resource_descriptor = self._get_resource_descriptor(response_payload, harvestable_resource)
                result = base.HarvestedResourceInfo(
                    resource_descriptor=resource_descriptor,
                    additional_information=None
                )
        else:
            logger.error(
                f"Could not retrieve remote resource with unique "
                f"identifier {harvestable_resource.unique_identifier!r}"
            )
        return result

    def _get_resource_descriptor(
            self,
            layer_representation: typing.Dict,
            harvestable_resource: models.HarvestableResource
    ) -> resourcedescriptor.RecordDescription:
        if harvestable_resource.geonode_resource is None:
            resource_uuid = uuid.uuid4()
        else:
            resource_uuid = uuid.UUID(harvestable_resource.geonode_resource.uuid)
        name = layer_representation["name"]
        epsg_code, spatial_extent = _parse_spatial_extent(layer_representation["extent"])
        return resourcedescriptor.RecordDescription(
            uuid=resource_uuid,
            point_of_contact=None,
            author=None,
            date_stamp=None,
            identification=resourcedescriptor.RecordIdentification(
                name=name,
                title=name,
                date=None,
                date_type=None,
                originator=None,
                graphic_overview_uri=None,
                place_keywords=None,
                other_keywords=None,
                license=None,
                abstract=layer_representation.get("description", ""),
                purpose=None,
                status=None,
                native_format=None,
                other_constraints=layer_representation.get("copyrightTest", ""),
                topic_category=None,
                supplemental_information=None,
                spatial_extent=spatial_extent,
                temporal_extent=None
            ),
            distribution=resourcedescriptor.RecordDistribution(
                link_url=f"{self.remote_url}/{layer_representation['id']}",
                wms_url=None,
                wfs_url=None,
                wcs_url=None,
                thumbnail_url=None,
                download_url=None,
                embed_url=None
            ),
            reference_systems=[epsg_code,],
            data_quality=None,
            additional_parameters=None,
            language=None,
            character_set=None,
        )


def _list_sub_layers(arc_layer: arcrest.MapLayer) -> typing.List[base.BriefRemoteResource]:
    result = []
    for sub_layer in arc_layer.subLayers:
        if arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value:
            result.append(_parse__brief_layer(sub_layer))
        result.extend(_list_sub_layers(sub_layer))
    return result


def _parse_spatial_extent(raw_extent: typing.Dict) -> typing.Tuple[str, geos.Polygon]:
    epsg_code = f"EPSG:{raw_extent.get('latestWkid', raw_extent.get('wkid'))}"
    extent = geos.Polygon.from_bbox(
        (
            raw_extent["xmin"],
            raw_extent["ymin"],
            raw_extent["xmax"],
            raw_extent["ymax"]
        )
    )
    return epsg_code, extent

