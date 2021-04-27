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
import logging
import math
import typing
import uuid

import dateutil.parser
import requests
from celery import chord
from django.contrib.gis import geos
from django.template.loader import render_to_string
from lxml import etree

from .. import resourcedescriptor
from ..utils import XML_PARSER
from .base import BaseHarvester
from . import tasks

logger = logging.getLogger(__name__)


class GeonodeLegacyHarvester(BaseHarvester):
    harvest_documents: bool
    harvest_layers: bool
    harvest_maps: bool
    resource_title_filter: typing.Optional[str]
    http_session: requests.Session
    page_size: int = 10

    def __init__(
            self,
            *args,
            harvest_documents: typing.Optional[bool] = True,
            harvest_layers: typing.Optional[bool] = True,
            harvest_maps: typing.Optional[bool] = True,
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
        self.resource_title_filter = resource_title_filter

    @property
    def base_api_url(self):
        return f"{self.remote_url}/api"

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

    def get_extra_config_schema(self) -> typing.Dict:
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

    def perform_metadata_harvesting(self) -> None:
        harvesting_session_id = self.create_harvesting_session()
        total_resources = 0
        harvesting_batches = []
        for resource_type_suffix in ("documents", "layers", "maps"):
            total_records = self._get_total_records(resource_type_suffix)
            num_pages = math.ceil(total_records / self.page_size)
            total_resources += total_records
            harvesting_batches.extend(
                self._generate_harvest_batches(
                    num_pages, harvesting_session_id, resource_type_suffix)
            )
        logger.debug(
            f"There are {total_resources!r} resources that match the current "
            f"configuration on the remote"
        )
        self.update_harvesting_session(total_records_found=total_resources)
        harvesting_finalizer = tasks.finalize_harvesting_session.signature(
            args=(harvesting_session_id,), immutable=True)
        harvesting_workflow = chord(harvesting_batches, body=harvesting_finalizer)
        harvesting_workflow.apply_async()

    def harvest_record_batch(self, endpoint_suffix: str, offset: int):
        request_params = self._get_resource_list_params()
        request_params["offset"] = offset
        response = self.http_session.get(
            f"{self.base_api_url}/{endpoint_suffix}/",
            params=request_params
        )
        response.raise_for_status()
        brief_record_list = response.json().get("objects", [])
        record_descriptions = []
        for index, brief_record in enumerate(brief_record_list):
            logger.debug(
                f"Harvesting {endpoint_suffix!r} batch "
                f"{index + 1}/{len(brief_record_list)}..."
            )
            detail_url = f"{self.base_api_url}{brief_record['detail_url']}"
            # we get the full record representation because that contains more
            # information, including embedded CSW GetRecord too
            full_record_response = self.http_session.get(detail_url)
            full_record_response.raise_for_status()
            full_record = full_record_response.json()
            record_description = self._get_resource_descriptor(full_record)
            logger.debug(
                f"Found details for record {record_description.uuid!r} - "
                f"{record_description.identification.title!r}"
            )
            record_descriptions.append(record_description)
            self.update_harvesting_session(additional_harvested_records=1)

    def _generate_harvest_batches(
            self,
            num_pages: int,
            session_id: int,
            endpoint_suffix: str
    ) -> typing.List[typing.Callable]:
        batches = []
        for page in range(num_pages):
            logger.debug(
                f"Creating batch for {endpoint_suffix!r}, page "
                f"({page + 1!r}/{num_pages})..."
            )
            pagination_offset = page * self.page_size
            batches.append(
                tasks.harvest_record_batch.signature(
                    args=(session_id, pagination_offset),
                    kwargs={"endpoint_suffix": endpoint_suffix}
                )
            )
        return batches

    def _get_resource_list_params(self) -> typing.Dict:
        result = {
            "limit": self.page_size
        }
        if self.resource_title_filter is not None:
            result["title__icontains"] = self.resource_title_filter
        return result

    def _get_total_records(
            self,
            endpoint_suffix: str,
    ) -> int:
        response = self.http_session.get(
            f"{self.base_api_url}/{endpoint_suffix}/",
            params=self._get_resource_list_params()
        )
        response.raise_for_status()
        return response.json().get("meta", {}).get("total_count", 0)

    def _get_resource_descriptor(
            self, record: typing.Dict) -> resourcedescriptor.RecordDescription:
        xml_root = etree.fromstring(record["metadata_xml"], parser=XML_PARSER)
        return get_resource_descriptor(xml_root)


class GeonodeCswHarvester(BaseHarvester):
    http_session: requests.Session
    max_records: int = 10
    typename: str = "gmd:MD_Metadata"

    @property
    def catalogue_url(self):
        return f"{self.remote_url}/catalogue/csw"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_session = requests.Session()
        self.http_session.headers = {
            "Content-Type": "application/xml"
        }

    def perform_metadata_harvesting(self):
        """Main harvesting entrypoint

        This method dispatches batches of async tasks to perform the actual harvesting.
        Implementation roughly follows this workflow:

        1. Create a new harvesting session
        2. Find out how many records exist on the remote service
        3. Create batches of records to be harvested, whereby each batch processes as
           much records as the GeoNode CSW API returns on each page of GetRecords
           results
        4. Send each batch into the task queue in order to be processed later

        """

        harvesting_session_id = self.create_harvesting_session()
        try:
            total_records, page_size = self.find_number_of_records()
            self.update_harvesting_session(total_records_found=total_records)
            num_pages = math.ceil(total_records / page_size)
            logger.info(
                f"total_records: {total_records} - page_size: {page_size!r} - "
                f"num_pages: {num_pages!r}"
            )
            harvesting_finalizer = tasks.finalize_harvesting_session.signature(
                args=(harvesting_session_id,), immutable=True)
            harvesting_batches = []
            for current_page in range(num_pages):
                start_index = current_page * page_size
                logger.debug(f"Creating batch with start_index {start_index!r}...")
                harvesting_batches.append(
                    tasks.harvest_csw_records.signature(
                        args=(harvesting_session_id, start_index, page_size))
                )
            harvesting_workflow = chord(harvesting_batches, body=harvesting_finalizer)
            harvesting_workflow.apply_async()
        except requests.HTTPError as exc:
            logger.exception(f"Could not contact {self.remote_url!r}")
        except AttributeError as exc:
            logger.exception(f"Could not extract total number of records")
        except ZeroDivisionError:
            logger.exception("Received invalid page_size from server")

    def harvest_record_batch(self, start_index: int, page_size: int):
        """Harvest a batch of records.

        This method is usually called by the
        `geonode.harvesting.harvesters.tasks.harvest_records` task. It is used to
        perform a CSW GetRecords request to the remote GeoNode service. The response
        is then parsed into a list of `RecordDescription` instances, making them
        ready for being ingested into this instance of GeoNode.

        """

        logger.debug(
            f"Inside harvest_record_batch. start_index: {start_index} - "
            f"page_size: {page_size}"
        )
        get_records_response = self.http_session.post(
            self.catalogue_url,
            data=render_to_string(
                "harvesting/harvesters_geonode_get_records.xml",
                {
                    "start_position": start_index,
                    "max_records": page_size,
                    "typename": self.typename,
                    "result_type": "results",
                }
            )
        )
        logger.debug(
            f"get_records_response.status_code: {get_records_response.status_code}")
        get_records_response.raise_for_status()
        root = etree.fromstring(get_records_response.content, parser=XML_PARSER)
        # logger.debug(etree.tostring(root, pretty_print=True))
        records = root.xpath(
            f"csw:SearchResults/{self.typename}", namespaces=root.nsmap)
        logger.debug(f"records: {records}")
        record_descriptions = []
        for index, record in enumerate(records):
            logger.debug(
                f"Harvesting metadata from record {index + 1}/{len(records)}...")
            if len(record) == 0:  # skip empty records
                continue
            record_description = get_resource_descriptor(record)
            logger.debug(
                f"Found details for record {record_description.uuid!r} - "
                f"{record_description.identification.title!r}"
            )
            record_descriptions.append(record_description)
        self.update_harvesting_session(
            additional_harvested_records=len(record_descriptions))

    def find_number_of_records(self) -> typing.Tuple[int, int]:
        payload = render_to_string(
            "harvesting/harvesters_geonode_get_records.xml",
            {
                "result_type": "hits",
                "start_position": 1,
                "max_records": self.max_records,
                "typename": self.typename,
            }
        )
        get_records_response = self.http_session.post(
            self.catalogue_url,
            data=payload
        )
        get_records_response.raise_for_status()
        root = etree.fromstring(get_records_response.content, parser=XML_PARSER)
        # logger.debug(etree.tostring(root, pretty_print=True))
        total_records = int(
            root.xpath(
                "csw:SearchResults/@numberOfRecordsMatched", namespaces=root.nsmap)[0]
        )
        page_size = int(
            root.xpath(
                "csw:SearchResults/@numberOfRecordsReturned", namespaces=root.nsmap)[0]
        )
        return total_records, page_size


def get_resource_descriptor(record: etree.Element):
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
        reference_system=f"EPSG:{crs_epsg_code}",
        identification=get_identification_descriptor(
            record.xpath("gmd:identificationInfo", namespaces=record.nsmap)[0]
        ),
        distribution=get_distribution_info(
            record.xpath("gmd:distributionInfo", namespaces=record.nsmap)[0]
        ),
        data_quality=get_xpath_value(record, ".//gmd:dataQualityInfo//gmd:lineage")
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
