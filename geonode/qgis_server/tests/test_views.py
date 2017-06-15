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

import StringIO
import os
import urlparse
import zipfile

import gisdata
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase, TestCase

from geonode import qgis_server
from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload


class DefaultViewsTest(TestCase):

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


class QGISServerViewsTest(LiveServerTestCase):

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

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
            reverse('qgis_server:download-zip', kwargs=params))
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
            reverse('qgis_server:legend', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        # Tile
        coordinates = {'z': '0', 'x': '1', 'y': '0'}
        coordinates.update(params)
        response = self.client.get(
            reverse('qgis_server:tile', kwargs=coordinates))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        # Tile 404
        response = self.client.get(
            reverse('qgis_server:tile', kwargs=params))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get('Content-Type'), 'text/html; charset=utf-8')

        # Geotiff
        response = self.client.get(
            reverse('qgis_server:geotiff', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/tiff')

        # OGC Server specific for THE layer
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.3',
            'REQUEST': 'GetLegendGraphics',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
        }
        response = self.client.get(
            reverse('qgis_server:layer-request', kwargs=params), query_string)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        # OGC Server for the Geonode instance
        # GetLegendGraphics is a shortcut when using the main OGC server.
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.3',
            'REQUEST': 'GetLegendGraphics',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
        }
        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')

        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.3',
            'REQUEST': 'GetMap',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
            'HEIGHT': 250,
            'WIDTH': 250,
            'SRS': 'EPSG:4326',
            'BBOX': '-5.2820,96.9406,-5.54025,97.1250',
        }
        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.get('Content-Type'), 'image/png', response.content)

        # End of the test, we should remove every files related to the test.
        uploaded.delete()


class ThumbnailGenerationTest(LiveServerTestCase):

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_thumbnail_links(self):
        """Test that thumbnail links were created after upload."""

        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        layer = file_upload(filename)
        """:type: geonode.layers.models.Layer"""

        # check that we have remote thumbnail
        remote_thumbnail_link = layer.link_set.get(
            name__icontains='remote thumbnail')
        self.assertTrue(
            remote_thumbnail_link.url != settings.MISSING_THUMBNAIL)

        # thumbnail won't generate because remote thumbnail uses public
        # address

        remote_thumbnail_url = remote_thumbnail_link.url

        # Replace url's basename, we want to access it using django client
        parse_result = urlparse.urlsplit(remote_thumbnail_url)
        remote_thumbnail_url = urlparse.urlunsplit(
            ('', '', parse_result.path, parse_result.query, ''))

        response = self.client.get(remote_thumbnail_url)

        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbs')
        thumbnail_path = os.path.join(thumbnail_dir, 'layer-thumb.png')

        layer.save_thumbnail(thumbnail_path, response.content)

        # Check thumbnail created
        self.assertTrue(os.path.exists(thumbnail_path))

        # Check that now we have thumbnail
        self.assertTrue(layer.has_thumbnail())

        missing_thumbnail_url = staticfiles.static(settings.MISSING_THUMBNAIL)

        self.assertTrue(layer.get_thumbnail_url() != missing_thumbnail_url)

        thumbnail_links = layer.link_set.filter(name__icontains='thumbnail')
        self.assertTrue(len(thumbnail_links) > 0)

        link_names = ['remote thumbnail', 'thumbnail']
        for link in thumbnail_links:
            self.assertIn(link.name.lower(), link_names)
