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
    """
    This is a utiliy method using the GeoNode Proxy to fetch the "DescribeCoverage".
    The outcome will be used to fetch the "Envelope" "axisLabels", that the WCS declares accordingly to the provided "outputCrs".

    The response will be something like the following here below:

    <?xml version="1.0" encoding="UTF-8"?>
    <wcs:CoverageDescriptions
      xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:ows="http://www.opengis.net/ows/2.0"
      xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:gmlcov="http://www.opengis.net/gmlcov/1.0"
      xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:swe="http://www.opengis.net/swe/2.0" xmlns:wcsgs="http://www.geoserver.org/wcsgs/2.0"
    xsi:schemaLocation="
      http://www.opengis.net/wcs/2.0 http://schemas.opengis.net/wcs/2.0/wcsDescribeCoverage.xsd
      http://www.geoserver.org/wcsgs/2.0
      http://localhost:8080/geoserver/schemas/wcs/2.0/wcsgs.xsd">
    <wcs:CoverageDescription gml:id="geonode__gebco_2020_n54_0659179519862_s51_64453104883433_w0_5559082031249998_e4_409911975264549">
        <gml:description>Generated from WorldImage</gml:description>
        <gml:name>gebco_2020_n54.0659179519862_s51.64453104883433_w0.5559082031249998_e4.409911975264549</gml:name>
        <gml:boundedBy>
        <gml:Envelope srsName="http://www.opengis.net/def/crs/EPSG/0/404000" axisLabels="x y" uomLabels="m m" srsDimension="2">
            <gml:lowerCorner>-0.5 -0.5</gml:lowerCorner>
            <gml:upperCorner>580.5 924.5</gml:upperCorner>
        </gml:Envelope>
        </gml:boundedBy>
        <wcs:CoverageId>geonode__gebco_2020_n54_0659179519862_s51_64453104883433_w0_5559082031249998_e4_409911975264549</wcs:CoverageId>
        <gml:coverageFunction>
        <gml:GridFunction>
            <gml:sequenceRule axisOrder="+2 +1">Linear</gml:sequenceRule>
            <gml:startPoint>0 0</gml:startPoint>
        </gml:GridFunction>
        </gml:coverageFunction>
        <gmlcov:metadata>
        <gmlcov:Extension>
            <ows:Keywords>
            <ows:Keyword>gebco_2020_n54.0659179519862_s51.64453104883433_w0.5559082031249998_e4.409911975264549</ows:Keyword>
            <ows:Keyword>WCS</ows:Keyword>
            <ows:Keyword>WorldImage</ows:Keyword>
            </ows:Keywords>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="..."/>
            <ows:Metadata xlink:type="simple" xlink:href="http://localhost:8000/showmetadata/xsl/42"/>
        </gmlcov:Extension>
        </gmlcov:metadata>
        <gml:domainSet>
        <gml:RectifiedGrid gml:id="grid00__geonode__gebco_2020_n54_0659179519862_s51_64453104883433_w0_5559082031249998_e4_409911975264549" dimension="2">
            <gml:limits>
            <gml:GridEnvelope>
                <gml:low>0 0</gml:low>
                <gml:high>924 580</gml:high>
            </gml:GridEnvelope>
            </gml:limits>
            <gml:axisLabels>i j</gml:axisLabels>
            <gml:origin>
            <gml:Point gml:id="p00_geonode__gebco_2020_n54_0659179519862_s51_64453104883433_w0_5559082031249998_e4_409911975264549" srsName="http://www.opengis.net/def/crs/EPSG/0/404000">
                <gml:pos>0.0 0.0</gml:pos>
            </gml:Point>
            </gml:origin>
            <gml:offsetVector srsName="http://www.opengis.net/def/crs/EPSG/0/404000">0.0 1.0</gml:offsetVector>
            <gml:offsetVector srsName="http://www.opengis.net/def/crs/EPSG/0/404000">1.0 0.0</gml:offsetVector>
        </gml:RectifiedGrid>
        </gml:domainSet>
        <gmlcov:rangeType>
        <swe:DataRecord>
            <swe:field name="GRAY_INDEX">
            <swe:Quantity>
                <swe:description>GRAY_INDEX</swe:description>
                <swe:uom code="W.m-2.Sr-1"/>
                <swe:constraint>
                <swe:AllowedValues>
                    <swe:interval>0 65535</swe:interval>
                </swe:AllowedValues>
                </swe:constraint>
            </swe:Quantity>
            </swe:field>
        </swe:DataRecord>
        </gmlcov:rangeType>
        <wcs:ServiceParameters>
        <wcs:CoverageSubtype>RectifiedGridCoverage</wcs:CoverageSubtype>
        <wcs:nativeFormat>image/tiff</wcs:nativeFormat>
        </wcs:ServiceParameters>
    </wcs:CoverageDescription>
    </wcs:CoverageDescriptions>
    """

    def _swap(_axis_labels):
        # WCS 2.0.1 swaps the order of the Lon/Lat axis to Lat/Lon.
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
    """
    Utility method generating a "GetCoverage" URL by fixing some parameters, like the "axisLabels"

    e.g.:
    http://localhost:8080/geoserver/ows?
     service=WCS&
     request=GetCoverage&
     coverageid=geonode__relief_san_andres0&
     format=image%2Ftiff&
     version=2.0.1&
     compression=DEFLATE&
     tileWidth=512&
     tileHeight=512&
     outputCrs=EPSG%3A4326&
     subset=Long(-84.0,-78.0)&
     subset=Lat(11.0,15.0)
    """
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
    """
    Creates the WCS GetCoverage Default download links.

    By providing 'None' bbox and srid, we are going to ask to the WCS to
    skip subsetting, i.e. output the whole coverage in the netive SRS.

    Notice that the "wcs_links" method also generates 1 default "outputFormat":
    - "geotiff"; GeoTIFF which will be compressed and tiled by passing to the WCS the default query params compression='DEFLATE' and tile_size=512
    """
    types = [
        # AF: Slow outputFormat, removed -> ("x-gzip", _("GZIP"), "application/x-gzip", None, None),
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
