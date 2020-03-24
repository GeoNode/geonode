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
        return cls()

    def as_polygon(self):
        return Polygon.from_bbox((self.xmin, self.ymin, self.xmax, self.ymax))




def normalize_x_value(self, value):
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
    bbox = bbox.split(',')
    bbox = list(map(Decimal, bbox))

    # Return all layers when the search extent exceeds 360deg
    if abs(bbox[0] - bbox[2]) >= 360:
        return queryset.all()
    
    x_min = normalize_x_value(bbox[0])
    x_max = normalize_x_value(bbox[2])

    # When the search extent crosses the 180th meridian, we'll need to search
    # on two conditions
    if x_min > x_max:
        left_polygon = polygon_from_bbox((-180, bbox[1], x_max, bbox[3]))
        right_polygon = polygon_from_bbox((x_min, bbox[1], 180, bbox[3]))
        return queryset.filter(
            Q(bbox_polygon__intersects=left_polygon) |
            Q(bbox_polygon__intersects=right_polygon)
        )

    # Otherwise, we do a simple polygon-based search
    else:
        search_polygon = polygon_from_bbox((x_min, bbox[1], x_max, bbox[3]))
        return queryset.filter(bbox_polygon__intersects=search_polygon)