# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2019 OSGeo
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
from geonode.tests.base import GeoNodeBaseTestSupport

import os
import gisdata

from geonode import geoserver
from geonode.decorators import on_ogc_backend

from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geonode.layers.populate_layers_data import create_layer_data

import logging
logger = logging.getLogger(__name__)


class HelperTest(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super(HelperTest, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_replace_layer(self):
        """
        Ensures the layer_style_manage route returns a 200.
        """
        layer = Layer.objects.all()[0]
        logger.debug(Layer.objects.all())
        self.assertIsNotNone(layer)

        logger.info("Attempting to replace a vector layer with a raster.")
        filename = filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        vector_layer = file_upload(filename)
        self.assertTrue(vector_layer.is_vector())
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        with self.\
        assertRaisesRegexp(Exception, "You are attempting to replace a vector layer with a raster."):
            file_upload(filename, layer=vector_layer, overwrite=True)

        logger.info("Attempting to replace a raster layer with a vector.")
        raster_layer = file_upload(filename)
        self.assertFalse(raster_layer.is_vector())
        filename = filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        with self.\
        assertRaisesRegexp(Exception, "You are attempting to replace a raster layer with a vector."):
            file_upload(filename, layer=raster_layer, overwrite=True)

        logger.info("Attempting to replace a layer with no geometry type.")
        with self.\
        assertRaisesRegexp(Exception, "Local GeoNode layer has no geometry type."):
            replaced = file_upload(filename, layer=vector_layer, overwrite=True)

        logger.info("Attempting to replace a vector layer.")
        replaced = file_upload(filename, layer=vector_layer, overwrite=True, gtype='LineString')
        self.assertIsNotNone(replaced)
        self.assertTrue(replaced.is_vector())
