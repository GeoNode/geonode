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


def crs_parameters(srs):
    """Function to get the correct parameters to include in the QGIS Project.

    :param srs: The Spatial Reference System
    :type srs: django.contrib.gis.gdal.SpatialReference

    :return: Parameters
    :rtype: dict
    """
    parameters = dict()

    unit = srs.units[1]
    if unit in ['metre']:
        unit = 'meters'
    parameters['units'] = unit

    parameters['proj4'] = srs.proj4

    # If 4326, it seems to be 3452, 3857 if it's 3857. We need to check.
    parameters['srsid'] = unicode(srs.srid if srs.srid != 4326 else 3452)

    parameters['srid'] = unicode(srs.srid)

    parameters['authid'] = '%s:%s' % (srs['AUTHORITY'], srs['AUTHORITY', 1])

    parameters['description'] = srs.name.replace('-', ' ')

    # proj : u'+proj=merc +a=6378137 +b=6378137 [...] +no_defs'
    items = srs.proj.split(' ')
    # We want the attribute +proj, merc in this case
    acronym = [i for i in items if i.startswith('+proj')][0].split('=')[1]

    parameters['projection_acronym'] = acronym

    parameters['ellipsoide_acronym'] = srs['GEOGCS'].replace(' ', '')

    parameters['geogcs'] = srs['GEOGCS']

    parameters['geographic'] = unicode(srs.geographic)
    return parameters
