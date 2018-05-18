#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import re
import math
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def flip_coordinates(c1, c2):
    if c1 > c2:
        logger.debug('Flipping coordinates %s, %s' % (c1, c2))
        temp = c1
        c1 = c2
        c2 = temp
    return c1, c2


def format_float(value):
    if value is None:
        return None
    try:
        value = float(value)
        if value > 999999999:
            return None
        return value
    except ValueError:
        return None


def bbox2wktpolygon(bbox):
    """
    Return OGC WKT Polygon of a simple bbox list of strings
    """

    minx = float(bbox[0])
    miny = float(bbox[1])
    maxx = float(bbox[2])
    maxy = float(bbox[3])
    return 'POLYGON((%.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f))' \
        % (minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)


def inverse_mercator(xy):
    """
    Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / 20037508.34) * 180
    lat = (xy[1] / 20037508.34) * 180
    lat = 180 / math.pi * \
        (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return (lon, lat)


def mercator_to_llbbox(bbox):
    minlonlat = inverse_mercator([bbox[0], bbox[1]])
    maxlonlat = inverse_mercator([bbox[2], bbox[3]])
    return [minlonlat[0], minlonlat[1], maxlonlat[0], maxlonlat[1]]


def get_esri_service_name(url):
    """
    A method to get a service name from an esri endpoint.
    For example: http://example.com/arcgis/rest/services/myservice/mylayer/MapServer/?f=json
    Will return: myservice/mylayer
    """
    result = re.search('rest/services/(.*)/[MapServer|ImageServer]', url)
    if result is None:
        return url
    else:
        return result.group(1)


def get_esri_extent(esriobj):
    """
    Get the extent of an ESRI resource
    """

    extent = None
    srs = None

    try:
        if 'fullExtent' in esriobj._json_struct:
            extent = esriobj._json_struct['fullExtent']
    except Exception, err:
        logger.error(err, exc_info=True)

    try:
        if 'extent' in esriobj._json_struct:
            extent = esriobj._json_struct['extent']
    except Exception, err:
        logger.error(err, exc_info=True)

    try:
        srs = extent['spatialReference']['wkid']
    except Exception, err:
        logger.error(err, exc_info=True)

    return [extent, srs]


def decimal_encode(bbox):
    _bbox = []
    for o in [float(coord) for coord in bbox]:
        if isinstance(o, Decimal):
            o = (str(o) for o in [o])
        _bbox.append("{0:.15f}".format(round(o, 2)))
    return _bbox
