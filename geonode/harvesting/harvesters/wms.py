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
import uuid
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.contrib.gis import geos
from lxml import etree

from geonode.base.models import ResourceBase
from geonode.layers.models import Dataset

from . import base
from ..models import Harvester
from ..utils import (
    XML_PARSER,
    get_xpath_value,
)
from .. import resourcedescriptor

logger = logging.getLogger(__name__)


class OgcWmsHarvester(base.BaseHarvesterWorker):
    """Harvester for resources coming from OGC WMS web services"""

    dataset_title_filter: typing.Optional[str]
    _base_wms_parameters: typing.Dict = {
        "service": "WMS",
        "version": "1.3.0",
    }

    def __init__(
            self,
            *args,
            dataset_title_filter: typing.Optional[str] = None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.http_session = requests.Session()
        self.http_session.headers = {
            "Content-Type": "application/xml"
        }
        self.dataset_title_filter = dataset_title_filter

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, record: Harvester):
        return cls(
            record.remote_url,
            record.id,
            dataset_title_filter=record.harvester_type_specific_configuration.get(
                "dataset_title_filter")
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
                "dataset_title_filter": {
                    "type": "string",
                }
            },
            "additionalProperties": False,
        }

    def get_capabilities(self) -> requests.Response:
        params = self._base_wms_parameters.copy()
        params.update({
            "request": "GetCapabilities",
        })
        get_capabilities_response = self.http_session.get(
            self.remote_url, params=params)
        get_capabilities_response.raise_for_status()
        return get_capabilities_response

    def get_num_available_resources(self) -> int:
        data = self._get_data()
        return len(data['layers'])

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:

        # look at `tasks.update_harvestable_resources()` in order to understand the purpose of the
        # `offset` parameter. Briefly, we try to retrieve resources in batches and we use `offset` to
        # control the pagination of the remote service. Unfortunately WMS does not really have the
        # concept of pagination and dumps all available layers in a single `GetCapabilities` response.
        # With this in mind, we only handle the case where `offset == 0`, which returns all available resources
        # and simply return an empty list when `offset != 0`
        if offset != 0:
            return []

        resources = []
        data = self._get_data()
        for layer in data['layers']:
            resources.append(
                base.BriefRemoteResource(
                    unique_identifier=layer['name'],
                    title=layer['title'],
                    resource_type='layers',
                )
            )
        return resources

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        try:
            response = self.get_capabilities()
        except (requests.HTTPError, requests.ConnectionError):
            result = False
        else:
            try:
                root = etree.fromstring(response.content, parser=XML_PARSER)
            except etree.XMLSyntaxError:
                result = False
            else:
                if 'WMS_Capabilities' in root.tag:
                    result = True
                else:
                    result = False
        return result

    def get_geonode_resource_type(self, remote_resource_type: str) -> ResourceBase:
        """Return resource type class from resource type string."""
        # WMS just have Layer type on it's resource.
        # So whatever remote_resource_type it is, it always return Layer.
        return Dataset

    def get_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
            harvesting_session_id: int
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        resource_unique_identifier = harvestable_resource.unique_identifier
        data = self._get_data()
        result = None
        try:
            relevant_layer = [layer for layer in data["layers"] if layer["name"] == resource_unique_identifier][0]
        except IndexError:
            logger.exception(f"Could not find resource {resource_unique_identifier!r}")
        else:
            # WMS does not provide uuid, so needs to generated on the first time
            # for update, use uuid from geonode resource
            resource_uuid = uuid.uuid4()
            if harvestable_resource.geonode_resource:
                resource_uuid = uuid.UUID(harvestable_resource.geonode_resource.uuid)
            # WMS does not provide the date of the resource.
            # Use current time for the date stamp and resource time.
            time = datetime.now()
            contact = resourcedescriptor.RecordDescriptionContact(**data['contact'])
            result = base.HarvestedResourceInfo(
                resource_descriptor=resourcedescriptor.RecordDescription(
                    uuid=resource_uuid,
                    point_of_contact=contact,
                    author=contact,
                    date_stamp=time,
                    identification=resourcedescriptor.RecordIdentification(
                        name=relevant_layer['name'],
                        title=relevant_layer['title'],
                        date=time,
                        date_type='',
                        originator=contact,
                        graphic_overview_uri='',
                        place_keywords=[],
                        other_keywords=relevant_layer['keywords'],
                        license=[],
                        abstract=relevant_layer['abstract'],
                        spatial_extent=relevant_layer['spatial_extent']
                    ),
                    distribution=resourcedescriptor.RecordDistribution(
                        legend_url=relevant_layer['legend_url'],
                        wms_url=relevant_layer['wms_url']
                    ),
                    reference_systems=relevant_layer['crs'],
                ),
                additional_information=None
            )
        return result

    def _get_data(self) -> typing.Dict:
        """Return data from the harvester URL in JSON format."""
        get_capabilities_response = self.get_capabilities()
        root = etree.fromstring(get_capabilities_response.content, parser=XML_PARSER)
        nsmap = _get_nsmap(root.nsmap)

        layers = []
        leaf_layers = root.xpath("//wms:Layer[not(.//wms:Layer)]", namespaces=nsmap)
        for layer_element in leaf_layers:
            try:
                data = self._layer_element_to_json(layer_element)
                title = data['title']
                if self.dataset_title_filter is not None:
                    if self.dataset_title_filter.lower() not in title.lower():
                        continue
                layers.append(data)
            except Exception as e:
                logger.exception(e)
        return {
            'contact': self._get_contact(root),
            'layers': layers
        }

    def _get_contact(self, element: etree.Element) -> dict:
        """Return contact from element"""
        nsmap = _get_nsmap(
            element.nsmap)
        return {
            'role': '',
            'name': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactPersonPrimary/wms:ContactPerson", nsmap),
            'organization': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactPersonPrimary/wms:ContactOrganization", nsmap),
            'position': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactPosition", nsmap),
            'phone_voice': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactVoiceTelephone", nsmap),
            'phone_facsimile': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactFacsimileTelephone", nsmap),
            'address_delivery_point': '',
            'address_city': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactAddress/wms:City", nsmap),
            'address_administrative_area': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactAddress/wms:StateOrProvince", nsmap),
            'address_postal_code': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactAddress/wms:PostCode", nsmap),
            'address_country': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactAddress/wms:Country", nsmap),
            'address_email': get_xpath_value(
                element, "wms:Service/wms:ContactInformation/wms:ContactElectronicMailAddress", nsmap),
        }

    def _layer_element_to_json(self, layer_element: etree.Element) -> dict:
        """Return json of layer from xml element"""
        nsmap = _get_nsmap(
            layer_element.nsmap)
        name = get_xpath_value(
            layer_element, "wms:Name", nsmap)
        title = get_xpath_value(
            layer_element, "wms:Title", nsmap)
        abstract = get_xpath_value(
            layer_element, "wms:Abstract", nsmap)
        try:
            keywords = layer_element.xpath("wms:KeywordList/wms:Keyword/text()", namespaces=nsmap)
            keywords = [str(keyword) for keyword in keywords]
        except IndexError:
            keywords = []

        try:
            legend_url = layer_element.xpath(
                "wms:Style/wms:LegendURL/wms:OnlineResource",
                namespaces=nsmap
            )[0].attrib[f"{{{layer_element.nsmap['xlink']}}}href"]
        except (IndexError, KeyError):
            legend_url = ''
        params = self._base_wms_parameters
        wms_url = f"{self.remote_url}?{urlencode(params)}"

        try:
            crs = layer_element.xpath("wms:CRS//text()", namespaces=nsmap)[0]
            left_x = get_xpath_value(
                layer_element, "wms:EX_GeographicBoundingBox/wms:westBoundLongitude", nsmap)
            right_x = get_xpath_value(
                layer_element, "wms:EX_GeographicBoundingBox/wms:eastBoundLongitude", nsmap)
            lower_y = get_xpath_value(
                layer_element, "wms:EX_GeographicBoundingBox/wms:southBoundLatitude", nsmap)
            upper_y = get_xpath_value(
                layer_element, "wms:EX_GeographicBoundingBox/wms:northBoundLatitude", nsmap)

            # Preventing if it returns comma as the decimal separator
            spatial_extent = geos.Polygon.from_bbox((
                float(left_x.replace(",", ".")),
                float(lower_y.replace(",", ".")),
                float(right_x.replace(",", ".")),
                float(upper_y.replace(",", ".")),
            ))
        except IndexError:
            crs = None
            spatial_extent = None
        return {
            'name': name,
            'title': title,
            'abstract': abstract,
            'crs': crs,
            'keywords': keywords,
            'spatial_extent': spatial_extent,
            'wms_url': wms_url,
            'legend_url': legend_url,
        }


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
