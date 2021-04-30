# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
import traceback
from urllib.parse import urlencode
from urllib.request import urlretrieve
from os.path import splitext
from math import atan, degrees, sinh, pi
from defusedxml import lxml as dlxml

from django.conf import settings as geonode_config

from geonode.layers.models import Attribute
from geonode.qgis_server.models import QGISServerLayer

logger = logging.getLogger(__name__)


def set_attributes(layer, overwrite=False):
    """Retrieve layer attribute names & types from QGIS Server using
    the WFS/WMS/WCS, then store in GeoNode database using Attribute model.

    This function is copied/adapted from set_attributes in geoserver/helper.py.

    :param layer: The layer where we want to add/update the attributes.
    :type layer: QGISServerLayer

    :param overwrite: If we should overwrite or not in the database.
    :type overwrite: bool
    """
    if layer.storeType in ['dataStore']:
        layer_name = layer.alternate
        qgis_layer = QGISServerLayer.objects.get(layer=layer)

        qgis_server = geonode_config.QGIS_SERVER_CONFIG['qgis_server_url']
        basename, _ = splitext(qgis_layer.base_layer_path)
        dft_url = f"{qgis_server}?{urlencode({'MAP': f'{basename}.qgs', 'SERVICE': 'WFS', 'VERSION': '1.0.0', 'REQUEST': 'DescribeFeatureType', 'LAYER': layer_name})}"

        # noinspection PyBroadException
        try:
            temp_file = urlretrieve(dft_url)[0]
            with open(temp_file, 'r') as wfs_file:
                doc = dlxml.fromstring(wfs_file.read())

            path = './/{xsd}extension/{xsd}sequence/{xsd}element'.format(
                xsd='{http://www.w3.org/2001/XMLSchema}')

            attribute_map = [
                [n.attrib['name'], n.attrib['type']] for n in doc.findall(
                    path) if n.attrib.get('name') and n.attrib.get('type')]

        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
            attribute_map = []
    else:
        attribute_map = []

    # We need 3 more items for description, attribute_label and display_order
    attribute_map_dict = {
        'field': 0,
        'ftype': 1,
        'description': 2,
        'label': 3,
        'display_order': 4,
    }
    for attribute in attribute_map:
        attribute.extend((None, None, 0))

    attributes = layer.attribute_set.all()

    # Delete existing attributes if they no longer exist in an updated layer.
    for la in attributes:
        lafound = False
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field == la.attribute:
                lafound = True
                # store description and attribute_label in attribute_map
                attribute[attribute_map_dict['description']] = la.description
                attribute[attribute_map_dict['label']] = la.attribute_label
                attribute[attribute_map_dict['display_order']] = la.display_order

        if overwrite or not lafound:
            logger.debug(
                'Going to delete [%s] for [%s]',
                la.attribute,
                layer.name)
            la.delete()

    # Add new layer attributes if they don't already exist.
    if attribute_map is not None:
        iter = len(Attribute.objects.filter(layer=layer)) + 1
        for attribute in attribute_map:
            field, ftype, description, label, display_order = attribute
            if field is not None:
                _gs_attrs = Attribute.objects.filter(
                    layer=layer, attribute=field, attribute_type=ftype,
                    description=description, attribute_label=label,
                    display_order=display_order)
                if _gs_attrs.count() > 1:
                    _gs_attrs.delete()
                la, created = Attribute.objects.get_or_create(
                    layer=layer, attribute=field, attribute_type=ftype,
                    description=description, attribute_label=label,
                    display_order=display_order)
                if created:
                    la.visible = ftype.find('gml:') != 0
                    la.display_order = iter
                    la.save()
                    iter += 1
                    logger.debug(
                        'Created [%s] attribute for [%s]',
                        field,
                        layer.name)
    else:
        logger.debug('No attributes found')


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
