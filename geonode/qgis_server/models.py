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

import os
import logging
from shutil import rmtree

from django.db import models
from django.conf import settings

from geonode.layers.models import Layer

logger = logging.getLogger("geonode.qgis_server.models")

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

    def delete_qgis_layer(self):
        """Delete all files related to this object from disk."""
        try:
            base_path = self.base_layer_path
            base_name, _ = os.path.splitext(base_path)
            for ext in QGISServerLayer.accepted_format:
                file_path = base_name + '.' + ext
                if os.path.exists(file_path):
                    os.remove(file_path)

            # QGIS can create a .aux.xml too
            file_path = self.base_layer_path + '.aux.xml'
            if os.path.exists(file_path):
                os.remove(file_path)

        except QGISServerLayer.DoesNotExist:
            logger.debug('QGIS Server Layer not found. Not deleting.')
            pass

        # Removing the cache.
        basename, _ = os.path.splitext(self.base_layer_path)
        basename = os.path.basename(basename)
        path = os.path.join(QGIS_TILES_DIRECTORY, basename)
        logger.info('Removing the cache from a qgis layer : %s' % path)
        try:
            rmtree(path)
        except OSError:
            pass


from geonode.qgis_server import signals  # noqa: F402.F401
