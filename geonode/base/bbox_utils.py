#########################################################################
#
# Copyright (C) 2020 OSGeo
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

import math
import copy
import json

from decimal import Decimal
from typing import Union, List, Generator
from shapely import affinity
from shapely.ops import split
from shapely.geometry import (
    mapping,
    Polygon,
    LineString,
    GeometryCollection)

from django.contrib.gis.geos import Polygon as DjangoPolygon


class BBOXHelper:
    """
    A bounding box representation to avoid use of list indices when
    dealing with bounding boxes.
    """

    def __init__(self, minmaxform):
        self.xmin, self.ymin, self.xmax, self.ymax = minmaxform

    @classmethod
    def from_xy(cls, xy):
        """
        Constructs a `BBOXHelper` instance from coordinates in "xy" format.

        :param xy: collection of coordinates as [xmin, xmax, ymin, ymax]
        """
        xy[1], xy[2] = xy[2], xy[1]
        return cls(xy)

    def as_polygon(self):
        return DjangoPolygon.from_bbox((self.xmin, self.ymin, self.xmax, self.ymax))


def normalize_x_value(value):
    """
    Normalise x-axis value/longtitude to fall within [-180, 180]
    """
    return ((value + 180) % 360) - 180


def polygon_from_bbox(bbox, srid=4326):
    """
    Constructs a Polygon object with srid from a provided bbox.
    """
    poly = DjangoPolygon.from_bbox(bbox)
    poly.srid = srid
    return poly


def filter_bbox(queryset, bbox):
    """
    Filters a queryset by a provided bounding box.

    :param bbox: Comma-separated coordinates as "xmin,ymin,xmax,ymax"
    """
    assert queryset.model.__class__.__name__ == "PolymorphicModelBase"

    bboxes = []
    _bbox_index = -1
    for _x, _y in enumerate(bbox.split(",")):
        if _x % 4 == 0:
            bboxes.append([])
            _bbox_index += 1
        bboxes[_bbox_index].append(_y)

    search_queryset = None
    for _bbox in bboxes:
        _bbox = list(map(Decimal, _bbox))
        search_polygon = polygon_from_bbox((_bbox[0], _bbox[1], _bbox[2], _bbox[3]))
        for search_polygon_dl in [DjangoPolygon.from_ewkt(_p.wkt) for _p in split_polygon(json.loads(search_polygon.json), output_format="polygons")]:
            _qs = queryset.filter(ll_bbox_polygon__intersects=search_polygon_dl)
            search_queryset = _qs if search_queryset is None else search_queryset | _qs

    return search_queryset


def check_crossing(lon1: float, lon2: float, validate: bool = False, dlon_threshold: float = 180.0):
    """
    ref.: https://towardsdatascience.com/around-the-world-in-80-lines-crossing-the-antimeridian-with-python-and-shapely-c87c9b6e1513
    Assuming a minimum travel distance between two provided longitude coordinates,
    checks if the 180th meridian (antimeridian) is crossed.
    """

    if validate and any([abs(x) > 180.0 for x in [lon1, lon2]]):
        raise ValueError("longitudes must be in degrees [-180.0, 180.0]")
    return abs(lon2 - lon1) > dlon_threshold


def translate_polygons(geometry_collection: GeometryCollection,
                       output_format: str = "geojson") -> Generator[
    Union[List[dict], List[Polygon]], None, None
]:
    """
    ref.: https://towardsdatascience.com/around-the-world-in-80-lines-crossing-the-antimeridian-with-python-and-shapely-c87c9b6e1513
    """
    for polygon in geometry_collection:
        (minx, _, maxx, _) = polygon.bounds
        if minx < -180:
            geo_polygon = affinity.translate(polygon, xoff=360)
        elif maxx > 180:
            geo_polygon = affinity.translate(polygon, xoff=-360)
        else:
            geo_polygon = polygon

        yield_geojson = output_format == "geojson"
        yield json.dumps(mapping(geo_polygon)) if (yield_geojson) else geo_polygon


def split_polygon(geojson: dict, output_format: str = "geojson", validate: bool = False) -> Union[
    List[dict], List[Polygon], GeometryCollection
]:
    """
    ref.: https://towardsdatascience.com/around-the-world-in-80-lines-crossing-the-antimeridian-with-python-and-shapely-c87c9b6e1513
    Given a GeoJSON representation of a Polygon, returns a collection of
    'antimeridian-safe' constituent polygons split at the 180th meridian,
    ensuring compliance with GeoJSON standards (https://tools.ietf.org/html/rfc7946#section-3.1.9)
    Assumptions:
      - Any two consecutive points with over 180 degrees difference in
        longitude are assumed to cross the antimeridian
      - The polygon spans less than 360 degrees in longitude (i.e. does not wrap around the globe)
      - However, the polygon may cross the antimeridian on multiple occasions
    Parameters:
        geojson (dict): GeoJSON of input polygon to be split. For example:
                        {
                        "type": "Polygon",
                        "coordinates": [
                          [
                            [179.0, 0.0], [-179.0, 0.0], [-179.0, 1.0],
                            [179.0, 1.0], [179.0, 0.0]
                          ]
                        ]
                        }
        output_format (str): Available options: "geojson", "polygons", "geometrycollection"
                             If "geometrycollection" returns a Shapely GeometryCollection.
                             Otherwise, returns a list of either GeoJSONs or Shapely Polygons
        validate (bool): Checks if all longitudes are within [-180.0, 180.0]

    Returns:
        List[dict]/List[Polygon]/GeometryCollection: antimeridian-safe polygon(s)
    """
    output_format = output_format.replace("-", "").strip().lower()
    coords_shift = copy.deepcopy(geojson["coordinates"])
    shell_minx = shell_maxx = None
    split_meridians = set()
    splitter = None

    for ring_index, ring in enumerate(coords_shift):
        if len(ring) < 1:
            continue
        else:
            ring_minx = ring_maxx = ring[0][0]
            crossings = 0

        for coord_index, (lon, _) in enumerate(ring[1:], start=1):
            lon_prev = ring[coord_index - 1][0]  # [0] corresponds to longitude coordinate
            if check_crossing(lon, lon_prev, validate=validate):
                direction = math.copysign(1, lon - lon_prev)
                coords_shift[ring_index][coord_index][0] = lon - (direction * 360.0)
                crossings += 1

            x_shift = coords_shift[ring_index][coord_index][0]
            if x_shift < ring_minx:
                ring_minx = x_shift
            if x_shift > ring_maxx:
                ring_maxx = x_shift

        # Ensure that any holes remain contained within the (translated) outer shell
        if (ring_index == 0):  # by GeoJSON definition, first ring is the outer shell
            shell_minx, shell_maxx = (ring_minx, ring_maxx)
        elif (ring_minx < shell_minx):
            ring_shift = [[x + 360, y] for (x, y) in coords_shift[ring_index]]
            coords_shift[ring_index] = ring_shift
            ring_minx, ring_maxx = (x + 360 for x in (ring_minx, ring_maxx))
        elif (ring_maxx > shell_maxx):
            ring_shift = [[x - 360, y] for (x, y) in coords_shift[ring_index]]
            coords_shift[ring_index] = ring_shift
            ring_minx, ring_maxx = (x - 360 for x in (ring_minx, ring_maxx))

        if crossings:  # keep track of meridians to split on
            if ring_minx < -180:
                split_meridians.add(-180)
            if ring_maxx > 180:
                split_meridians.add(180)

    n_splits = len(split_meridians)
    if n_splits > 1:
        raise NotImplementedError(
            """Splitting a Polygon by multiple meridians (MultiLineString)
               not supported by Shapely"""
        )
    elif n_splits == 1:
        split_lon = next(iter(split_meridians))
        meridian = [[split_lon, -90.0], [split_lon, 90.0]]
        splitter = LineString(meridian)

    shell, *holes = coords_shift if splitter else geojson["coordinates"]
    if splitter:
        split_polygons = split(Polygon(shell, holes), splitter)
    else:
        split_polygons = GeometryCollection([Polygon(shell, holes)])

    geo_polygons = list(translate_polygons(split_polygons, output_format))
    if output_format == "geometrycollection":
        return GeometryCollection(geo_polygons)
    else:
        return geo_polygons
