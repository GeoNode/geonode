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

import logging
import typing

import requests
from django.template.loader import render_to_string
from lxml import etree

from .base import BaseHarvester

logger = logging.getLogger(__name__)


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
        self.update_harvesting_session()
        try:
            total_records = self._get_existing_records()
            logger.info(f"total_records: {total_records}")
        except requests.HTTPError as exc:
            logger.exception(f"Could not contact {self.remote_url!r}")
        except AttributeError as exc:
            logger.exception(f"Could not extract total number of records")
        else:
            self.finish_harvesting_session(records_harvested=total_records)

    def _get_existing_records(self) -> int:
        payload = render_to_string(
            "harvesting/harvesters_geonode_get_records.xml",
            {
                "max_records": self.max_records,
                "typename": self.typename,
                "result_type": "hits",
            }
        )
        get_records_response = self.http_session.post(
            self.catalogue_url,
            data=payload
        )
        get_records_response.raise_for_status()
        root = etree.fromstring(get_records_response.content)
        # logger.debug(etree.tostring(root, pretty_print=True))
        result = int(
            root.xpath(
                "csw:SearchResults/@numberOfRecordsMatched", namespaces=root.nsmap)[0]
        )
        return result