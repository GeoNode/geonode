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

import datetime as dt
import json
import logging
import typing
import uuid

import dateutil.parser
import requests
from django.contrib.gis import geos
from lxml import etree

from .. import (
    resourcedescriptor,
)
from ..utils import XML_PARSER
from . import base

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map

logger = logging.getLogger(__name__)


class GeonodeLegacyHarvester(base.BaseHarvesterWorker):
    harvest_documents: bool
    harvest_layers: bool
    harvest_maps: bool
    copy_documents: bool
    resource_title_filter: typing.Optional[str]
    http_session: requests.Session
    page_size: int = 10

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
        for resource_type_suffix in ("documents", "layers", "maps"):
            result += self._get_total_records(resource_type_suffix)
        return result

    def _get_num_available_resources_by_type(self) -> typing.Dict[str, int]:
        result = {
            "documents": 0,
            "layers": 0,
            "maps": 0,
        }
        for resource_type_suffix in result.keys():
            result[resource_type_suffix] = self._get_total_records(resource_type_suffix)
        return result

    def _list_resources_by_type(
            self,
            resource_type: str, offset: int
    ) -> typing.List[base.BriefRemoteResource]:
        response = self.http_session.get(
            f"{self.base_api_url}/{resource_type}/",
            params=self._get_resource_list_params(offset)
        )
        response.raise_for_status()
        resources = response.json().get("objects", [])
        result = []
        for resource in response.json().get("objects", []):
            brief_resource = base.BriefRemoteResource(
                unique_identifier=self._extract_unique_identifier(resource),
                title=resource["title"],
                resource_type=resource_type,
            )
            result.append(brief_resource)
        return result

    def _extract_unique_identifier(self, raw_remote_resource: typing.Dict) -> str:
        return raw_remote_resource["id"]

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        total_resources = self._get_num_available_resources_by_type()
        if offset < total_resources["documents"]:
            document_list = self._list_resources_by_type("documents", offset)
            if len(document_list) < self.page_size:
                layer_list = self._list_resources_by_type("layers", 0)
                added = document_list + layer_list
                if len(added) < self.page_size:
                    map_list = self._list_resources_by_type("maps", 0)
                    result = (added + map_list)[:self.page_size]
                else:
                    result = added[:self.page_size]
            else:
                result = document_list
        elif offset < (total_resources["documents"] + total_resources["layers"]):
            layer_offset = offset - total_resources["documents"]
            layer_list = self._list_resources_by_type("layers", layer_offset)
            if len(layer_list) < self.page_size:
                map_list = self._list_resources_by_type("maps", 0)
                result = (layer_list + map_list)[:self.page_size]
            else:
                result = layer_list
        else:
            map_offset = offset - (
                    total_resources["documents"] + total_resources["layers"])
            result = self._list_resources_by_type("maps", map_offset)
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

    def get_resource_type_class(
            self, resource_type: str) -> typing.Optional[
        typing.Union[Layer, Map, Document]]:
        """ Return resource type class from resource type string """
        try:
            return {
                'maps': Map,
                'layers': Layer,
                'documents': Document,
            }[resource_type]
        except KeyError:
            return None

    def get_resource(
            self,
            resource_unique_identifier: str,
            resource_type: str,
            harvesting_session_id: typing.Optional[int] = None
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        endpoint_suffix = {
            "documents": f"/documents/{resource_unique_identifier}/",
            "layers": f"/layers/{resource_unique_identifier}/",
            "maps": f"/maps/{resource_unique_identifier}/",
        }[resource_type.lower()]
        response = self.http_session.get(f"{self.base_api_url}/{endpoint_suffix}")
        resource_descriptor = None
        if response.status_code == requests.codes.ok:
            raw_brief_resource = response.json()
            resource_descriptor = get_resource_descriptor(raw_brief_resource)
            self.update_harvesting_session(
                harvesting_session_id, additional_harvested_records=1)
        else:
            logger.warning(
                f"Could not retrieve remote resource {resource_unique_identifier!r}")
        return resource_descriptor

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
            endpoint_suffix: str,
    ) -> int:
        url = f"{self.base_api_url}/{endpoint_suffix}/"
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

    def _get_resource_descriptor(
            self, record: typing.Dict) -> resourcedescriptor.RecordDescription:
        xml_root = etree.fromstring(record["metadata_xml"], parser=XML_PARSER)
        try:
            result = get_resource_descriptor(xml_root)
        except TypeError:
            logger.debug(f"metadata_xml: {record['metadata_xml']}")
            raise
        return result


def get_resource_descriptor(
        record: dict) -> resourcedescriptor.RecordDescription:
    record_from_xml = {}

    # get metadata from xml
    try:
        xml = etree.fromstring(
            record["metadata_xml"], parser=XML_PARSER)

        record_from_xml = {
            'character_set': xml.xpath(
                "gmd:characterSet/gmd:MD_CharacterSetCode/text()",
                namespaces=xml.nsmap)[0],
            'hierarchy_level': xml.xpath(
                "gmd:hierarchyLevel/gmd:MD_ScopeCode/text()",
                namespaces=xml.nsmap)[0],
            'point_of_contact': xml.xpath(
                "gmd:contact[.//gmd:role//@codeListValue='pointOfContact']",
                namespaces=xml.nsmap
            )[0],
            'author': xml.xpath(
                "gmd:contact[.//gmd:role//@codeListValue='author']",
                namespaces=xml.nsmap
            )[0]
        }
    except (TypeError, KeyError):
        logger.warning(
            f"No metadata detail from xml found"
        )

    return resourcedescriptor.RecordDescription(
        uuid=record['uuid'],
        language=record.get('language', None),
        character_set=record_from_xml.get('character_set', ''),
        hierarchy_level=record_from_xml.get('hierarchy_level', ''),
        point_of_contact=get_contact_descriptor(record_from_xml.get('point_of_contact', '')),
        author=get_contact_descriptor(record_from_xml.get('author', '')),
        date_stamp=dateutil.parser.parse(
            record.get('date', None)).replace(tzinfo=dt.timezone.utc),
        reference_systems=[record_from_xml.get('srid', None)],
        identification=get_identification_descriptor(record),
        distribution=get_distribution_info(record),
        data_quality=record.get('data_quality_statement', None),
        # this is needed by map
        zoom=record.get('zoom', None),
        projection=record.get('projection', None),
        center_x=record.get('center_x', None),
        center_y=record.get('center_y', None),
        last_modified=record.get('last_modified', None),
    )


def get_contact_descriptor(contact: typing.Optional[etree.Element]) -> resourcedescriptor.RecordDescriptionContact:
    if contact:
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
    return resourcedescriptor.RecordDescriptionContact(
        role='',
        name='',
        organization='',
        position='',
        phone_voice='',
        phone_facsimile='',
        address_delivery_point='',
        address_city='',
        address_administrative_area='',
        address_postal_code='',
        address_country='',
        address_email=''
    )


def get_identification_descriptor(
        record: dict) -> resourcedescriptor.RecordIdentification:
    name = record.get('name', None)
    title = record.get('title', None)
    date = dateutil.parser.parse(
            record.get('date', None)).replace(tzinfo=dt.timezone.utc)
    date_type = record.get('date_type', None)
    abstract = record.get('abstract', None)
    purpose = record.get('purpose', None)
    status = None
    originator = get_contact_descriptor(None)
    graphic_overview_uri = None
    native_format = ''
    place_keywords = None
    other_keywords = record.get('keywords', None)
    licenses = []
    other_constraints = record.get('constraints_other', None)
    topic_category = None
    spatial_extent = geos.Polygon.from_ewkt(record.get('bbox_polygon', None))
    temporal_extent = None
    supplemental_information = record.get('supplemental_information', None)

    # check from metadata xml
    try:
        xml = etree.fromstring(
            record["metadata_xml"], parser=XML_PARSER)
        identification = xml.xpath("gmd:identificationInfo", namespaces=xml.nsmap)[0]

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

        # get all values
        name = get_xpath_value(identification, ".//gmd:citation//gmd:name")
        title = get_xpath_value(identification, ".//gmd:citation//gmd:title")
        date = dateutil.parser.parse(
            get_xpath_value(identification, ".//gmd:citation//gmd:date//gmd:date")
        ).replace(tzinfo=dt.timezone.utc)
        date_type = get_xpath_value(identification, ".//gmd:citation//gmd:dateType")
        abstract = get_xpath_value(identification, ".//gmd:abstract")
        purpose = get_xpath_value(identification, ".//gmd:purpose")
        status = get_xpath_value(identification, ".//gmd:status")
        originator = get_contact_descriptor(
            identification.xpath(
                ".//gmd:pointOfContact", namespaces=identification.nsmap)[0]
        )
        graphic_overview_uri = get_xpath_value(
            identification, ".//gmd:graphicOverview//gmd:fileName")
        native_format = get_xpath_value(
            identification, ".//gmd:resourceFormat//gmd:name")
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
        licenses = license_info.split(":", maxsplit=1)
        other_constraints = (
            f"{other_constraints_code or ''}:{other_constraints_description}")
        topic_category = get_xpath_value(identification, ".//gmd:topicCategory")
        spatial_extent = get_spatial_extent(identification)
        temporal_extent = get_temporal_extent(identification)
        supplemental_information = get_xpath_value(
            identification, ".//gmd:supplumentalInformation")
    except (TypeError, KeyError):
        logger.warning(
            f"No links metadata detail from xml found"
        )

    return resourcedescriptor.RecordIdentification(
        name=name,
        title=title,
        date=date,
        date_type=date_type,
        abstract=abstract,
        purpose=purpose,
        status=status,
        originator=originator,
        graphic_overview_uri=graphic_overview_uri,
        native_format=native_format,
        place_keywords=place_keywords,
        other_keywords=other_keywords,
        license=licenses,
        other_constraints=other_constraints,
        topic_category=topic_category,
        spatial_extent=spatial_extent,
        temporal_extent=temporal_extent,
        supplemental_information=supplemental_information
    )


def get_distribution_info(record: dict) -> resourcedescriptor.RecordDistribution:
    link = None
    wms = None
    wfs = None
    wcs = None
    thumbnail = None
    legend = None
    geojson = None
    original = None

    # check from metadata xml
    try:
        xml = etree.fromstring(
            record["metadata_xml"], parser=XML_PARSER)
        distribution = xml.xpath("gmd:distributionInfo", namespaces=xml.nsmap)[0]
        online_elements = distribution.xpath(
            ".//gmd:transferOptions//gmd:onLine", namespaces=distribution.nsmap)
        for online_el in online_elements:
            protocol = get_xpath_value(online_el, ".//gmd:protocol").lower()
            linkage = get_xpath_value(online_el, ".//gmd:linkage")
            description = (
                    get_xpath_value(online_el, ".//gmd:description") or "").lower()
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
    except (TypeError, KeyError):
        logger.warning(
            f"No links metadata detail from xml found"
        )
        # if no metadata on xml, use from record links
        for link in record.get('links', []):
            protocol = link['link_type'].lower()
            linkage = link['url']
            if "link" in protocol:
                link = linkage
            elif "ogc:wms" in protocol:
                wms = linkage
            elif "ogc:wfs" in protocol:
                wfs = linkage
            elif "ogc:wcs" in protocol:
                wcs = linkage
            elif "thumbnail" in link['name'].lower():
                thumbnail = linkage
            elif "legend" in link['name'].lower():
                legend = linkage
            elif "geojson" in link['name'].lower():
                geojson = linkage
            elif "original dataset" in link['name'].lower():
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
