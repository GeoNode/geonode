# -*- coding: utf-8 -*-

from math import atan, degrees, sinh, pi, radians, log, cos, tan


def num2deg(xtile, ytile, zoom):
    """ conversion of X,Y + zoom to lat/lon coordinates - from OSM wiki """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return lat_deg, lon_deg


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
    return xtile, ytile