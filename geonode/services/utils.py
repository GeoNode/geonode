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
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


def flip_coordinates(c1, c2):
    if c1 > c2:
        logger.debug(f"Flipping coordinates {c1}, {c2}")
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
    return f"POLYGON(({minx:.2f} {miny:.2f}, {minx:.2f} {maxy:.2f}, {maxx:.2f} {maxy:.2f}, {maxx:.2f} {miny:.2f}, {minx:.2f} {miny:.2f}))"


def inverse_mercator(xy):
    """
    Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / 20037508.34) * 180
    lat = (xy[1] / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
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
    result = re.search("rest/services/(.*)/(?:MapServer|ImageServer)", url)
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
        if "fullExtent" in esriobj._json_struct:
            extent = esriobj._json_struct["fullExtent"]
    except Exception as err:
        logger.debug(err, exc_info=True)

    try:
        if "extent" in esriobj._json_struct:
            extent = esriobj._json_struct["extent"]
    except Exception as err:
        logger.debug(err, exc_info=True)

    try:
        srs = extent["spatialReference"]["wkid"]
    except Exception as err:
        logger.debug(err, exc_info=True)

    return [extent, srs]


def decimal_encode(bbox):
    _bbox = []
    _srid = None
    for o in bbox:
        try:
            o = float(o)
        except Exception:
            o = None if "EPSG" not in o else o
        if o and isinstance(o, float):
            _bbox.append(f"{round(o, 2):.15f}")
        elif o and "EPSG" in o:
            _srid = o
    _bbox = _bbox if not _srid else _bbox + [_srid]
    return _bbox


def test_resource_table_status(test_cls, table, is_row_filtered):
    tbody = table.find_elements_by_tag_name("tbody")
    rows = tbody[0].find_elements_by_tag_name("tr")
    visible_rows_count = 0
    filter_row_count = 0
    hidden_row_count = 0
    for row in rows:
        attr_name = row.get_attribute("name")
        val = row.value_of_css_property("display")

        if attr_name == "filter_row":
            filter_row_count = filter_row_count + 1
        if val == "none":
            hidden_row_count = hidden_row_count + 1
        else:
            visible_rows_count = visible_rows_count + 1
    result = {
        "filter_row_count": filter_row_count,
        "visible_rows_count": visible_rows_count,
        "hidden_row_count": hidden_row_count,
    }

    if is_row_filtered:
        test_cls.assertTrue(result["filter_row_count"] > 0)
        test_cls.assertEqual(result["visible_rows_count"], result["filter_row_count"])
        test_cls.assertEqual(result["hidden_row_count"], 20)
    else:
        test_cls.assertEqual(result["filter_row_count"], 0)
        test_cls.assertEqual(result["visible_rows_count"], 20)
        test_cls.assertEqual(result["hidden_row_count"], 0)


def parse_services_types():
    from django.utils.module_loading import import_string

    services_type_modules = (
        django_settings.SERVICES_TYPE_MODULES if hasattr(django_settings, "SERVICES_TYPE_MODULES") else []
    )
    custom_services_types = {}
    for services_type_path in services_type_modules:
        custom_services_type_module = import_string(services_type_path)
        custom_services_types = {**custom_services_types, **custom_services_type_module.services_type}
    return custom_services_types
