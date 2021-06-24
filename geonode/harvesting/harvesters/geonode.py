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
import uuid

import dateutil.parser
import requests
from django.contrib.gis import geos
from lxml import etree

from .. import (
    models,
    resourcedescriptor,
)
from ..utils import XML_PARSER
from . import base

from geonode.base.models import ResourceBase
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map

logger = logging.getLogger(__name__)


class GeoNodeResourceType(enum.Enum):
    DOCUMENT = "documents"
    LAYER = "layers"
    MAP = "maps"


class GeonodeLegacyHarvester(base.BaseHarvesterWorker):
    harvest_documents: bool
    harvest_layers: bool
    harvest_maps: bool
    copy_documents: bool
    resource_title_filter: typing.Optional[str]
    http_session: requests.Session
    page_size: int = 10

    _TYPE_DOCUMENT = "documents"
    _TYPE_LAYER = "layers"
    _TYPE_MAP = "maps"

    def __init__(
            self,
            *args,
            harvest_documents: typing.Optional[bool] = True,
            harvest_layers: typing.Optional[bool] = True,
            harvest_maps: typing.Optional[bool] = True,
            copy_documents: typing.Optional[bool] = False,
            resource_title_filter: typing.Optional[str] = None,
            **kwargs
    ):
        """A harvester for remote GeoNode instances."""
        super().__init__(*args, **kwargs)
        self.http_session = requests.Session()
        self.harvest_documents = (
            harvest_documents if harvest_documents is not None else True)
        self.harvest_layers = harvest_layers if harvest_layers is not None else True
        self.harvest_maps = harvest_maps if harvest_maps is not None else True
        self.copy_documents = copy_documents
        self.resource_title_filter = resource_title_filter

    @property
    def base_api_url(self):
        return f"{self.remote_url}/api"

    @property
    def allows_copying_resources(self) -> bool:
        return True

    @classmethod
    def from_django_record(cls, record: "Harvester"):
        return cls(
            record.remote_url,
            record.id,
            harvest_documents=(
                record.harvester_type_specific_configuration.get(
                    "harvest_documents", True)
            ),
            harvest_layers=(
                record.harvester_type_specific_configuration.get(
                    "harvest_layers", True)
            ),
            harvest_maps=(
                record.harvester_type_specific_configuration.get(
                    "harvest_maps", True)
            ),
            resource_title_filter=(
                record.harvester_type_specific_configuration.get(
                    "resource_title_filter")
            ),
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
                "harvest_layers": {
                    "type": "boolean",
                    "default": True
                },
                "harvest_maps": {
                    "type": "boolean",
                    "default": True
                },
                "resource_title_filter": {
                    "type": "string",
                },
            },
            "additionalProperties": False,
        }

    def get_num_available_resources(self) -> int:
        result = 0
        if self.harvest_documents:
            result += self._get_total_records(GeoNodeResourceType.DOCUMENT)
        if self.harvest_layers:
            result += self._get_total_records(GeoNodeResourceType.LAYER)
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
                layer_list = self._list_layer_resources(0)
                added = document_list + layer_list
                if len(added) < self.page_size:
                    map_list = self._list_map_resources(0)
                    result = (added + map_list)[:self.page_size]
                else:
                    result = added[:self.page_size]
            else:
                result = document_list
        elif offset < (
                total_resources[GeoNodeResourceType.DOCUMENT] +
                total_resources[GeoNodeResourceType.LAYER]
        ):
            layer_offset = offset - total_resources[GeoNodeResourceType.DOCUMENT]
            layer_list = self._list_layer_resources(layer_offset)
            if len(layer_list) < self.page_size:
                map_list = self._list_map_resources(0)
                result = (layer_list + map_list)[:self.page_size]
            else:
                result = layer_list
        else:
            map_offset = offset - (
                    total_resources[GeoNodeResourceType.DOCUMENT] +
                    total_resources[GeoNodeResourceType.LAYER]
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
            result = True
        return result

    def get_geonode_resource_type(self, remote_resource_type: str) -> ResourceBase:
        """Return resource type class from resource type string."""
        return {
            GeoNodeResourceType.MAP.value: Map,
            GeoNodeResourceType.LAYER.value: Layer,
            GeoNodeResourceType.DOCUMENT.value: Document,
        }[remote_resource_type]

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
            harvesting_session_id: int
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        resource_unique_identifier = harvestable_resource.unique_identifier
        endpoint_suffix = {
            GeoNodeResourceType.DOCUMENT.value: (
                f"/documents/{resource_unique_identifier}/"),
            GeoNodeResourceType.LAYER.value: f"/layers/{resource_unique_identifier}/",
            GeoNodeResourceType.MAP.value: f"/maps/{resource_unique_identifier}/",
        }[harvestable_resource.remote_resource_type.lower()]
        response = self.http_session.get(f"{self.base_api_url}/{endpoint_suffix}")
        resource_descriptor = None
        if response.status_code == requests.codes.ok:
            raw_brief_resource = response.json()
            resource_descriptor = self._get_resource_details(raw_brief_resource)
            self.update_harvesting_session(
                harvesting_session_id, additional_harvested_records=1)
        else:
            logger.warning(
                f"Could not retrieve remote resource {resource_unique_identifier!r}")
        return resource_descriptor

    def _get_num_available_resources_by_type(
            self) -> typing.Dict[GeoNodeResourceType, int]:
        result = {
            GeoNodeResourceType.DOCUMENT: 0,
            GeoNodeResourceType.LAYER: 0,
            GeoNodeResourceType.MAP: 0,
        }
        if self.harvest_documents:
            result[GeoNodeResourceType.DOCUMENT] = self._get_total_records(
                GeoNodeResourceType.DOCUMENT)
        if self.harvest_layers:
            result[GeoNodeResourceType.LAYER] = self._get_total_records(
                GeoNodeResourceType.LAYER)
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

    def _list_layer_resources(
            self, offset: int) -> typing.List[base.BriefRemoteResource]:
        result = []
        if self.harvest_layers:
            result = self._list_resources_by_type(GeoNodeResourceType.LAYER, offset)
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
        for resource in response.json().get("objects", []):
            brief_resource = base.BriefRemoteResource(
                unique_identifier=self._extract_unique_identifier(resource),
                title=resource["title"],
                resource_type=resource_type.value,
            )
            result.append(brief_resource)
        return result

    def _extract_unique_identifier(self, raw_remote_resource: typing.Dict) -> str:
        return raw_remote_resource["id"]


    def _get_resource_details(
            self,
            raw_brief_resource: typing.Dict
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
                "id": raw_brief_resource["uuid"],
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
                logger.warning(
                    f"Unable to retrieve a metadata element from the CSW GetRecordById "
                    f"response, skipping..."
                )
                logger.debug(
                    f"Original response content: {get_record_by_id_response.content}")
            else:
                try:
                    result = get_resource_descriptor(metadata_element)
                except TypeError:
                    logger.exception(
                        f"Could not retrieve metadata details to generate "
                        f"resource descriptor, skipping..."
                    )
                else:
                    logger.debug(
                        f"Found details for resource {result.uuid!r} - "
                        f"{result.identification.title!r}"
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
        return result


def get_resource_descriptor(
        record: etree.Element) -> resourcedescriptor.RecordDescription:
    crs_epsg_code = ''.join(
        record.xpath(
            'gmd:referenceSystemInfo//code//text()', namespaces=record.nsmap)
    ).strip()
    return resourcedescriptor.RecordDescription(
        uuid=uuid.UUID(get_xpath_value(record, "gmd:fileIdentifier")),
        language=get_xpath_value(record, "gmd:language"),
        character_set=record.xpath(
            "gmd:characterSet/gmd:MD_CharacterSetCode/text()",
            namespaces=record.nsmap)[0],
        hierarchy_level=record.xpath(
            "gmd:hierarchyLevel/gmd:MD_ScopeCode/text()",
            namespaces=record.nsmap)[0],
        point_of_contact=get_contact_descriptor(
            record.xpath(
                "gmd:contact[.//gmd:role//@codeListValue='pointOfContact']",
                namespaces=record.nsmap
            )[0]
        ),
        author=get_contact_descriptor(
            record.xpath(
                "gmd:contact[.//gmd:role//@codeListValue='author']",
                namespaces=record.nsmap
            )[0]
        ),
        date_stamp=dateutil.parser.parse(
            record.xpath(
                "gmd:dateStamp/gco:DateTime/text()", namespaces=record.nsmap)[0],
        ).replace(tzinfo=dt.timezone.utc),
        reference_systems=[f"EPSG:{crs_epsg_code}"],
        identification=get_identification_descriptor(
            record.xpath("gmd:identificationInfo", namespaces=record.nsmap)[0]
        ),
        distribution=get_distribution_info(
            record.xpath("gmd:distributionInfo", namespaces=record.nsmap)[0]
        ),
        data_quality=get_xpath_value(record, ".//gmd:dataQualityInfo//gmd:lineage"),
    )


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


def get_identification_descriptor(identification: etree.Element):
    place_keywords = identification.xpath(
        ".//gmd:descriptiveKeywords//gmd:keyword//text()[../../../gmd:type//"
        "@codeListValue='place']",
        namespaces=identification.nsmap
    )
    other_keywords = identification.xpath(
        ".//gmd:descriptiveKeywords//gmd:keyword//text()[../../../gmd:type//"
        "@codeListValue!='place']",
        namespaces=identification.nsmap
    )
    license_info = "".join(
        identification.xpath(
            ".//gmd:resourceConstraints//gmd:otherConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue='license']",
            namespaces=identification.nsmap
        )
    ).strip()
    other_constraints_description = "".join(
        identification.xpath(
            ".//gmd:resourceConstraints//gmd:otherConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue!='license']",
            namespaces=identification.nsmap
        )
    ).strip()
    other_constraints_code = "".join(
        identification.xpath(
            ".//gmd:resourceConstraints//gmd:useConstraints//text()[../../..//"
            "gmd:useConstraints//@codeListValue!='license']",
            namespaces=identification.nsmap
        )
    ).strip() or None
    return resourcedescriptor.RecordIdentification(
        name=get_xpath_value(identification, ".//gmd:citation//gmd:name"),
        title=get_xpath_value(identification, ".//gmd:citation//gmd:title"),
        date=dateutil.parser.parse(
            get_xpath_value(identification, ".//gmd:citation//gmd:date//gmd:date")
        ).replace(tzinfo=dt.timezone.utc),
        date_type=get_xpath_value(identification, ".//gmd:citation//gmd:dateType"),
        abstract=get_xpath_value(identification, ".//gmd:abstract"),
        purpose=get_xpath_value(identification, ".//gmd:purpose"),
        status=get_xpath_value(identification, ".//gmd:status"),
        originator=get_contact_descriptor(
            identification.xpath(
                ".//gmd:pointOfContact", namespaces=identification.nsmap)[0]
        ),
        graphic_overview_uri=get_xpath_value(
            identification, ".//gmd:graphicOverview//gmd:fileName"),
        native_format=get_xpath_value(
            identification, ".//gmd:resourceFormat//gmd:name"),
        place_keywords=place_keywords,
        other_keywords=other_keywords,
        license=license_info.split(":", maxsplit=1),
        other_constraints=(
            f"{other_constraints_code or ''}:{other_constraints_description}"),
        topic_category=get_xpath_value(identification, ".//gmd:topicCategory"),
        spatial_extent=get_spatial_extent(identification),
        temporal_extent=get_temporal_extent(identification),
        supplemental_information=get_xpath_value(
            identification, ".//gmd:supplumentalInformation")
    )


def get_distribution_info(
        distribution: etree.Element) -> resourcedescriptor.RecordDistribution:
    online_elements = distribution.xpath(
        ".//gmd:transferOptions//gmd:onLine", namespaces=distribution.nsmap)
    link = None
    wms = None
    wfs = None
    wcs = None
    thumbnail = None
    legend = None
    geojson = None
    original = None
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
        elif "thumbnail" in description:
            thumbnail = linkage
        elif "legend" in description:
            legend = linkage
        elif "geojson" in description:
            geojson = linkage
        elif "original dataset format" in description:
            original = linkage
    return resourcedescriptor.RecordDistribution(
        link_url=link,
        wms_url=wms,
        wfs_url=wfs,
        wcs_url=wcs,
        thumbnail_url=thumbnail,
        legend_url=legend,
        geojson_url=geojson,
        original_format_url=original,
    )


def get_spatial_extent(
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


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
) -> typing.Optional[str]:
    values = element.xpath(f"{xpath_expression}//text()", namespaces=element.nsmap)
    return "".join(values).strip() or None


def _get_optional_attribute_value(
        element: etree.Element, xpath: str) -> typing.Optional[str]:
    return element.xpath(f"{xpath}/text()", namespaces=element.nsmap)[0].strip() or None
