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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import urllib
from urlparse import urljoin

from .helpers import OGC_Servers_Handler

logger = logging.getLogger(__name__)

ogc_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

DEFAULT_EXCLUDE_FORMATS = ['PNG', 'JPEG', 'GIF', 'TIFF']


def _wcs_get_capabilities():
    try:
        wcs_url = urljoin(settings.SITEURL, reverse('wcs_endpoint'))
    except BaseException:
        wcs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wcs_url += '&' if '?' in wcs_url else '?'

    return wcs_url + urllib.urlencode({
        'service': 'WCS',
        'request': 'GetCapabilities',
        'version': '2.0.1',
    })


def _wcs_link(wcs_url, identifier, mime, srid=None, bbox=None):
    wcs_params = {
        'service': 'WCS',
        'request': 'GetCoverage',
        'coverageid': identifier,
        'format': mime,
        'version': '2.0.1',
    }
    if srid:
        wcs_params['srs'] = srid
    if bbox:
        wcs_params['bbox'] = bbox
    return wcs_url + urllib.urlencode(wcs_params)


def wcs_links(wcs_url, identifier, bbox=None, srid=None):
    types = [
        ("x-gzip", _("GZIP"), "application/x-gzip"),
        ("geotiff", _("GeoTIFF"), "image/tiff"),
    ]
    output = []
    for ext, name, mime in types:
        url = _wcs_link(wcs_url, identifier, mime, bbox=bbox, srid=srid)
        output.append((ext, name, mime, url))
    return output


def _wfs_get_capabilities():
    try:
        wfs_url = urljoin(settings.SITEURL, reverse('wfs_endpoint'))
    except BaseException:
        wfs_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wfs_url += '&' if '?' in wfs_url else '?'

    return wfs_url + urllib.urlencode({
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
    return wfs_url + urllib.urlencode(params)


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
        wms_url = urljoin(settings.SITEURL, reverse('wms_endpoint'))
    except BaseException:
        wms_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
    wms_url += '&' if '?' in wms_url else '?'

    return wms_url + urllib.urlencode({
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.1.1',
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

    return wms_url + urllib.urlencode(wms_params)


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
