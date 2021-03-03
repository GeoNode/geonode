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

from decimal import Decimal

from django.contrib.gis.geos import Polygon
from django.db.models import Q


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
        return Polygon.from_bbox((self.xmin, self.ymin, self.xmax, self.ymax))


def normalize_x_value(value):
    """
    Normalise x-axis value/longtitude to fall within [-180, 180]
    """
    return ((value + 180) % 360) - 180


def polygon_from_bbox(bbox, srid=4326):
    """
    Constructs a Polygon object with srid from a provided bbox.
    """
    poly = Polygon.from_bbox(bbox)
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

    for _bbox in bboxes:
        _bbox = list(map(Decimal, _bbox))

        # Return all layers when the search extent exceeds 360deg
        if abs(_bbox[0] - _bbox[2]) >= 360:
            return queryset.all()

        x_min = normalize_x_value(_bbox[0])
        x_max = normalize_x_value(_bbox[2])

        # When the search extent crosses the 180th meridian, we'll need to search
        # on two conditions
        if x_min > x_max:
            left_polygon = polygon_from_bbox((-180, _bbox[1], x_max, _bbox[3]))
            right_polygon = polygon_from_bbox((x_min, _bbox[1], 180, _bbox[3]))
            queryset = queryset.filter(
                Q(ll_bbox_polygon__intersects=left_polygon) |
                Q(ll_bbox_polygon__intersects=right_polygon)
            )
        # Otherwise, we do a simple polygon-based search
        else:
            search_polygon = polygon_from_bbox((x_min, _bbox[1], x_max, _bbox[3]))
            queryset = queryset.filter(ll_bbox_polygon__intersects=search_polygon)
    return queryset
