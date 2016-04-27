# -*- coding: utf-8 -*-
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

import logging

from django.utils.translation import ugettext_lazy as _
import urllib

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_FORMATS = ['PNG', 'JPEG', 'GIF', 'TIFF']


def _wcs_link(wcs_url, identifier, mime):
    return wcs_url + urllib.urlencode({
        'service': 'WCS',
        'request': 'GetCoverage',
        'coverageid': identifier,
        'format': mime,
        'version': '2.0.1'
    })


def wcs_links(wcs_url, identifier):
    types = [
        ("x-gzip", _("GZIP"), "application/x-gzip"),
        ("geotiff", _("GeoTIFF"), "image/tiff"),
    ]
    output = []
    for ext, name, mime in types:
        url = _wcs_link(wcs_url, identifier, mime)
        output.append((ext, name, mime, url))
    return output


def _wfs_link(wfs_url, identifier, mime, extra_params):
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typename': identifier,
        'outputFormat': mime
    }
    params.update(extra_params)
    return wfs_url + urllib.urlencode(params)


def wfs_links(wfs_url, identifier):
    types = [
        ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
        ("gml", _("GML 2.0"), "gml2", {}),
        ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
        ("csv", _("CSV"), "csv", {}),
        ("excel", _("Excel"), "excel", {}),
        ("json", _("GeoJSON"), "json", {'srsName': 'EPSG:4326'})
    ]
    output = []
    for ext, name, mime, extra_params in types:
        url = _wfs_link(wfs_url, identifier, mime, extra_params)
        output.append((ext, name, mime, url))
    return output


def _wms_link(wms_url, identifier, mime, height, width, srid, bbox):
    return wms_url + urllib.urlencode({
        'service': 'WMS',
        'request': 'GetMap',
        'layers': identifier,
        'format': mime,
        'height': height,
        'width': width,
        'srs': srid,
        'bbox': bbox,
    })


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
