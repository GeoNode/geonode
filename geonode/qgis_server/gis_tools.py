# -*- coding: utf-8 -*-

from math import atan, degrees, sinh, pi


def num2deg(x_tile, y_tile, zoom):
    """Conversion of X,Y and zoom from a TMS url to lat/lon coordinates
    See http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    :param x_tile: The X tile number.
    :type x_tile: integer

    :param y_tile: The Y tile number.
    :type y_tile: integer

    :param zoom: The zoom level, usually between 0 and 20.
    :type zoom: integer

    :return: Tuple (lat,lon).
    :rtype: list
    """
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * y_tile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg
