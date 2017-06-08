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
        base_name, _ = os.path.splitext(base_path)
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
    def cache_path(self):
        """Returned the location of tile cache for this layer.

        :return: Base path of layer cache
        :rtype: str
        """
        basename, _ = os.path.splitext(self.base_layer_path)
        basename = os.path.basename(basename)
        path = os.path.join(QGIS_TILES_DIRECTORY, basename)
        return path

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


from geonode.qgis_server import signals  # noqa: F402,F401
