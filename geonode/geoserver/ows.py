#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import ast
import typing
import logging

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from lxml import etree
from urllib.parse import urlencode, urljoin
from geonode.utils import (
    XML_PARSER,
    http_client,
    OGC_Servers_Handler)

logger = logging.getLogger(__name__)

ogc_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

DEFAULT_EXCLUDE_FORMATS = ['PNG', 'JPEG', 'GIF', 'TIFF']


def _get_nsmap(original: typing.Dict, key: str):
    """Prepare namespaces dict for running xpath queries.

    lxml complains when a namespaces dict has an entry with None as a key.

    """

    result = original.copy()
    try:
        result[key] = original[None]
    except KeyError:
        pass
    else:
        del result[None]

    return result


def _wcs_get_capabilities():
    try:
        wcs_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
    except Exception:
        wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wcs_url += '&' if '?' in wcs_url else '?'

    return wcs_url + urlencode({
        'service': 'WCS',
        'request': 'GetCapabilities',
        'version': '2.0.1',
    })


def _wcs_describe_coverage(coverage_id):
    try:
        wcs_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
    except Exception:
        wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wcs_url += '&' if '?' in wcs_url else '?'
    return wcs_url + urlencode({
        'service': 'WCS',
        'request': 'describecoverage',
        'version': '2.0.1',
        'coverageid': coverage_id
    })


def _get_wcs_axis_labels(coverage_id):

    def _swap(_axis_labels):
        if _axis_labels[0].lower() in 'lat':
            return [_axis_labels[1], _axis_labels[0]]
        else:
            return _axis_labels

    try:
        _describe_coverage_response, _content = http_client.get(_wcs_describe_coverage(coverage_id))
        _describe_coverage_response.raise_for_status()
        _root = etree.fromstring(_content.encode('UTF-8'), parser=XML_PARSER)
        _nsmap = _get_nsmap(_root.nsmap, 'wcs')
        _coverage_descriptions = _root.xpath("//wcs:CoverageDescription", namespaces=_nsmap)
        for _coverage_description in _coverage_descriptions:
            _envelope = _coverage_description.xpath("gml:boundedBy/gml:Envelope", namespaces=_nsmap)
            _axis_labels = _envelope[0].attrib["axisLabels"].split(" ")
            if _axis_labels and isinstance(_axis_labels, list) and len(_axis_labels) == 2:
                return _swap(_axis_labels)
    except Exception as e:
        logger.error(e)
    return None


def _wcs_link(wcs_url, identifier, mime, srid=None, bbox=None, compression=None, tile_size=None):
    coverage_id = identifier.replace(':', '__', 1)
    wcs_params = {
        'service': 'WCS',
        'request': 'GetCoverage',
        'coverageid': coverage_id,
        'format': mime,
        'version': '2.0.1',
    }

    if compression:
        wcs_params['compression'] = compression

    if tile_size:
        wcs_params['tileWidth'] = tile_size
        wcs_params['tileHeight'] = tile_size

    if srid:
        wcs_params['outputCrs'] = srid

    _wcs_params = urlencode(wcs_params)

    if bbox:
        _bbox = None
        if isinstance(bbox, list):
            _bbox = bbox
        elif isinstance(bbox, str):
            _bbox = ast.literal_eval(f'[{bbox}]') if all([_x in bbox for _x in ['[', ']']]) else ast.literal_eval(f'[{bbox}]')
        if _bbox:
            _axis_labels = _get_wcs_axis_labels(coverage_id)
            if _axis_labels:
                _wcs_params += f'&subset={_axis_labels[0]}({_bbox[0]},{_bbox[2]})&subset={_axis_labels[1]}({_bbox[1]},{_bbox[3]})'
    return f'{wcs_url}{_wcs_params}'


def wcs_links(wcs_url, identifier, bbox=None, srid=None):
    types = [
        ("x-gzip", _("GZIP"), "application/x-gzip", None, None),
        ("geotiff", _("GeoTIFF"), "image/tiff", "DEFLATE", 512),
    ]
    output = []
    for ext, name, mime, compression, tile_size in types:
        url = _wcs_link(wcs_url, identifier, mime, bbox=bbox, srid=srid, compression=compression, tile_size=tile_size)
        output.append((ext, name, mime, url))
    return output


def _wfs_get_capabilities():
    try:
        wfs_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
    except Exception:
        wfs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wfs_url += '&' if '?' in wfs_url else '?'

    return wfs_url + urlencode({
        'service': 'WFS',
        'request': 'GetCapabilities',
        'version': '1.1.0',
    })


def _wfs_link(wfs_url, identifier, mime, extra_params, bbox=None, srid=None):
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typename': identifier,
        'outputFormat': mime,
    }
    if srid:
        params['srs'] = srid
    if bbox:
        params['bbox'] = bbox
    params.update(extra_params)
    return wfs_url + urlencode(params)


def wfs_links(wfs_url, identifier, bbox=None, srid=None):
    types = [
        ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
        ("gml", _("GML 2.0"), "gml2", {}),
        ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
        ("csv", _("CSV"), "csv", {}),
        ("excel", _("Excel"), "excel", {}),
        ("json", _("GeoJSON"), "json", {'srsName': srid or 'EPSG:4326'})
    ]
    output = []
    for ext, name, mime, extra_params in types:
        url = _wfs_link(wfs_url, identifier, mime, extra_params, bbox=bbox, srid=srid)
        output.append((ext, name, mime, url))
    return output


def _wms_get_capabilities():
    try:
        wms_url = urljoin(settings.SITEURL, reverse('ows_endpoint'))
    except Exception:
        wms_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wms_url += '&' if '?' in wms_url else '?'

    return wms_url + urlencode({
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.3.0',
    })


def _wms_link(wms_url, identifier, mime, height, width, srid=None, bbox=None):
    wms_params = {
        'service': 'WMS',
        'request': 'GetMap',
        'layers': identifier,
        'format': mime,
        'height': height,
        'width': width,
    }
    if srid:
        wms_params['srs'] = srid
    if bbox:
        wms_params['bbox'] = bbox

    return wms_url + urlencode(wms_params)


def wms_links(wms_url, identifier, bbox, srid, height, width):
    types = [
        ("jpg", _("JPEG"), "image/jpeg"),
        ("pdf", _("PDF"), "application/pdf"),
        ("png", _("PNG"), "image/png"),
    ]
    output = []
    for ext, name, mime in types:
        url = _wms_link(wms_url, identifier, mime, height, width, srid, bbox)
        output.append((ext, name, mime, url))
    return output
