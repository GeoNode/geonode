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
from django.template.loader import render_to_string
from lxml import etree

from .. import resourcedescriptor
from .base import BaseHarvester
from . import tasks

logger = logging.getLogger(__name__)


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
        reference_system=f"EPSG:{crs_epsg_code}"
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
    other_keywords = "".join(
        identification.xpath(
            ".//gmd:descriptiveKeywords//gmd:keyword//text()[../../../gmd:type//"
            "@codeListValue!='place']",
            namespaces=identification.nsmap
        )
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

    )


class GeonodeHarvester(BaseHarvester):
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

        1. Find out how may records exist on the remote service
        2. Create batches of records to be harvested
        3. Send each batch into the task queue in order to be processed later

        """

        self.update_harvesting_session()
        try:
            total_records, page_size = self.find_number_of_records()
            self.update_harvesting_session(total_records_found=total_records)
            num_pages = math.ceil(total_records / page_size)
            logger.info(f"total_records: {total_records}")
            logger.info(f"page_size: {page_size}")
            logger.info(f"num_pages: {num_pages}")
            harvesting_session = self.get_harvesting_session()
            harvesting_finalizer = tasks.finalize_harvesting_session.signature(
                args=(harvesting_session.id,))
            harvesting_batches = []
            for current_page in range(num_pages):
                start_index = current_page * page_size
                logger.debug(f"Creating batch with start_index {start_index!r}...")
                harvesting_batches.append(
                    tasks.harvest_records.signature(
                        args=(harvesting_session.id, start_index, page_size))
                )
            harvesting_workflow = chord(harvesting_batches, body=harvesting_finalizer)
            # max_retries is used to prevent an infinite loop of celery's chord_unlock
            # task, as mentioned in:
            # https://github.com/celery/celery/issues/1700#issuecomment-167681486
            # the issued linked above seems to also be relevant for celery result
            # backends other than redis and memcached
            harvesting_workflow.apply_async(max_retries=5, interval=1)

        except requests.HTTPError as exc:
            logger.exception(f"Could not contact {self.remote_url!r}")
        except AttributeError as exc:
            logger.exception(f"Could not extract total number of records")
        except ZeroDivisionError:
            logger.exception("Received invalid page_size from server")
        finally:
            self.finish_harvesting_session()

    def harvest_record_batch(self, start_index: int, page_size: int):
        logger.debug(
            f"Inside harvest_record_batch. sta_index: {start_index} - "
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
        # TODO: implement error handling
        get_records_response.raise_for_status()
        root = etree.fromstring(get_records_response.content)
        logger.debug(etree.tostring(root, pretty_print=True))
        records = root.xpath(
            f"csw:SearchResults/{self.typename}", namespaces=root.nsmap)
        record_descriptions = []
        for index, record in enumerate(records):
            logger.debug(f"Harvesting metadata from record {index}/{len(records)}...")
            if len(record) == 0:  # skip empty records
                continue
            record_description = get_resource_descriptor(record)
            logger.debug(f"Found details for record {record_description.uuid!r}")
            record_descriptions.append(record_description)
        session = self.get_harvesting_session()
        self.update_harvesting_session(
            records_harvested=session.records_harvested + len(record_descriptions))

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
        root = etree.fromstring(get_records_response.content)
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
#
#
# def get_xpath_value(
#         element: etree.Element,
#         xpath_prefix: str,
#         xpath_suffix: typing.Optional[str] = "gco:CharacterString/text()"
# ) -> typing.Optional[str]:
#     if xpath_suffix:
#         xpath_expression = f"{xpath_prefix}/{xpath_suffix}"
#     else:
#         xpath_expression = xpath_prefix
#     values = element.xpath(xpath_expression, namespaces=element.nsmap)
#     try:
#         result = values[0].strip()
#     except IndexError:
#         result = None
#     return result or None


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
) -> typing.Optional[str]:
    values = element.xpath(f"{xpath_expression}//text()", namespaces=element.nsmap)
    return "".join(values).strip() or None


def _get_optional_attribute_value(
        element: etree.Element, xpath: str) -> typing.Optional[str]:
    return element.xpath(f"{xpath}/text()", namespaces=element.nsmap)[0].strip() or None
