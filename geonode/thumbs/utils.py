from typing import List, Tuple, Callable, Union

from geonode.maps.models import Map
from geonode.layers.models import Layer


def make_bbox_to_pixels_transf(src_bbox: Union[List, Tuple], dest_bbox: Union[List, Tuple]) -> Callable:
    """
    Linear transformation of bbox between CRS and pixel values

    :param src_bbox: image's BBOX in a certain CRS, in (west_bound, south_bound, east_bound, north_bound) order
    :param dest_bbox: image's BBOX in pixels: (0,0,PIL.Image().size[0], PIL.Image().size[1])
    :return: function translating X, Y coordinates in CRS to (x, y) coordinates in pixels
    """

    return lambda x, y: (
        dest_bbox[0] + (x - src_bbox[0]) * (dest_bbox[2] - dest_bbox[0]) / (src_bbox[2] - src_bbox[0]),
        dest_bbox[1] + (src_bbox[3] - y) * (dest_bbox[3] - dest_bbox[1]) / (src_bbox[3] - src_bbox[1]),
    )


def assign_missing_thumbnail(instance: Union[Layer, Map]) -> None:
    """
    Function assigning settings.MISSING_THUMBNAIL to a provided instance

    :param instance: instance of Layer or Map models
    """
    instance.save_thumbnail("", image=None)
