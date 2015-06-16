#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from owslib.wcs import WebCoverageService
from owslib.coverage.wcsBase import ServiceException
import urllib
from geonode import GeoNodeException
from re import sub

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_FORMATS = ['PNG', 'JPEG', 'GIF', 'TIFF']


def wcs_links(
        wcs_url,
        identifier,
        bbox=None,
        crs=None,
        height=None,
        width=None,
        exclude_formats=True,
        quiet=True,
        version='1.0.0'):
    # FIXME(Ariel): This would only work for layers marked for public view,
    # what about the ones with permissions enabled?

    try:
        wcs = WebCoverageService(wcs_url, version=version)
    except ServiceException as err:
        err_msg = 'WCS server returned exception: %s' % err
        if not quiet:
            logger.warn(err_msg)
        raise GeoNodeException(err_msg)

    msg = ('Could not create WCS links for layer "%s",'
           ' it was not in the WCS catalog,'
           ' the available layers were: "%s"' % (
               identifier, wcs.contents.keys()))

    output = []
    formats = []

    if identifier not in wcs.contents:
        if not quiet:
            raise RuntimeError(msg)
        else:
            logger.warn(msg)
    else:
        coverage = wcs.contents[identifier]
        formats = coverage.supportedFormats
        for f in formats:
            if exclude_formats and f in DEFAULT_EXCLUDE_FORMATS:
                continue
            # roundabout, hacky way to accomplish getting a getCoverage url.
            # nonetheless, it's better than having to load an entire large
            # coverage just to generate a URL
            fakeUrl = wcs.getCoverage(identifier=coverage.id, format=f,
                                      bbox=bbox, crs=crs, height=20,
                                      width=20).geturl()
            url = sub(r'(height=)20(\&width=)20', r'\g<1>{0}\g<2>{1}',
                      fakeUrl).format(height, width)
            # The outputs are: (ext, name, mime, url)
            # FIXME(Ariel): Find a way to get proper ext, name and mime
            # using format as a default for all is not good enough
            output.append((f, f, f, url))
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
