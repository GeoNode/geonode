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
import StringIO
import zipfile
import gisdata

from django.core.management import call_command
from django.test import TestCase
from django.core.urlresolvers import reverse

from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload
from geonode import qgis_server


class ViewsTest(TestCase):

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

    def test_default_context(self):
        """Test default context provided by qgis_server."""

        response = self.client.get('/')

        context = response.context

        # Necessary context to ensure compatibility with views
        # Some view needs these context to do some javascript logic.
        self.assertIn('UPLOADER_URL', context)
        self.assertIn('MAPFISH_PRINT_ENABLED', context)
        self.assertIn('PRINT_NG_ENABLED', context)
        self.assertIn('GEONODE_SECURITY_ENABLED', context)
        self.assertIn('GEOGIG_ENABLED', context)
        self.assertIn('TIME_ENABLED', context)
        self.assertIn('MOSAIC_ENABLED', context)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_ogc_specific_layer(self):
        """Test we can use QGIS Server API for a layer.

        For now, we are just checking we can call these views without any
        exceptions. We should improve this test by checking the result.
        """
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)

        params = {'layername': uploaded.name}

        # Zip
        response = self.client.get(
            reverse('qgis-server-download-zip', kwargs=params))
        self.assertEqual(response.status_code, 200)
        try:
            f = StringIO.StringIO(response.content)
            zipped_file = zipfile.ZipFile(f, 'r')

            for one_file in zipped_file.namelist():
                if one_file.endswith('.qgs'):
                    # We shoudn't get any QGIS project
                    assert False
            self.assertIsNone(zipped_file.testzip())
        finally:
            zipped_file.close()
            f.close()

        # Legend
        response = self.client.get(
            reverse('qgis-server-legend', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        # Tile
        coordinates = {'z': '0', 'x': '1', 'y': '0'}
        coordinates.update(params)
        response = self.client.get(
            reverse('qgis-server-tile', kwargs=coordinates))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        # Tile 404
        response = self.client.get(
            reverse('qgis-server-tile', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'), 'text/html; charset=utf-8')

        # Geotiff
        response = self.client.get(
            reverse('qgis-server-geotiff', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/tiff')
