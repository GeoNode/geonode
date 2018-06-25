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

from geonode.tests.base import GeoNodeBaseTestSupport

import os
import urlparse
import unittest
from imghdr import what

from geonode.qgis_server.models import QGISServerLayer
from lxml import etree

import gisdata
import shutil

import requests
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse

from geonode import qgis_server
from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload
from geonode.qgis_server.helpers import validate_django_settings, \
    transform_layer_bbox, qgis_server_endpoint, tile_url_format, tile_url, \
    style_get_url, style_add_url, style_list, style_set_default_url, \
    style_remove_url


class HelperTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_validate_settings(self):
        """Test settings validation"""
        self.assertTrue(validate_django_settings())

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_transform_layer_bbox(self):
        """Test bbox CRS conversion"""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)

        new_bbox = transform_layer_bbox(uploaded, 3857)

        expected_bbox = [
            10793092.549352637, -615294.6893182159,
            10810202.947307253, -591232.8900397272]

        self.assertEqual(new_bbox, expected_bbox)

        new_bbox = transform_layer_bbox(uploaded, 4326)

        expected_bbox = [
            96.956, -5.5187329999999,
            97.10970532, -5.3035455519999]

        self.assertEqual(new_bbox, expected_bbox)

        uploaded.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_qgis_server_endpoint(self):
        """Test QGIS Server endpoint url."""

        # Internal url should go to http://qgis-server (docker container
        self.assertEqual(
            settings.QGIS_SERVER_URL, qgis_server_endpoint(internal=True))
        # Public url should go to proxy url
        parse_result = urlparse.urlparse(qgis_server_endpoint(internal=False))
        self.assertEqual(parse_result.path, reverse('qgis_server:request'))

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_tile_url(self):
        """Test to return tile format."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)

        tile_format = tile_url_format(uploaded.name)

        # Accessing this directly should return 404
        response = self.client.get(tile_format)
        self.assertEqual(response.status_code, 404)

        qgis_tile_url = tile_url(uploaded, 11, 1576, 1054, internal=True)

        parse_result = urlparse.urlparse(qgis_tile_url)

        base_net_loc = urlparse.urlparse(settings.QGIS_SERVER_URL).netloc

        self.assertEqual(base_net_loc, parse_result.netloc)

        query_string = urlparse.parse_qs(parse_result.query)

        expected_query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': '10801469.341,-606604.256471,10821037.2203,-587036.37723',
            'CRS': 'EPSG:3857',
            'WIDTH': '256',
            'HEIGHT': '256',
            'LAYERS': 'test_grid',
            'STYLE': 'default',
            'FORMAT': 'image/png',
            'TRANSPARENT': 'true',
            'DPI': '96',
            'MAP_RESOLUTION': '96',
            'FORMAT_OPTIONS': 'dpi:96'
        }
        for key, value in expected_query_string.iteritems():
            # urlparse.parse_qs returned a dictionary of list
            actual_value = query_string[key][0]
            self.assertEqual(actual_value, value)

        # Check that qgis server returns valid url
        # Use python requests because the endpoint is not django
        response = requests.get(qgis_tile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

        uploaded.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_style_management_url(self):
        """Test QGIS Server style management url construction."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)

        # Get default style
        # There will always be a default style when uploading a layer
        style_url = style_get_url(uploaded, 'default', internal=True)

        response = requests.get(style_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'text/xml')

        # it has to contains qgis tags
        style_xml = etree.fromstring(response.content)
        self.assertTrue('qgis' in style_xml.tag)

        # Add new style
        # change default style slightly
        self.assertTrue('WhiteToBlack' not in response.content)
        self.assertTrue('BlackToWhite' in response.content)
        new_style_xml = etree.fromstring(
            response.content.replace('BlackToWhite', 'WhiteToBlack'))
        new_xml_content = etree.tostring(new_style_xml, pretty_print=True)

        # save it to qml file, accessible by qgis server
        qgis_layer = QGISServerLayer.objects.get(layer=uploaded)
        with open(qgis_layer.qml_path, mode='w') as f:
            f.write(new_xml_content)

        style_url = style_add_url(uploaded, 'new_style', internal=True)

        response = requests.get(style_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'OK')

        # Get style list
        qml_styles = style_list(uploaded, internal=False)
        if qml_styles:
            expected_style_names = ['default', 'new_style']
            actual_style_names = [s.name for s in qml_styles]
            self.assertEqual(
                set(expected_style_names),
                set(actual_style_names))

        # Get new style
        style_url = style_get_url(uploaded, 'new_style', internal=True)

        response = requests.get(style_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'text/xml')
        self.assertTrue('WhiteToBlack' in response.content)

        # Set default style
        style_url = style_set_default_url(
            uploaded, 'new_style', internal=True)

        response = requests.get(style_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'OK')

        # Remove style
        style_url = style_remove_url(uploaded, 'new_style', internal=True)

        response = requests.get(style_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'OK')

        # Cleanup
        uploaded.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    @unittest.skipIf(
        not os.environ.get('ON_TRAVIS', False),
        'Only run this on Travis')
    def test_delete_orphan(self):
        """Test orphan deletions.

        This test only started in travis to avoid accidentally deleting owners
        data.
        """
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)

        # Clean up first
        call_command('delete_orphaned_qgis_server_layers')

        # make request to generate tile cache
        response = self.client.get(
            reverse('qgis_server:tile', kwargs={
                'z': '11',
                'x': '1576',
                'y': '1054',
                'layername': uploaded.name
            }))
        self.assertEqual(response.status_code, 200)

        # register file list
        layer_path = settings.QGIS_SERVER_CONFIG['layer_directory']
        tiles_path = settings.QGIS_SERVER_CONFIG['tiles_directory']
        geonode_layer_path = os.path.join(settings.MEDIA_ROOT, 'layers')

        qgis_layer_list = set(os.listdir(layer_path))
        tile_cache_list = set(os.listdir(tiles_path))
        geonode_layer_list = set(os.listdir(geonode_layer_path))

        # run management command. should not change anything
        call_command('delete_orphaned_qgis_server_layers')

        actual_qgis_layer_list = set(os.listdir(layer_path))
        actual_tile_cache_list = set(os.listdir(tiles_path))
        actual_geonode_layer_list = set(os.listdir(geonode_layer_path))

        self.assertEqual(qgis_layer_list, actual_qgis_layer_list)
        self.assertEqual(tile_cache_list, actual_tile_cache_list)
        self.assertEqual(geonode_layer_list, actual_geonode_layer_list)

        # now create random file without reference
        shutil.copy(
            os.path.join(layer_path, 'test_grid.tif'),
            os.path.join(layer_path, 'test_grid_copy.tif'))
        shutil.copytree(
            os.path.join(tiles_path, 'test_grid'),
            os.path.join(tiles_path, 'test_grid_copy'))
        shutil.copy(
            os.path.join(geonode_layer_path, 'test_grid.tif'),
            os.path.join(geonode_layer_path, 'test_grid_copy.tif'))

        actual_qgis_layer_list = set(os.listdir(layer_path))
        actual_tile_cache_list = set(os.listdir(tiles_path))
        actual_geonode_layer_list = set(os.listdir(geonode_layer_path))

        # run management command. This should clear the files. But preserve
        # registered files (the one that is saved in database)
        call_command('delete_orphaned_qgis_server_layers')

        self.assertEqual(
            {'test_grid_copy.tif'},
            actual_qgis_layer_list - qgis_layer_list)
        self.assertEqual(
            {'test_grid_copy'},
            actual_tile_cache_list - tile_cache_list)
        self.assertEqual(
            {'test_grid_copy.tif'},
            actual_geonode_layer_list - geonode_layer_list)

        # cleanup
        uploaded.delete()
