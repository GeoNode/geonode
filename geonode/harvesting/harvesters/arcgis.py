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
    FEATURE_SERVICE = "FeatureServer"
    GEOCODE_SERVICE = "GeocodeServer"
    GEOPROCESSING_SERVICE = "GPServer"
    GEOMETRY_SERVICE = "GeometryServer"
    IMAGE_SERVICE = "ImageServer"
    NETWORK_SERVICE = "NAServer"
    GEODATA_SERVICE = "GeoDataServer"
    GLOBE_SERVICE = "GlobeServer"
    MOBILE_SERVICE = "MobileServer"


def parse_remote_url(url: str) -> typing.Tuple[str, typing.Optional[str], typing.Optional[str]]:
    """Parse the input url into the ArcGIS REST catalog URL and any service name."""
    url_fragments = url.partition("/rest/services")
    catalog_url = "".join(url_fragments[:2])
    possible_service_name, other = url_fragments[-1].strip("/").partition("/")[::2]
    if possible_service_name != "":
        service_name = possible_service_name
        service_type = other.partition("/")[0]
    else:
        service_name = None
        service_type = None

    return catalog_url, service_name, service_type


class ArcgisServiceResourceExtractor(abc.ABC):
    """Abstract base class with the methods that must be reimplemented
    in order to add support for additional ArcGIS REST services"""

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

    @classmethod
    @abc.abstractmethod
    def from_resource_url(cls, resource_url: str):
        """Create a new instance from the harvestable resource url"""


class ArcgisMapServiceResourceExtractor(ArcgisServiceResourceExtractor):
    service: arcrest.MapService
    http_session: requests.Session
    _cached_resources: typing.Optional[typing.List[base.BriefRemoteResource]]

    def __init__(self, service: arcrest.MapService):
        super().__init__(service)
        self.http_session = requests.Session()
        self._cached_resources = None

    @classmethod
    def from_resource_url(cls, resource_url: str):
        service_url = resource_url.strip("/").rpartition("/")[0]
        service_type = service_url.rpartition("/")[-1]
        service_class = {
            ArcgisServiceType.MAP_SERVICE: arcrest.MapService,
            ArcgisServiceType.IMAGE_SERVICE: arcrest.ImageService
        }[ArcgisServiceType(service_type)]
        service = service_class(service_url)
        return cls(service)

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
        response = self.http_session.get(
            harvestable_resource.unique_identifier,
            params={"f": "json"}
        )
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
                result.extend(self._list_sub_layers(arc_layer))
        except HTTPError:
            logger.exception(msg="Could not list resources")
        return result

    def _list_sub_layers(self, arc_layer: arcrest.MapLayer) -> typing.List[base.BriefRemoteResource]:
        result = []
        for sub_layer in arc_layer.subLayers:
            if arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value:
                result.append(self._parse_brief_layer(sub_layer))
            result.extend(self._list_sub_layers(sub_layer))
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
            identification=resourcedescriptor.RecordIdentification(
                name=name,
                title=name,
                abstract=layer_representation.get("description", ""),
                other_constraints=layer_representation.get("copyrightTest", ""),
                spatial_extent=spatial_extent,
            ),
            distribution=resourcedescriptor.RecordDistribution(
                link_url=harvestable_resource.unique_identifier,
                wms_url=None,
                wfs_url=None,
                wcs_url=None,
                thumbnail_url=None,
                download_url=None,
                embed_url=None
            ),
            reference_systems=[epsg_code],
            additional_parameters={"service": self.service.__service_type__},
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

    @classmethod
    def from_resource_url(cls, resource_url: str):
        pass

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


def get_resource_extractor(
        harvestable_resource: models.HarvestableResource
) -> typing.Optional[ArcgisServiceResourceExtractor]:
    service_type_name = parse_remote_url(harvestable_resource.unique_identifier)[-1]
    extractor_class = {
        ArcgisServiceType.MAP_SERVICE: ArcgisMapServiceResourceExtractor,
        ArcgisServiceType.IMAGE_SERVICE: ArcgisImageServiceResourceExtractor
    }.get(ArcgisServiceType(service_type_name))
    if extractor_class is not None:
        result = extractor_class.from_resource_url(harvestable_resource.unique_identifier)
    else:
        result = None
    return result


# here are some test servers for development:
# https://pro-ags2.dfs.un.org/arcgis/rest/services/UNMISS/UNMISS_Road_Rehabilitation/MapServer
# http://sit.cittametropolitana.na.it/arcgis/rest/services/CTR2011/MapServer/
# https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer
# https://carto.nationalmap.gov/arcgis/rest/services/transportation/MapServer
# https://sampleserver6.arcgisonline.com/arcgis/rest/services/
class ArcgisHarvesterWorker(base.BaseHarvesterWorker):
    harvest_map_services: bool
    harvest_image_services: bool
    resource_title_filter: typing.Optional[str]
    service_names_filter: typing.Optional[typing.List[str]]

    http_session: requests.Session
    _arc_catalog: typing.Optional[arcrest.Catalog]
    _relevant_service_extractors: typing.Optional[
        typing.List[
            typing.Union[ArcgisMapServiceResourceExtractor, ArcgisImageServiceResourceExtractor]
        ]
    ]
    _supported_service_types = {
        ArcgisServiceType.MAP_SERVICE: ArcgisMapServiceResourceExtractor,
        ArcgisServiceType.IMAGE_SERVICE: ArcgisImageServiceResourceExtractor,
    }

    def __init__(
            self,
            remote_url: str,
            harvester_id: int,
            harvest_map_services: bool = True,
            harvest_image_services: bool = True,
            resource_title_filter: typing.Optional[str] = True,
            service_names_filter: typing.Optional[typing.List[str]] = None
    ) -> None:
        catalog_url, service_name, service_type_name = parse_remote_url(remote_url)
        if service_name is not None:
            names_filter = [service_name] + (service_names_filter or [])
        else:
            names_filter = service_names_filter
        if service_name is not None:
            service = ArcgisServiceType(service_type_name)
            harvest_maps = (service == ArcgisServiceType.MAP_SERVICE) or harvest_map_services
            harvest_images = (service == ArcgisServiceType.IMAGE_SERVICE) or harvest_image_services
        else:
            harvest_maps = harvest_map_services
            harvest_images = harvest_image_services
        super().__init__(catalog_url, harvester_id)
        self.http_session = requests.Session()
        self.harvest_map_services = harvest_maps
        self.harvest_image_services = harvest_images
        self.resource_title_filter = resource_title_filter
        self.service_names_filter = names_filter
        self._arc_catalog = None
        self._relevant_service_extractors = None

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, harvester: "Harvester"):
        return cls(
            remote_url=harvester.remote_url,
            harvester_id=harvester.pk,
            harvest_map_services=harvester.harvester_type_specific_configuration.get(
                "harvest_map_service", True),
            harvest_image_services=harvester.harvester_type_specific_configuration.get(
                "harvest_image_service", True),
            resource_title_filter=harvester.harvester_type_specific_configuration.get(
                "resource_title_filter"),
            service_names_filter=harvester.harvester_type_specific_configuration.get(
                "service_names_filter"
            )
        )

    @classmethod
    def get_extra_config_schema(cls) -> typing.Optional[typing.Dict]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://geonode.org/harvesting/geonode-arcgis-rest-harvester.schema.json"),
            "title": "ArcGIS REST harvester config",
            "description": (
                "A jsonschema for validating configuration option for GeoNode's "
                "remote ArcGIS REST services harvester"
            ),
            "type": "object",
            "properties": {
                "harvest_map_services": {
                    "type": "boolean",
                    "default": True
                },
                "harvest_image_services": {
                    "type": "boolean",
                    "default": True
                },
                "resource_title_filter": {
                    "type": "string",
                },
                "service_names_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    }
                },
            },
            "additionalProperties": False,
        }

    @property
    def arc_catalog(self):
        if self._arc_catalog is None:
            try:
                self._arc_catalog = arcrest.Catalog(self.remote_url)
            except (json.JSONDecodeError, URLError, HTTPError):
                logger.exception(f"Could not connect to ArcGIS REST server at {self.remote_url!r}")
        return self._arc_catalog

    def _get_relevant_services(self) -> typing.List[
        typing.Union[
            ArcgisMapServiceResourceExtractor,
            ArcgisImageServiceResourceExtractor
        ]
    ]:
        if self._relevant_service_extractors is None:
            result = []
            relevant_service_names = self.service_names_filter or self.arc_catalog.servicenames
            for service_name in relevant_service_names:
                service = self.arc_catalog[service_name]
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
            self._relevant_service_extractors = result
        return self._relevant_service_extractors

    def get_num_available_resources(self) -> int:
        result = 0
        for service_extractor in self._get_relevant_services():
            result += service_extractor.get_num_resources()
        return result

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        result = []
        # NOTE: Since ArcGIS REST services work in a nested fashion we are
        # not able to paginate the underlying results. As such, we resort to
        # processing all resources sequentially. This means we only care about
        # `offset=0` and explicitly return an empty list when the supplied
        # offset is different.
        if offset == 0:
            for service_extractor in self._get_relevant_services():
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
        extractor = get_resource_extractor(harvestable_resource)
        return extractor.get_resource(harvestable_resource)


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

