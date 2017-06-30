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
import os
from shutil import rmtree

from django.conf import settings
from django.db import models

from geonode import qgis_server
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.utils import check_ogc_backend

logger = logging.getLogger("geonode.qgis_server.models")

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    QGIS_LAYER_DIRECTORY = settings.QGIS_SERVER_CONFIG['layer_directory']
    QGIS_TILES_DIRECTORY = settings.QGIS_SERVER_CONFIG['tiles_directory']

    if not os.path.exists(QGIS_LAYER_DIRECTORY):
        os.mkdir(QGIS_LAYER_DIRECTORY)


class QGISServerLayer(models.Model):
    """Model for Layer in QGIS Server Backend.
    """

    accepted_format = [
        'tif', 'tiff', 'asc', 'shp', 'shx', 'dbf', 'prj', 'qml', 'xml', 'qgs']

    geotiff_format = ['tif', 'tiff']

    ascii_format = ['asc']

    layer = models.OneToOneField(
        Layer,
        primary_key=True,
        name='layer'
    )
    base_layer_path = models.CharField(
        name='base_layer_path',
        verbose_name='Base Layer Path',
        help_text='Location of the base layer.',
        max_length=100
    )

    @property
    def files(self):
        """Returned all files related with this layer.

        :return: List of related paths
        :rtype: list(str)
        """
        base_path = self.base_layer_path
        base_name, __ = os.path.splitext(base_path)
        extensions_list = QGISServerLayer.accepted_format

        # QGIS can create a .aux.xml too
        extensions_list += '.aux.xml'
        found_files = []
        for ext in extensions_list:
            file_path = '{base}.{ext}'.format(
                base=base_name,
                ext=ext)
            if os.path.exists(file_path):
                found_files.append(file_path)
        return found_files

    @property
    def qgis_layer_path_prefix(self):
        """Returned QGIS layer path prefix.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        Path prefix: /usr/src/app/geonode/qgis_layer/jakarta_flood
        """
        prefix, __ = os.path.splitext(self.base_layer_path)
        return prefix

    @property
    def qgis_layer_name(self):
        """Returned QGIS Layer name associated with this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS Layer name: jakarta_flood
        """
        return os.path.basename(self.qgis_layer_path_prefix)

    @property
    def qgis_project_path(self):
        """Returned QGIS Project path related with this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS Project path: /usr/src/app/geonode/qgis_layer/jakarta_flood.qgs
        """
        return '{prefix}.qgs'.format(prefix=self.qgis_layer_path_prefix)

    @property
    def cache_path(self):
        """Returned the location of tile cache for this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS cache path: /usr/src/app/geonode/qgis_tiles/jakarta_flood

        :return: Base path of layer cache
        :rtype: str
        """
        return os.path.join(QGIS_TILES_DIRECTORY, self.qgis_layer_name)

    @property
    def qml_path(self):
        """Returned the location of QML path for this layer (if any).

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS QML path: /usr/src/app/geonode/qgis_tiles/jakarta_flood.qml

        :return: Base path of qml style
        :rtype: str
        """
        return '{prefix}.qml'.format(prefix=self.qgis_layer_path_prefix)

    def delete_qgis_layer(self):
        """Delete all files related to this object from disk."""
        for file_path in self.files:
            try:
                os.remove(file_path)
            except OSError:
                pass

        # Removing the cache.
        path = self.cache_path
        logger.info('Removing the cache from a qgis layer : %s' % path)
        try:
            rmtree(path)
        except OSError:
            pass


class QGISServerMap(models.Model):
    """Model wrapper for QGIS Server Map."""

    map = models.OneToOneField(
        Map,
        primary_key=True,
        name='map'
    )

    map_name_format = 'map_{id}'

    @property
    def qgis_map_name(self):
        """Returned QGIS Map name associated with this layer.

        based on map_name_format
        Example QGIS Map name: map_1
        """
        return self.map_name_format.format(id=self.map.id)

    @property
    def qgis_map_path_prefix(self):
        """Returned QGIS map path prefix.

        based on map_name_format
        Path prefix: /usr/src/app/geonode/qgis_layer/map_1
        """
        return os.path.join(QGIS_LAYER_DIRECTORY, self.qgis_map_name)

    @property
    def qgis_project_path(self):
        """Returned QGIS Project path related with this map.

        based on map_name_format
        QGIS Project path: /usr/src/app/geonode/qgis_layer/map_1.qgs
        """
        return '{prefix}.qgs'.format(prefix=self.qgis_map_path_prefix)

    @property
    def cache_path(self):
        """Returned the location of tile cache for this layer.

        based on map_name_format
        QGIS cache path: /usr/src/app/geonode/qgis_tiles/map_1

        :return: Base path of layer cache
        :rtype: str
        """
        return os.path.join(QGIS_TILES_DIRECTORY, self.qgis_map_name)


from geonode.qgis_server.signals import \
    register_qgis_server_signals  # noqa: F402,F401
register_qgis_server_signals()
