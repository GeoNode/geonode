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
from functools import lru_cache
from urllib.parse import (
    unquote,
    urlparse,
    urlencode,
    parse_qsl,
    ParseResult
)

import requests
from lxml import etree

from owslib.map import wms111, wms130
from owslib.util import clean_ows_url

from django.conf import settings
from django.contrib.gis import geos
from django.template.defaultfilters import slugify

from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase
from geonode.layers.enumerations import GXP_PTYPES
from geonode.thumbs.thumbnails import create_thumbnail

from .. import models
from geonode.utils import (
    XML_PARSER,
    get_xpath_value,
)
from .. import resourcedescriptor

from . import base

logger = logging.getLogger(__name__)


@lru_cache()
def WebMapService(url,
                  version='1.3.0',
                  xml=None,
                  username=None,
                  password=None,
                  parse_remote_metadata=False,
                  timeout=30,
                  headers=None):
    """
    API for Web Map Service (WMS) methods and metadata.
    """
    '''wms factory function, returns a version specific WebMapService object

    @type url: string
    @param url: url of WFS capabilities document
    @type xml: string
    @param xml: elementtree object
    @type parse_remote_metadata: boolean
    @param parse_remote_metadata: whether to fully process MetadataURL elements
    @param timeout: time (in seconds) after which requests should timeout
    @return: initialized WebFeatureService_2_0_0 object
    '''

    clean_url = clean_ows_url(url)
    base_ows_url = clean_url

    if version in ['1.1.1']:
        return (
            base_ows_url,
            wms111.WebMapService_1_1_1(
                clean_url, version=version, xml=xml,
                parse_remote_metadata=parse_remote_metadata,
                username=username, password=password,
                timeout=timeout, headers=headers
            )
        )
    elif version in ['1.3.0']:
        return (
            base_ows_url,
            wms130.WebMapService_1_3_0(
                clean_url, version=version, xml=xml,
                parse_remote_metadata=parse_remote_metadata,
                username=username, password=password,
                timeout=timeout, headers=headers
            )
        )
    raise NotImplementedError(
        f'The WMS version ({version}) you requested is not implemented. Please use 1.1.1 or 1.3.0.')


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
    def from_django_record(cls, record: models.Harvester):
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

    @classmethod
    def get_wms_operations(cls, url, version=None) -> typing.Optional[typing.Dict]:
        operations = {}
        try:
            _url, _parsed_service = WebMapService(
                url,
                version=version)
            for _op in _parsed_service.operations:
                _methods = []
                for _op_method in (getattr(_op, 'methods', []) if hasattr(_op, 'methods') else _op.get('methods', [])):
                    _methods.append(
                        {
                            'type': _op_method.get('type', None),
                            'url': _op_method.get('url', None)
                        }
                    )

                _name = getattr(_op, 'name', None) if hasattr(_op, 'name') else _op.get('name', None)
                _formatOptions = getattr(_op, 'formatOptions', []) if hasattr(_op, 'formatOptions') else _op.get('formatOptions', [])
                if _name:
                    operations[_name] = {
                        'name': _name,
                        'methods': _methods,
                        'formatOptions': _formatOptions
                    }
        except Exception as e:
            logger.debug(e)
        return operations

    def get_ogc_wms_url(self, wms_url, version=None):
        ogc_wms_url = f"{wms_url.scheme}://{wms_url.netloc}{wms_url.path}"
        try:
            operations = OgcWmsHarvester.get_wms_operations(wms_url.geturl(), version=version)
            ogc_wms_get_capabilities = operations.get('GetCapabilities', None)
            if ogc_wms_get_capabilities and ogc_wms_get_capabilities.get('methods', None):
                for _op_method in ogc_wms_get_capabilities.get('methods'):
                    if _op_method.get('type', None).upper() == 'GET' and _op_method.get('url', None):
                        ogc_wms_url = _op_method.get('url')
                        break
        except Exception as e:
            logger.exception(e)
        return ogc_wms_url

    def get_capabilities(self) -> requests.Response:
        params = self._base_wms_parameters.copy()
        params.update({
            "request": "GetCapabilities",
        })
        (wms_url, _service, _version, _request) = self._get_cleaned_url_params(self.remote_url)
        if _service:
            params['service'] = _service
        if _version:
            params['version'] = _version
        if wms_url.query:
            for _param in parse_qsl(wms_url.query):
                params[_param[0]] = _param[1]

        get_capabilities_response = self.http_session.get(
            self.get_ogc_wms_url(wms_url, version=_version), params=params)
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
            name = layer['name']
            title = layer.get('title') or name.rpartition(':')[-1]
            resources.append(
                base.BriefRemoteResource(
                    unique_identifier=name,
                    title=title,
                    abstract=layer['abstract'],
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

    def get_geonode_resource_defaults(
            self,
            harvested_info: base.HarvestedResourceInfo,
            harvestable_resource: models.HarvestableResource,  # noqa
    ) -> typing.Dict:
        defaults = super().get_geonode_resource_defaults(harvested_info, harvestable_resource)
        defaults["name"] = harvested_info.resource_descriptor.identification.name
        defaults.update(harvested_info.resource_descriptor.additional_parameters)
        return defaults

    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
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
            service_name = slugify(self.remote_url)[:255]
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
                        place_keywords=[],
                        other_keywords=relevant_layer['keywords'],
                        license=[],
                        abstract=relevant_layer['abstract'],
                        spatial_extent=relevant_layer['spatial_extent']
                    ),
                    distribution=resourcedescriptor.RecordDistribution(
                        wms_url=relevant_layer['wms_url'],
                    ),
                    reference_systems=[relevant_layer['crs']],
                    additional_parameters={
                        'alternate': relevant_layer["name"],
                        'store': service_name,
                        'workspace': 'remoteWorkspace',
                        'ows_url': relevant_layer['wms_url'],
                        'ptype': GXP_PTYPES["WMS"]
                    }
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

    def _get_cleaned_url_params(self, url):
        # Unquoting URL first so we don't loose existing args
        url = unquote(url)
        # Extracting url info
        parsed_url = urlparse(url)
        # Extracting URL arguments from parsed URL
        get_args = parsed_url.query
        # Converting URL arguments to dict
        parsed_get_args = dict(parse_qsl(get_args))
        # Strip out redoundant args
        _version = parsed_get_args.pop('version', '1.3.0') if 'version' in parsed_get_args else '1.3.0'
        _service = parsed_get_args.pop('service') if 'service' in parsed_get_args else None
        _request = parsed_get_args.pop('request') if 'request' in parsed_get_args else None
        # Converting URL argument to proper query string
        encoded_get_args = urlencode(parsed_get_args, doseq=True)
        # Creating new parsed result object based on provided with new
        # URL arguments. Same thing happens inside of urlparse.
        new_url = ParseResult(
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, encoded_get_args, parsed_url.fragment
        )
        return (new_url, _service, _version, _request)

    def _layer_element_to_json(self, layer_element: etree.Element) -> dict:
        """Return json of layer from xml element"""
        nsmap = _get_nsmap(
            layer_element.nsmap)
        nsmap['xlink'] = "http://www.w3.org/1999/xlink"
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
            )[0].attrib[f"{{{nsmap['xlink']}}}href"]
        except (IndexError, KeyError):
            legend_url = ''
        params = {}
        (wms_url, _service, _version, _request) = self._get_cleaned_url_params(self.remote_url)
        if _service:
            params['service'] = _service
        if _version:
            params['version'] = _version
        if wms_url.query:
            for _param in parse_qsl(wms_url.query):
                params[_param[0]] = _param[1]

        wms_url = self.get_ogc_wms_url(
            wms_url._replace(query=urlencode(params)),
            version=_version)

        crs = None
        spatial_extent = None
        try:
            for bbox in layer_element.xpath("wms:BoundingBox", namespaces=nsmap):
                crs = bbox.attrib.get('CRS')
                if 'EPSG:' in crs.upper() or crs.upper() == 'CRS:84':
                    crs = 'EPSG:4326' if crs.upper() == 'CRS:84' else crs
                    left_x = bbox.attrib.get('minx')
                    right_x = bbox.attrib.get('maxx')
                    lower_y = bbox.attrib.get('miny')
                    upper_y = bbox.attrib.get('maxy')

                    # Preventing if it returns comma as the decimal separator
                    spatial_extent = geos.Polygon.from_bbox((
                        float(left_x.replace(",", ".")),
                        float(lower_y.replace(",", ".")),
                        float(right_x.replace(",", ".")),
                        float(upper_y.replace(",", ".")),
                    ))
                    break
            if not spatial_extent:
                crs = None
                raise Exception("No suitable wms:BoundingBox element found!")
        except Exception as e:
            logger.exception(e)
            try:
                for crs in layer_element.xpath("wms:CRS//text()", namespaces=nsmap):
                    if 'EPSG:' in crs.upper() or crs.upper() == 'CRS:84':
                        crs = 'EPSG:4326' if crs.upper() == 'CRS:84' else crs
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
                        break
                if not spatial_extent:
                    crs = None
                    raise Exception("No suitable wms:CRS element found!")
            except Exception as e:
                logger.exception(e)
                spatial_extent = None
            if not spatial_extent:
                crs = "EPSG:4326"
                spatial_extent = geos.Polygon.from_bbox((
                    -180.0,
                    -90.0,
                    180.0,
                    90.0
                ))
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

    def finalize_resource_update(
            self,
            geonode_resource: ResourceBase,
            harvested_info: base.HarvestedResourceInfo,
            harvestable_resource: models.HarvestableResource
    ) -> ResourceBase:
        """Create a thumbnail with a WMS request."""
        if not geonode_resource.srid:
            target_crs = settings.DEFAULT_MAP_CRS
        elif 'EPSG:' in str(geonode_resource.srid).upper() or 'CRS:' in str(geonode_resource.srid).upper():
            target_crs = geonode_resource.srid
        else:
            target_crs = f'EPSG:{geonode_resource.srid}'
        create_thumbnail(
            instance=geonode_resource,
            # wms_version=harvested_info.resource_descriptor,
            bbox=geonode_resource.bbox,
            forced_crs=target_crs,
            overwrite=True,
        )


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
