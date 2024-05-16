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
import re
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
from django.template.defaultfilters import slugify

from geonode.layers.enumerations import GXP_PTYPES
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

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


def parse_remote_url(url: str) -> typing.Tuple[str, typing.Optional[str], typing.Optional[str]]:
    """Parse the input url into the ArcGIS REST catalog URL and any service name."""
    url_fragments = url.partition("/rest/services")
    catalog_url = "".join(url_fragments[:2])
    service_type = None
    possible_service_name = None
    service_type_regex = re.match(r".*\/(.*Server).*", "".join(url_fragments[-1:]))
    if service_type_regex:
        for service_type_value in service_type_regex.groups():
            if ArcgisServiceType.has_value(service_type_value):
                service_type = service_type_value
                possible_service_name = "".join(url_fragments[-1:]).strip("/").partition(service_type)[0].rstrip("/")
                other = None
                break
    else:
        possible_service_name, other = url_fragments[-1].strip("/").partition("/")[::2]
    if possible_service_name is not None and possible_service_name != "":
        service_name = possible_service_name
        if not service_type and other:
            service_type = other.partition("/")[0]
    else:
        service_name = None

    return catalog_url, service_name, service_type


class ArcgisServiceResourceExtractor(abc.ABC):
    """Abstract base class with the methods that must be reimplemented
    in order to add support for additional ArcGIS REST services"""

    resource_name_filter: typing.Optional[str]
    service: typing.Type

    def __init__(self, service, resource_name_filter: typing.Optional[str] = None):
        self.service = service
        self.resource_name_filter = resource_name_filter

    @abc.abstractmethod
    def get_num_resources(self) -> int:
        """Return the number of resources that can be extracted from the service."""

    @abc.abstractmethod
    def list_resources(self) -> typing.List[base.BriefRemoteResource]:
        """Return a list of BriefRemoteResource with the resources exposed by the service"""

    @abc.abstractmethod
    def get_resource(self, harvestable_resource: models.HarvestableResource) -> base.HarvestedResourceInfo:
        """Parse the remote resource into a HarvestedResourceInfo"""

    def _is_relevant_layer(self, layer_name: str) -> bool:
        result = False
        if self.resource_name_filter is not None:
            if self.resource_name_filter.lower() in layer_name.lower():
                result = True
        else:
            result = True
        return result


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
        response = self.http_session.get(harvestable_resource.unique_identifier, params={"f": "json"})
        result = None
        if response.status_code == requests.codes.ok:
            try:
                response_payload = response.json()
            except json.JSONDecodeError:
                logger.exception("Could not decode response payload as valid JSON")
            else:
                resource_descriptor = self._get_resource_descriptor(response_payload, harvestable_resource)
                result = base.HarvestedResourceInfo(
                    resource_descriptor=resource_descriptor, additional_information=None
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
                if (
                    self._is_relevant_layer(arc_layer.name)
                    and arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value
                ):
                    result.append(self._parse_brief_layer(arc_layer))
                result.extend(self._list_sub_layers(arc_layer))
        except HTTPError:
            logger.exception(msg="Could not list resources")
        return result

    def _list_sub_layers(self, arc_layer: arcrest.MapLayer) -> typing.List[base.BriefRemoteResource]:
        result = []
        for sub_layer in arc_layer.subLayers:
            if self._is_relevant_layer(arc_layer.name) and arc_layer.type != ArcgisRestApiLayerType.GROUP_LAYER.value:
                result.append(self._parse_brief_layer(sub_layer))
            result.extend(self._list_sub_layers(sub_layer))
        return result

    def _get_resource_descriptor(
        self, layer_representation: typing.Dict, harvestable_resource: models.HarvestableResource
    ) -> resourcedescriptor.RecordDescription:
        if harvestable_resource.geonode_resource is None:
            resource_uuid = uuid.uuid4()
        else:
            resource_uuid = uuid.UUID(harvestable_resource.geonode_resource.uuid)
        _, service_name, service_type = parse_remote_url(harvestable_resource.unique_identifier)
        epsg_code, spatial_extent = _parse_spatial_extent(layer_representation["extent"])
        ows_url = harvestable_resource.harvester.remote_url
        store = slugify(ows_url)
        name = layer_representation.get("id", layer_representation.get("name", "Undefined"))
        title = layer_representation.get("name", layer_representation.get("title", "Undefined"))
        workspace = "remoteWorkspace"
        alternate = f"{workspace}:{name}"
        return resourcedescriptor.RecordDescription(
            uuid=resource_uuid,
            identification=resourcedescriptor.RecordIdentification(
                name=name,
                title=title,
                abstract=layer_representation.get("description", ""),
                other_constraints=layer_representation.get("copyrightTest", ""),
                spatial_extent=spatial_extent,
                other_keywords=[
                    "ESRI",
                    f"ArcGIS REST {self.service.__service_type__}",
                ],
            ),
            distribution=resourcedescriptor.RecordDistribution(
                link_url=harvestable_resource.unique_identifier,
                thumbnail_url=None,
            ),
            reference_systems=[epsg_code],
            additional_parameters={
                "store": store,
                "workspace": workspace,
                "alternate": alternate,
                "ows_url": ows_url,
                "ptype": GXP_PTYPES["REST_MAP"],
            },
        )

    def _parse_brief_layer(self, arc_layer: arcrest.MapLayer) -> base.BriefRemoteResource:
        base_url = urllib.parse.urlparse(self.service.url)
        layer_path = "/".join((base_url.path.rstrip("/"), str(arc_layer.id)))
        layer_url = urllib.parse.urlunparse((base_url.scheme, base_url.netloc, layer_path, "", "", ""))
        return base.BriefRemoteResource(
            unique_identifier=layer_url,
            title=arc_layer.name,
            resource_type=arc_layer.type,
        )


class ArcgisImageServiceResourceExtractor(ArcgisServiceResourceExtractor):
    service: arcrest.ImageService
    http_session: requests.Session

    def __init__(self, service: arcrest.ImageService):
        super().__init__(service)
        self.http_session = requests.Session()

    def get_num_resources(self) -> int:
        return len(self.list_resources())

    def list_resources(self) -> typing.List[base.BriefRemoteResource]:
        name = self._get_resource_name()
        if self._is_relevant_layer(name):
            unique_id = self.service.url.rpartition("?")[0].rstrip("/")
            result = [
                base.BriefRemoteResource(
                    unique_identifier=unique_id,
                    title=name,
                    resource_type="raster",
                )
            ]
        else:
            result = []
        return result

    def get_resource(self, harvestable_resource: models.HarvestableResource) -> base.HarvestedResourceInfo:
        response = self.http_session.get(harvestable_resource.unique_identifier, params={"f": "json"})
        result = None
        if response.status_code == requests.codes.ok:
            try:
                response_payload = response.json()
            except json.JSONDecodeError:
                logger.exception("Could not decode response payload as valid JSON")
            else:
                resource_descriptor = self._get_resource_descriptor(response_payload, harvestable_resource)
                result = base.HarvestedResourceInfo(
                    resource_descriptor=resource_descriptor, additional_information=None
                )
        else:
            logger.error(
                f"Could not retrieve remote resource with unique "
                f"identifier {harvestable_resource.unique_identifier!r}"
            )
        return result

    def _get_resource_name(self):
        return self.service.url.rpartition("/rest/services/")[-1].partition("/ImageServer")[0]

    def _get_resource_descriptor(
        self, layer_representation: typing.Dict, harvestable_resource: models.HarvestableResource
    ) -> resourcedescriptor.RecordDescription:
        if harvestable_resource.geonode_resource is None:
            resource_uuid = uuid.uuid4()
        else:
            resource_uuid = uuid.UUID(harvestable_resource.geonode_resource.uuid)
        _, service_name, service_type = parse_remote_url(harvestable_resource.unique_identifier)
        epsg_code, spatial_extent = _parse_spatial_extent(layer_representation["extent"])
        ows_url = harvestable_resource.harvester.remote_url
        store = slugify(ows_url)
        name = layer_representation.get("id", layer_representation.get("name", "Undefined"))
        title = layer_representation.get("name", layer_representation.get("title", "Undefined"))
        workspace = "remoteWorkspace"
        alternate = f"{workspace}:{name}"
        return resourcedescriptor.RecordDescription(
            uuid=resource_uuid,
            identification=resourcedescriptor.RecordIdentification(
                name=name,
                title=title,
                abstract=layer_representation.get("description", ""),
                other_constraints=layer_representation.get("copyrightTest", ""),
                spatial_extent=spatial_extent,
                other_keywords=[
                    "ESRI",
                    f"ArcGIS REST {self.service.__service_type__}",
                ],
            ),
            distribution=resourcedescriptor.RecordDistribution(
                link_url=harvestable_resource.unique_identifier,
                thumbnail_url=None,
            ),
            reference_systems=[epsg_code],
            additional_parameters={
                "store": store,
                "workspace": workspace,
                "alternate": alternate,
                "ows_url": ows_url,
                "ptype": GXP_PTYPES["REST_IMG"],
            },
        )


def get_resource_extractor(resource_unique_identifier: str) -> typing.Optional[ArcgisServiceResourceExtractor]:
    """A factory for instantiating the correct extractor for the resource"""
    service_type_name = parse_remote_url(resource_unique_identifier)[-1]
    service_type = ArcgisServiceType(service_type_name)
    if service_type == ArcgisServiceType.MAP_SERVICE:
        service = arcrest.MapService(resource_unique_identifier)
        result = ArcgisMapServiceResourceExtractor(service)
    elif service_type == ArcgisServiceType.IMAGE_SERVICE:
        service = arcrest.ImageService(resource_unique_identifier)
        result = ArcgisImageServiceResourceExtractor(service)
    else:
        logger.error(f"Unsupported ArcGIS REST service {service_type!r}")
        result = None
    return result


class ArcgisHarvesterWorker(base.BaseHarvesterWorker):
    harvest_map_services: bool
    harvest_image_services: bool
    resource_name_filter: typing.Optional[str]
    service_names_filter: typing.Optional[typing.List[str]]

    http_session: requests.Session
    _arc_catalog: typing.Optional[arcrest.Catalog]
    _relevant_service_extractors: typing.Optional[
        typing.List[typing.Union[ArcgisMapServiceResourceExtractor, ArcgisImageServiceResourceExtractor]]
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
        resource_name_filter: typing.Optional[str] = True,
        service_names_filter: typing.Optional[typing.List[str]] = None,
    ) -> None:
        catalog_url, service_name, service_type_name = parse_remote_url(remote_url)
        if service_name is not None:
            names_filter = [service_name] + (service_names_filter or [])
            service_type = ArcgisServiceType(service_type_name)
            harvest_maps = (service_type == ArcgisServiceType.MAP_SERVICE) or harvest_map_services
            harvest_images = (service_type == ArcgisServiceType.IMAGE_SERVICE) or harvest_image_services
        else:
            names_filter = service_names_filter or []
            harvest_maps = harvest_map_services
            harvest_images = harvest_image_services
        super().__init__(catalog_url, harvester_id)
        self.http_session = requests.Session()
        self.harvest_map_services = harvest_maps
        self.harvest_image_services = harvest_images
        self.resource_name_filter = resource_name_filter
        self.service_names_filter = names_filter
        self._arc_catalog = None
        self._relevant_service_extractors = None

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @property
    def arc_catalog(self):
        if self._arc_catalog is None:
            try:
                self._arc_catalog = arcrest.Catalog(self.remote_url)
            except (json.JSONDecodeError, URLError, HTTPError):
                logger.exception(f"Could not connect to ArcGIS REST server at {self.remote_url!r}")
        return self._arc_catalog

    @classmethod
    def from_django_record(cls, harvester: "Harvester"):  # noqa
        return cls(
            remote_url=harvester.remote_url,
            harvester_id=harvester.pk,
            harvest_map_services=harvester.harvester_type_specific_configuration.get("harvest_map_services", True),
            harvest_image_services=harvester.harvester_type_specific_configuration.get("harvest_image_services", True),
            resource_name_filter=harvester.harvester_type_specific_configuration.get("resource_name_filter"),
            service_names_filter=harvester.harvester_type_specific_configuration.get("service_names_filter"),
        )

    @classmethod
    def get_extra_config_schema(cls) -> typing.Optional[typing.Dict]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": ("https://geonode.org/harvesting/geonode-arcgis-rest-harvester.schema.json"),
            "title": "ArcGIS REST harvester config",
            "description": (
                "A jsonschema for validating configuration option for GeoNode's "
                "remote ArcGIS REST services harvester"
            ),
            "type": "object",
            "properties": {
                "harvest_map_services": {"type": "boolean", "default": True},
                "harvest_image_services": {"type": "boolean", "default": True},
                "resource_name_filter": {
                    "type": "string",
                },
                "service_names_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "additionalProperties": False,
        }

    def get_num_available_resources(self) -> int:
        result = 0
        for service_extractor in self._get_relevant_services():
            result += service_extractor.get_num_resources()
        return result

    def list_resources(self, offset: typing.Optional[int] = 0) -> typing.List[base.BriefRemoteResource]:
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

    def get_geonode_resource_defaults(
        self,
        harvested_info: base.HarvestedResourceInfo,
        harvestable_resource: models.HarvestableResource,
    ) -> typing.Dict:
        defaults = super().get_geonode_resource_defaults(harvested_info, harvestable_resource)
        defaults["name"] = harvested_info.resource_descriptor.identification.name
        defaults.update(harvested_info.resource_descriptor.additional_parameters)
        return defaults

    def get_resource(
        self,
        harvestable_resource: models.HarvestableResource,
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        extractor = get_resource_extractor(harvestable_resource.unique_identifier)
        extractor.resource_name_filter = self.resource_name_filter
        return extractor.get_resource(harvestable_resource)

    def _get_extractor_class(self, service_type: ArcgisServiceType) -> typing.Optional[typing.Type]:
        if service_type == ArcgisServiceType.MAP_SERVICE and self.harvest_map_services:
            result = ArcgisMapServiceResourceExtractor
        elif service_type == ArcgisServiceType.IMAGE_SERVICE and self.harvest_image_services:
            result = ArcgisImageServiceResourceExtractor
        else:
            result = None
        return result

    def _get_service_extractors(self, service) -> typing.List:
        # This method is fugly. Unfortunately, when multiple services share the
        # same name, arcrest just instantiates an `AmbiguousService` instance and
        # shoves the concrete services as attributes of this instance.
        # To make matters more unpleasant, the arcrest `AmbiguousService` class is
        # defined inside the `__getitem__` method of another class, so it cannot be
        # imported outside of it. Thus we resort to checking if there is a
        # `__service_type__` attribute on the service in order to deduct whether this is a
        # legit service or an ambiguous one and then deal with it
        result = []
        if not hasattr(service, "__service_type__"):
            # this is an arcrest AmbiguousService instance
            for sub_service_type in service.__dict__.keys():
                try:
                    type_ = ArcgisServiceType(sub_service_type)
                except ValueError:
                    logger.debug(f"Unrecognized service type: {sub_service_type!r}")
                    continue
                else:
                    extractor_class = self._get_extractor_class(type_)
                    if extractor_class is not None:
                        sub_service = getattr(service, sub_service_type)
                        extractor = extractor_class(sub_service)
                        extractor.resource_name_filter = self.resource_name_filter
                        result.append(extractor)
        else:
            try:
                type_ = ArcgisServiceType(service.__service_type__)
            except ValueError:
                logger.debug(f"Unrecognized service type: {service.__service_type__!r}")
            else:
                extractor_class = self._get_extractor_class(type_)
                if extractor_class is not None:
                    extractor = extractor_class(service)
                    extractor.resource_name_filter = self.resource_name_filter
                    result.append(extractor)
        return result

    def _get_relevant_services(
        self,
    ) -> typing.List[typing.Union[ArcgisMapServiceResourceExtractor, ArcgisImageServiceResourceExtractor]]:
        if self._relevant_service_extractors is None:
            result = []
            relevant_service_names = self.service_names_filter or self.arc_catalog.servicenames
            for service_name in relevant_service_names:
                service = None
                for _folder in service_name.split("/"):
                    if not service:
                        service = self.arc_catalog[_folder]
                    else:
                        service = service[_folder]
                extractors = self._get_service_extractors(service)
                result.extend(extractors)
            self._relevant_service_extractors = result
        return self._relevant_service_extractors


def _parse_spatial_extent(raw_extent: typing.Dict) -> typing.Tuple[str, geos.Polygon]:
    spatial_reference = raw_extent.get("spatialReference", {})
    epsg_code = f"EPSG:{spatial_reference.get('latestWkid', spatial_reference.get('wkid'))}"
    extent = geos.Polygon.from_bbox((raw_extent["xmin"], raw_extent["ymin"], raw_extent["xmax"], raw_extent["ymax"]))
    return epsg_code, extent
