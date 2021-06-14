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
from lxml import etree

from .. import resourcedescriptor
from ..utils import XML_PARSER
from . import base

logger = logging.getLogger(__name__)


class OgcWmsHarvester(base.BaseHarvesterWorker):
    """Harvester for resources coming from OGC WMS web services"""

    layer_title_filter: typing.Optional[str]
    _base_wms_parameters: typing.Dict = {
        "service": "WMS",
        "version": "1.3.0",
    }

    def __init__(
            self,
            *args,
            layer_title_filter: typing.Optional[str] = None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.http_session = requests.Session()
        self.http_session.headers = {
            "Content-Type": "application/xml"
        }
        self.layer_title_filter = layer_title_filter

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, record: "Harvester"):
        return cls(
            record.remote_url,
            record.id,
            layer_title_filter=record.harvester_type_specific_configuration.get(
                "layer_title_filter")
        )

    @classmethod
    def get_extra_config_schema(cls) -> typing.Optional[typing.Dict]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://geonode.org/harvesting/ogc-wms-harvester.schema.json",
            "title": "OGC WMS harvester config",
            "description": (
                "A jsonschema for validating configuration option for GeoNode's "
                "remote OGC WMS harvester"
            ),
            "type": "object",
            "properties": {
                "layer_title_filter": {
                    "type": "string",
                }
            },
            "additionalProperties": False,
        }

    def get_num_available_resources(self) -> int:
        raise NotImplementedError

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        raise NotImplementedError

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        try:
            response = self.http_session.get(f"{self.remote_url}")
            response.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError):
            result = False
        else:
            result = True
        return result

    def get_resource(
            self,
            resource_unique_identifier: str,
            resource_type: str,
            harvesting_session_id: typing.Optional[int] = None
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        params = self._base_wms_parameters
        params.update({
            "request": "GetCapabilities",
        })
        get_capabilities_response = self.http_session.get(
            self.remote_url, params=params)
        get_capabilities_response.raise_for_status()
        root = etree.fromstring(get_capabilities_response.content, parser=XML_PARSER)
        nsmap = _get_nsmap(root.nsmap)
        useful_layers_elements = []
        leaf_layers = root.xpath("//wms:Layer[not(.//wms:Layer)]", namespaces=nsmap)
        for layer_element in leaf_layers:
            try:
                title = layer_element.xpath("wms:Title/text()", namespaces=nsmap)[0]
            except IndexError:
                name = layer_element.xpath("wms:Name/text()", namespaces=nsmap)[0]
                title = name
            if self.layer_title_filter is not None:
                if self.layer_title_filter.lower() not in title.lower():
                    continue
            logger.debug(f"Creating resource descriptor for layer {title!r}...")
        self.update_harvesting_session(
            harvesting_session_id, total_records_found=len(useful_layers_elements))
        self.finish_harvesting_session(harvesting_session_id)

    def update_geonode_resource(
            self,
            resource_descriptor: resourcedescriptor.RecordDescription,
            harvesting_session_id: typing.Optional[int] = None
    ):
        raise NotImplementedError

    def _get_useful_layers(self) -> typing.List[etree.Element]:
        get_capabilities_response = self.http_session.get(
            self.remote_url,
            params={
                "service": "WMS",
                "version": "1.3.0",
                "request": "GetCapabilities",
            }
        )
        get_capabilities_response.raise_for_status()
        root = etree.fromstring(get_capabilities_response.content, parser=XML_PARSER)
        nsmap = _get_nsmap(root.nsmap)
        num_layers = 0
        useful_layers_elements = []
        leaf_layers = root.xpath("//wms:Layer[not(.//wms:Layer)]", namespaces=nsmap)
        for layer_element in leaf_layers:
            title = layer_element.xpath("wms:Title/text()", namespaces=nsmap)[0]
            if self.layer_title_filter is not None:
                if self.layer_title_filter.lower() not in title.lower():
                    continue
            useful_layers_elements.append(layer_element)
        return useful_layers_elements


def _get_nsmap(original: typing.Dict):
    """Prepare namespaces dict for running xpath queries.

    lxml complains when a namespaces dict has an entry with None as a key.

    """

    result = original.copy()
    try:
        result["wms"] = original[None]
    except KeyError:
        pass
    else:
        del result[None]
    return result
