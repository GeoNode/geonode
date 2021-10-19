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

"""Harvester for legacy GeoNode remote servers"""

import datetime as dt
import enum
import json
import logging
import typing
import urllib.parse
import uuid

import datetime
import dateutil.parser
import requests
from django.contrib.gis import geos
from lxml import etree

from geonode.documents.models import Document
from geonode.layers.models import Dataset
from geonode.maps.models import Map

from .. import (
    models,
    resourcedescriptor,
)
from ..utils import (
    XML_PARSER,
    get_xpath_value
)
from . import base

logger = logging.getLogger(__name__)


class GeoNodeDatasetType(enum.Enum):
    VECTOR = "vector"
    RASTER = "raster"


class RemoteDatasetType(enum.Enum):
    VECTOR = "shapefile"
    RASTER = "geotiff"


class GeoNodeResourceType(enum.Enum):
    DOCUMENT = "documents"
    DATASET = "layers"
    MAP = "maps"


class GeonodeLegacyHarvester(base.BaseHarvesterWorker):
    harvest_documents: bool
    harvest_datasets: bool

    # harvesting of maps is explicitly disabled - the GeoNode API does not
    # really allow reconstructing a Map via API, as there is no information
    # about the actual contents of the map, i.e. which layers are contained
    # in it
    harvest_maps: bool = False

    copy_documents: bool
    resource_title_filter: typing.Optional[str]
    http_session: requests.Session
    page_size: int = 10

    def __init__(
            self,
            *args,
            harvest_documents: typing.Optional[bool] = True,
            harvest_datasets: typing.Optional[bool] = True,
            copy_datasets: typing.Optional[bool] = False,
            copy_documents: typing.Optional[bool] = False,
            resource_title_filter: typing.Optional[str] = None,
            start_date_filter: typing.Optional[str] = None,
            end_date_filter: typing.Optional[str] = None,
            keywords_filter: typing.Optional[list] = None,
            categories_filter: typing.Optional[list] = None,
            **kwargs
    ):
        """A harvester for remote GeoNode instances."""
        super().__init__(*args, **kwargs)
        self.remote_url = self.remote_url.rstrip("/")
        self.http_session = requests.Session()
        self.harvest_documents = (
            harvest_documents if harvest_documents is not None else True)
        self.harvest_datasets = harvest_datasets if harvest_datasets is not None else True
        self.copy_datasets = copy_datasets
        self.copy_documents = copy_documents
        self.resource_title_filter = resource_title_filter
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.keywords_filter = keywords_filter
        self.categories_filter = categories_filter

    @property
    def base_api_url(self):
        return f"{self.remote_url}/api"

    @property
    def allows_copying_resources(self) -> bool:
        return True

    @classmethod
    def from_django_record(cls, record: models.Harvester):
        return cls(
            record.remote_url,
            record.id,
            harvest_documents=record.harvester_type_specific_configuration.get(
                "harvest_documents", True),
            harvest_datasets=record.harvester_type_specific_configuration.get(
                "harvest_datasets", True),
            copy_datasets=record.harvester_type_specific_configuration.get(
                "copy_datasets", False),
            copy_documents=record.harvester_type_specific_configuration.get(
                "copy_documents", False),
            resource_title_filter=record.harvester_type_specific_configuration.get(
                "resource_title_filter"),
            start_date_filter=record.harvester_type_specific_configuration.get(
                "start_date_filter"),
            end_date_filter=record.harvester_type_specific_configuration.get(
                "end_date_filter"),
            keywords_filter=record.harvester_type_specific_configuration.get(
                "keywords_filter"),
            categories_filter=record.harvester_type_specific_configuration.get(
                "categories_filter")
        )

    @classmethod
    def get_extra_config_schema(cls) -> typing.Dict:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://geonode.org/harvesting/geonode-legacy-harvester.schema.json"),
            "title": "GeoNode harvester config",
            "description": (
                "A jsonschema for validating configuration option for GeoNode's "
                "remote GeoNode harvester"
            ),
            "type": "object",
            "properties": {
                "harvest_documents": {
                    "type": "boolean",
                    "default": True
                },
                "copy_documents": {
                    "type": "boolean",
                    "default": False
                },
                "harvest_datasets": {
                    "type": "boolean",
                    "default": True
                },
                "copy_datasets": {
                    "type": "boolean",
                    "default": False
                },
                "resource_title_filter": {
                    "type": "string",
                },
                "start_date_filter": {
                    "type": "string",
                    "format": "date-time"
                },
                "end_date_filter": {
                    "type": "string",
                    "format": "date-time"
                },
                "keywords_filter": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "categories_filter": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
            },
            "additionalProperties": False,
        }

    def get_num_available_resources(self) -> int:
        result = 0
        if self.harvest_datasets:
            result += self._get_total_records(GeoNodeResourceType.DATASET)
        if self.harvest_documents:
            result += self._get_total_records(GeoNodeResourceType.DOCUMENT)
        if self.harvest_maps:
            result += self._get_total_records(GeoNodeResourceType.MAP)
        return result

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        # the implementation of this method is a bit convoluted because the GeoNode
        # legacy versions do not have a common `/resources` endpoint, we must query
        # the individual endpoints for documents, layers and maps and work out the
        # correct offsets to use.
        total_resources = self._get_num_available_resources_by_type()
        if offset < total_resources[GeoNodeResourceType.DOCUMENT]:
            document_list = self._list_document_resources(offset)
            if len(document_list) < self.page_size:
                dataset_list = self._list_dataset_resources(0)
                added = document_list + dataset_list
                if len(added) < self.page_size:
                    map_list = self._list_map_resources(0)
                    result = (added + map_list)[:self.page_size]
                else:
                    result = added[:self.page_size]
            else:
                result = document_list
        elif offset < (
                total_resources[GeoNodeResourceType.DOCUMENT] +
                total_resources[GeoNodeResourceType.DATASET]
        ):
            dataset_offset = offset - total_resources[GeoNodeResourceType.DOCUMENT]
            dataset_list = self._list_dataset_resources(dataset_offset)
            if len(dataset_list) < self.page_size:
                map_list = self._list_map_resources(0)
                result = (dataset_list + map_list)[:self.page_size]
            else:
                result = dataset_list
        else:
            map_offset = offset - (
                total_resources[GeoNodeResourceType.DOCUMENT] +
                total_resources[GeoNodeResourceType.DATASET]
            )
            result = self._list_map_resources(map_offset)
        return result

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        """Check whether the remote GeoNode is online."""
        try:
            response = self.http_session.get(
                f"{self.base_api_url}/", timeout=timeout_seconds)
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            result = False
        else:
            try:
                response_payload = response.json()
            except json.JSONDecodeError:
                logger.exception("Could not decode server response as valid JSON")
                result = False
            else:
                layers_endpoint_present = response_payload.get("layers") is not None
                result = layers_endpoint_present
        return result

    def get_geonode_resource_type(self, remote_resource_type: str) -> typing.Type[typing.Union[Dataset, Document, Map]]:
        """Return resource type class from resource type string."""
        return {
            GeoNodeResourceType.MAP.value: Map,
            GeoNodeResourceType.DATASET.value: Dataset,
            GeoNodeResourceType.DOCUMENT.value: Document,
        }[remote_resource_type]

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        resource_unique_identifier = harvestable_resource.unique_identifier
        local_resource_type = self.get_geonode_resource_type(harvestable_resource.remote_resource_type)
        endpoint_suffix = {
            Document: (
                f"/documents/{resource_unique_identifier}/"),
            Dataset: f"/layers/{resource_unique_identifier}/",
            Map: f"/maps/{resource_unique_identifier}/",
        }[local_resource_type]
        url = f"{self.base_api_url}{endpoint_suffix}"
        response = self.http_session.get(url)
        result = None
        if response.status_code == requests.codes.ok:
            api_record = response.json()
            resource_descriptor = self._get_resource_details(
                api_record, harvestable_resource)
            result = base.HarvestedResourceInfo(
                resource_descriptor=resource_descriptor,
                additional_information=None
            )
        else:
            logger.warning(
                f"Could not retrieve remote resource {resource_unique_identifier!r}")
        return result

    def should_copy_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
    ) -> bool:
        return {
            GeoNodeResourceType.DOCUMENT.value: self.copy_documents,
            GeoNodeResourceType.DATASET.value: self.copy_datasets,
            GeoNodeResourceType.MAP.value: False,
        }[harvestable_resource.remote_resource_type]

    def get_geonode_resource_defaults(
            self,
            harvested_info: base.HarvestedResourceInfo,
            harvestable_resource: models.HarvestableResource,
    ) -> typing.Dict:
        defaults = super().get_geonode_resource_defaults(harvested_info, harvestable_resource)
        defaults.update(harvested_info.resource_descriptor.additional_parameters)
        local_resource_type = self.get_geonode_resource_type(harvestable_resource.remote_resource_type)
        to_copy = self.should_copy_resource(harvestable_resource)
        if local_resource_type == Document and not to_copy:
            # since we are not copying the document, we need to provide suitable remote URLs
            defaults.update({
                "doc_url": harvested_info.resource_descriptor.distribution.original_format_url,
                "thumbnail_url": harvested_info.resource_descriptor.distribution.thumbnail_url,
            })
        elif local_resource_type == Dataset and not to_copy:
            # since we are not copying the dataset, we need to provide suitable SRID and remote URL
            try:
                srid = harvested_info.resource_descriptor.reference_systems[0]
            except AttributeError:
                srid = None
            defaults.update({
                "alternate": defaults["name"],
                "name": defaults["name"].rpartition(":")[-1],
                "workspace": defaults["name"].rpartition(":")[0],
                "ows_url": harvested_info.resource_descriptor.distribution.wms_url,
                "thumbnail_url": harvested_info.resource_descriptor.distribution.thumbnail_url,
                "srid": srid,
            })
        return defaults

    def _get_num_available_resources_by_type(
            self) -> typing.Dict[GeoNodeResourceType, int]:
        result = {
            GeoNodeResourceType.DOCUMENT: 0,
            GeoNodeResourceType.DATASET: 0,
            GeoNodeResourceType.MAP: 0,
        }
        if self.harvest_documents:
            result[GeoNodeResourceType.DOCUMENT] = self._get_total_records(
                GeoNodeResourceType.DOCUMENT)
        if self.harvest_datasets:
            result[GeoNodeResourceType.DATASET] = self._get_total_records(
                GeoNodeResourceType.DATASET)
        if self.harvest_maps:
            result[GeoNodeResourceType.MAP] = self._get_total_records(
                GeoNodeResourceType.MAP)
        return result

    def _list_document_resources(
            self, offset: int) -> typing.List[base.BriefRemoteResource]:
        result = []
        if self.harvest_documents:
            result = self._list_resources_by_type(GeoNodeResourceType.DOCUMENT, offset)
        return result

    def _list_dataset_resources(
            self, offset: int) -> typing.List[base.BriefRemoteResource]:
        result = []
        if self.harvest_datasets:
            result = self._list_resources_by_type(GeoNodeResourceType.DATASET, offset)
        return result

    def _list_map_resources(
            self, offset: int) -> typing.List[base.BriefRemoteResource]:
        result = []
        if self.harvest_maps:
            result = self._list_resources_by_type(GeoNodeResourceType.MAP, offset)
        return result

    def _list_resources_by_type(
            self,
            resource_type: GeoNodeResourceType,
            offset: int
    ) -> typing.List[base.BriefRemoteResource]:
        response = self.http_session.get(
            f"{self.base_api_url}/{resource_type.value}/",
            params=self._get_resource_list_params(offset)
        )
        response.raise_for_status()
        result = []
        for resource in response.json().get('objects', []):
            brief_resource = base.BriefRemoteResource(
                unique_identifier=self._extract_unique_identifier(resource),
                title=resource['title'],
                abstract=resource['abstract'],
                resource_type=resource_type.value,
            )
            result.append(brief_resource)
        return result

    def _extract_unique_identifier(self, raw_remote_resource: typing.Dict) -> str:
        return raw_remote_resource["id"]

    def _get_resource_details(
            self,
            api_record: typing.Dict,
            harvestable_resource: models.HarvestableResource
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        """
        Produce a record description from the response provided by the remote GeoNode.
        """
        result = None
        # query CSW endpoint and parse its response in order to get more information
        # about the resource
        get_record_by_id_response = self.http_session.get(
            f"{self.remote_url}/catalogue/csw",
            params={
                "service": "CSW",
                "version": "2.0.2",
                "request": "GetRecordById",
                "id": api_record["uuid"],
                "elementsetname": "full",
                "outputschema": "http://www.isotc211.org/2005/gmd",
            }
        )
        if get_record_by_id_response.status_code == requests.codes.ok:
            xml_root = etree.fromstring(
                get_record_by_id_response.content, parser=XML_PARSER)
            try:
                metadata_element = xml_root.xpath(
                    "./gmd:MD_Metadata", namespaces=xml_root.nsmap)[0]
            except IndexError:
                logger.warning("Unable to retrieve a metadata element from the CSW GetRecordById response, skipping...")
                logger.debug(f"Original response content: {get_record_by_id_response.content}")
            else:
                try:
                    result = self._get_resource_descriptor(
                        metadata_element, api_record, harvestable_resource)
                except TypeError:
                    logger.exception("Could not retrieve metadata details to generate resource descriptor, skipping...")
                else:
                    logger.debug(
                        f"Found details for resource {result.uuid!r} - {result.identification.title!r}"
                    )
        else:
            logger.warning(
                f"Got invalid response from {get_record_by_id_response.request.url}")
        return result

    def _get_resource_list_params(
            self, offset: typing.Optional[int] = 0) -> typing.Dict:
        result = {
            "limit": self.page_size,
            "offset": offset,
        }
        if self.resource_title_filter is not None:
            result["title__icontains"] = self.resource_title_filter
        if self.start_date_filter is not None:
            start_date = dateutil.parser.parse(self.start_date_filter)
            result["date__gte"] = f"{start_date.astimezone(datetime.timezone.utc).replace(microsecond=0).isoformat().split('+')[0]}Z"
        if self.end_date_filter is not None:
            end_date = dateutil.parser.parse(self.end_date_filter)
            result["date__lte"] = f"{end_date.astimezone(datetime.timezone.utc).replace(microsecond=0).isoformat().split('+')[0]}Z"
        if self.keywords_filter is not None:
            result["keywords__slug__in"] = ','.join(self.keywords_filter)
        if self.categories_filter is not None:
            result["category__identifier__in"] = ','.join(self.categories_filter)
        if self.categories_filter is not None:
            result["category__identifier__in"] = ','.join(self.categories_filter)
        return result

    def _get_total_records(
            self,
            resource_type: GeoNodeResourceType,
    ) -> int:
        url = f"{self.base_api_url}/{resource_type.value}/"
        response = self.http_session.get(
            url,
            params=self._get_resource_list_params()
        )
        result = 0
        if response.status_code != requests.codes.ok:
            logger.error(f"Got back invalid response from {url!r}")
        else:
            try:
                result = response.json().get("meta", {}).get("total_count", 0)
            except json.JSONDecodeError as exc:
                logger.exception("Could not decode response as a JSON object")
                raise base.HarvestingException(str(exc))
        return result

    def _get_resource_descriptor(
            self,
            csw_record: etree.Element,
            api_record: typing.Dict,
            harvestable_resource: models.HarvestableResource
    ) -> resourcedescriptor.RecordDescription:
        identification_descriptor = get_identification_descriptor(
            csw_record.xpath("gmd:identificationInfo", namespaces=csw_record.nsmap)[0],
            api_record
        )
        crs = api_record.get("srid", "EPSG:4326")
        descriptor = resourcedescriptor.RecordDescription(
            uuid=uuid.UUID(get_xpath_value(csw_record, "gmd:fileIdentifier")),
            language=get_xpath_value(csw_record, "gmd:language"),
            character_set=csw_record.xpath(
                "gmd:characterSet/gmd:MD_CharacterSetCode/text()",
                namespaces=csw_record.nsmap)[0],
            hierarchy_level=csw_record.xpath(
                "gmd:hierarchyLevel/gmd:MD_ScopeCode/text()",
                namespaces=csw_record.nsmap)[0],
            point_of_contact=get_contact_descriptor(
                csw_record.xpath(
                    "gmd:contact[.//gmd:role//@codeListValue='pointOfContact']",
                    namespaces=csw_record.nsmap
                )[0]
            ),
            author=get_contact_descriptor(
                csw_record.xpath(
                    "gmd:contact[.//gmd:role//@codeListValue='author']",
                    namespaces=csw_record.nsmap
                )[0]
            ),
            date_stamp=dateutil.parser.parse(
                csw_record.xpath(
                    "gmd:dateStamp/gco:DateTime/text()", namespaces=csw_record.nsmap)[0],
            ).replace(tzinfo=dt.timezone.utc),
            reference_systems=[crs],
            identification=identification_descriptor,
            distribution=self.get_distribution_info(
                csw_record.xpath(
                    "gmd:distributionInfo", namespaces=csw_record.nsmap)[0],
                api_record,
                harvestable_resource,
                identification_descriptor,
                crs
            ),
            data_quality=get_xpath_value(csw_record, ".//gmd:dataQualityInfo//gmd:lineage"),
        )
        additional_params_handler = {
            GeoNodeResourceType.DATASET.value: self._get_dataset_additional_parameters,
            GeoNodeResourceType.DOCUMENT.value: self._get_document_additional_parameters,
            GeoNodeResourceType.MAP.value: self._get_map_additional_parameters,
        }[harvestable_resource.remote_resource_type]
        additional_params = additional_params_handler(descriptor, api_record)
        descriptor.additional_parameters.update(additional_params)
        return descriptor

    def _get_dataset_additional_parameters(
            self,
            descriptor: resourcedescriptor.RecordDescription,
            api_record: typing.Dict
    ) -> typing.Dict:
        result = {
            "name": descriptor.identification.name,
            "charset": descriptor.character_set,
            "resource_type": "dataset"
        }
        if descriptor.identification.native_format.lower() == RemoteDatasetType.VECTOR.value:
            result["subtype"] = GeoNodeDatasetType.VECTOR.value
        elif descriptor.identification.native_format.lower() == RemoteDatasetType.RASTER.value:
            result["subtype"] = GeoNodeDatasetType.RASTER.value
        return result

    def _get_document_additional_parameters(
            self,
            descriptor: resourcedescriptor.RecordDescription,
            api_record: typing.Dict
    ) -> typing.Dict:
        return {
            "resource_type": "document",
            "extension": api_record.get("extension")
        }

    def _get_map_additional_parameters(
            self,
            descriptor: resourcedescriptor.RecordDescription,
            api_record: typing.Dict
    ) -> typing.Dict:
        return {
            "zoom": api_record.get("zoom", 5),
            "center_x": api_record.get("center_x", 0),
            "center_y": api_record.get("center_y", 0),
            "projection": api_record.get("projection", "EPSG:3857"),
            "last_modified": api_record.get("last_modified")
        }

    def get_distribution_info(
            self,
            csw_distribution: etree.Element,
            api_record: typing.Dict,
            harvestable_resource: models.HarvestableResource,
            identification_descriptor: resourcedescriptor.RecordIdentification,
            crs: str,
    ) -> resourcedescriptor.RecordDistribution:
        online_elements = csw_distribution.xpath(
            ".//gmd:transferOptions//gmd:onLine", namespaces=csw_distribution.nsmap)
        link = None
        wms = None
        wfs = None
        wcs = None
        legend = None
        geojson = None
        original = None
        original_format_values = (
            "original dataset format",
            "hosted document format",
        )
        for online_el in online_elements:
            protocol = get_xpath_value(online_el, ".//gmd:protocol").lower()
            linkage = get_xpath_value(online_el, ".//gmd:linkage")
            description = (get_xpath_value(online_el, ".//gmd:description") or "").lower()
            if "link" in protocol:
                link = linkage
            elif "ogc:wms" in protocol:
                wms = linkage
            elif "ogc:wfs" in protocol:
                wfs = linkage
            elif "ogc:wcs" in protocol:
                wcs = linkage
            elif "legend" in description.lower():
                legend = linkage
            elif "geojson" in description.lower():
                geojson = linkage
            else:
                for original_value in original_format_values:
                    if original_value in description.lower():
                        original = linkage
                        break
        if harvestable_resource.remote_resource_type == GeoNodeResourceType.DATASET.value:
            # for layers, we generate a download URL for a zipped shapefile, in a similar way
            # as is done on the main GeoNode UI, by leveraging WFS
            if wfs is not None:
                query_params = {
                    "service": "WFS",
                    "version": "1.0.0",
                    "request": "GetFeature",
                    "typename": identification_descriptor.name,
                    "outputformat": "SHAPE-ZIP",
                    "srs": crs,
                    "format_options": "charset:UTF-8",
                }
                original = f"{wfs}?{urllib.parse.urlencode(query_params)}"
            elif wcs is not None:
                coords = identification_descriptor.spatial_extent.coords[0]
                min_x = min([i[0] for i in coords])
                max_x = max([i[0] for i in coords])
                min_y = min([i[1] for i in coords])
                max_y = max([i[1] for i in coords])
                query_params = {
                    "service": "WCS",
                    "version": "2.0.1",
                    "request": "GetCoverage",
                    "srs": crs,
                    "format": "image/tiff",
                    "coverageid": identification_descriptor.name.replace(":", "__"),
                    "bbox": f"{min_x},{min_y},{max_x},{max_y}"
                }
                original = f"{wcs}?{urllib.parse.urlencode(query_params)}"
            else:
                try:
                    original = [record_link.get('url') for record_link in api_record.get("links", []) if record_link.get('name') == 'Zipped Shapefile'][0]
                except IndexError:
                    pass
        return resourcedescriptor.RecordDistribution(
            link_url=link,
            wms_url=wms,
            wfs_url=wfs,
            wcs_url=wcs,
            thumbnail_url=self._retrieve_thumbnail_url(
                api_record, harvestable_resource),
            legend_url=legend,
            geojson_url=geojson,
            original_format_url=original,
        )

    def _retrieve_thumbnail_url(
            self,
            api_record: typing.Dict,
            harvestable_resource: models.HarvestableResource,
    ) -> str:
        is_document = (
            harvestable_resource.remote_resource_type ==
            GeoNodeResourceType.DOCUMENT.value
        )
        found_thumbnail = False
        if is_document:
            # there seems to be a bug in GeoNode whereby the thumbnail for documents
            # is reported correctly on the document list endpoint but it is reported
            # incorrectly on the document detail endpoint and it is also incorrect in
            # the CSW response. Therefore we resort to fetching the thumbnail through
            # the document list endpoint
            document_list_response = self.http_session.get(
                f"{self.base_api_url}/documents/",
                params={"id": harvestable_resource.unique_identifier}
            )
            if document_list_response.status_code == requests.codes.ok:
                raw_response = document_list_response.json()
                try:
                    reported_thumbnail: str = (
                        raw_response["objects"][0]["thumbnail_url"])
                except (KeyError, IndexError):
                    logger.exception("Could not retrieve document details from the list endpoint")
                else:
                    if reported_thumbnail.startswith("/"):
                        thumbnail = f"{self.remote_url}{reported_thumbnail}"
                    else:
                        thumbnail = reported_thumbnail
                    found_thumbnail = True
            else:
                logger.debug(
                    f"Could not retrieve document list endpoint: {document_list_response.status_code} - {document_list_response.reason}"
                )
        if not found_thumbnail:
            reported_thumbnail: typing.Optional[str] = api_record.get("thumbnail_url")
            if reported_thumbnail is not None and reported_thumbnail.startswith("/"):
                # it is not a full URL
                thumbnail = f"{self.remote_url}{reported_thumbnail}"
            else:
                thumbnail = reported_thumbnail
        return thumbnail


def get_contact_descriptor(contact: etree.Element):
    return resourcedescriptor.RecordDescriptionContact(
        role=contact.xpath(
            ".//gmd:role/gmd:CI_RoleCode/text()",
            namespaces=contact.nsmap
        )[0],
        name=_get_optional_attribute_value(
            contact, ".//gmd:individualName"),
        organization=_get_optional_attribute_value(
            contact, ".//gmd:organisationName"),
        position=_get_optional_attribute_value(
            contact, ".//gmd:positionName"),
        phone_voice=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:phone//gmd:voice"),
        phone_facsimile=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:phone//gmd:facsimile"),
        address_delivery_point=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:address//gmd:deliveryPoint"),
        address_city=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:address//gmd:city"),
        address_administrative_area=_get_optional_attribute_value(
            contact,
            ".//gmd:contactInfo//gmd:address//gmd:administrativeArea"
        ),
        address_postal_code=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:address//gmd:postalCode"),
        address_country=_get_optional_attribute_value(
            contact, ".//gmd:contactInfo//gmd:address//gmd:country"),
        address_email=get_xpath_value(
            contact,
            ".//gmd:contactInfo//gmd:address//gmd:electronicMailAddress"
        )
    )


def get_identification_descriptor(csw_identification: etree.Element, api_record: typing.Dict):
    place_keywords = csw_identification.xpath(
        ".//gmd:descriptiveKeywords//gmd:keyword//text()[../../../gmd:type//"
        "@codeListValue='place']",
        namespaces=csw_identification.nsmap
    )
    other_keywords = csw_identification.xpath(
        ".//gmd:descriptiveKeywords//gmd:keyword//text()[../../../gmd:type//"
        "@codeListValue!='place']",
        namespaces=csw_identification.nsmap
    )
    license_info = "".join(
        csw_identification.xpath(
            ".//gmd:resourceConstraints//gmd:otherConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue='license']",
            namespaces=csw_identification.nsmap
        )
    ).strip()
    other_constraints_description = "".join(
        csw_identification.xpath(
            ".//gmd:resourceConstraints//gmd:otherConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue!='license']",
            namespaces=csw_identification.nsmap
        )
    ).strip()
    other_constraints_code = "".join(
        csw_identification.xpath(
            ".//gmd:resourceConstraints//gmd:useConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue!='license']",
            namespaces=csw_identification.nsmap
        )
    ).strip() or None
    name = get_xpath_value(csw_identification, ".//gmd:citation//gmd:name")
    title = get_xpath_value(csw_identification, ".//gmd:citation//gmd:title")
    return resourcedescriptor.RecordIdentification(
        name=name or title,
        title=title,
        date=dateutil.parser.parse(
            get_xpath_value(csw_identification, ".//gmd:citation//gmd:date//gmd:date")
        ).replace(tzinfo=dt.timezone.utc),
        date_type=get_xpath_value(csw_identification, ".//gmd:citation//gmd:dateType"),
        abstract=get_xpath_value(csw_identification, ".//gmd:abstract"),
        purpose=get_xpath_value(csw_identification, ".//gmd:purpose"),
        status=get_xpath_value(csw_identification, ".//gmd:status"),
        originator=get_contact_descriptor(
            csw_identification.xpath(
                ".//gmd:pointOfContact", namespaces=csw_identification.nsmap)[0]
        ),
        graphic_overview_uri=get_xpath_value(
            csw_identification, ".//gmd:graphicOverview//gmd:fileName"),
        native_format=_get_native_format(csw_identification, api_record),
        place_keywords=place_keywords,
        other_keywords=other_keywords,
        license=license_info.split(":", maxsplit=1),
        other_constraints=(
            f"{other_constraints_code or ''}:{other_constraints_description}"),
        topic_category=get_xpath_value(csw_identification, ".//gmd:topicCategory"),
        spatial_extent=get_spatial_extent_native(api_record),
        temporal_extent=get_temporal_extent(csw_identification),
        supplemental_information=get_xpath_value(
            csw_identification, ".//gmd:supplumentalInformation")
    )


def _get_native_format(
        csw_identification: etree.Element,
        api_record: typing.Dict
) -> typing.Optional[str]:
    if api_record.get("csw_type") == "document":
        result = api_record.get("extension")
    else:
        store_type = api_record.get("storeType", "").lower()
        if store_type == "coveragestore":
            result = "geotiff"
        elif store_type == "datastore":
            result = "shapefile"
        else:
            result = get_xpath_value(csw_identification, ".//gmd:resourceFormat//gmd:name")
    return result


def get_spatial_extent_4326(
        identification_el: etree.Element) -> typing.Optional[geos.Polygon]:
    try:
        extent_el = identification_el.xpath(
            ".//gmd:extent//gmd:geographicElement",
            namespaces=identification_el.nsmap
        )[0]
        left_x = get_xpath_value(extent_el, ".//gmd:westBoundLongitude")
        right_x = get_xpath_value(extent_el, ".//gmd:eastBoundLongitude")
        lower_y = get_xpath_value(extent_el, ".//gmd:southBoundLatitude")
        upper_y = get_xpath_value(extent_el, ".//gmd:northBoundLatitude")
        # GeoNode seems to have a bug whereby sometimes the reported extent uses a
        # comma as the decimal separator, other times it uses a dot
        result = geos.Polygon.from_bbox((
            float(left_x.replace(",", ".")),
            float(lower_y.replace(",", ".")),
            float(right_x.replace(",", ".")),
            float(upper_y.replace(",", ".")),
        ))
    except IndexError:
        result = None
    return result


def get_spatial_extent_native(api_record: typing.Dict):
    declared_ewkt = api_record.get("bbox_polygon")
    if declared_ewkt is not None:
        # this is a more recent GeoNode deployment
        result = geos.Polygon.from_ewkt(declared_ewkt)
    else:
        # this is an older GeoNode deployment
        left_x = float(api_record.get("bbox_x0", 0))
        right_x = float(api_record.get("bbox_x1", 0))
        lower_y = float(api_record.get("bbox_y0", 0))
        upper_y = float(api_record.get("bbox_y1", 0))
        result = geos.Polygon.from_bbox((
            left_x, lower_y, right_x, upper_y))
    return result


def get_temporal_extent(
        identification_el: etree.Element
) -> typing.Optional[typing.Tuple[dt.datetime, dt.datetime]]:
    try:
        extent_el = identification_el.xpath(
            ".//gmd:extent//gmd:temporalElement",
            namespaces=identification_el.nsmap
        )[0]
        begin = dateutil.parser.parse(
            get_xpath_value(extent_el, ".//gml:beginPosition")
        ).replace(tzinfo=dt.timezone.utc)
        end = dateutil.parser.parse(
            get_xpath_value(extent_el, ".//gml:endPosition")
        ).replace(tzinfo=dt.timezone.utc)
        result = (begin, end)
    except IndexError:
        result = None
    return result


def _get_optional_attribute_value(
        element: etree.Element, xpath: str) -> typing.Optional[str]:
    return element.xpath(f"{xpath}/text()", namespaces=element.nsmap)[0].strip() or None
