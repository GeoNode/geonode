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
import json
import os
import urlparse
import zipfile
from imghdr import what

import requests
from lxml import etree

import gisdata
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase, TestCase

from geonode import qgis_server
from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload
from geonode.maps.models import Map
from geonode.qgis_server.helpers import wms_get_capabilities_url, style_list


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

        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        vector_layer = file_upload(filename)

        params = {'layername': uploaded.name}

        # Zip
        response = self.client.get(
            reverse('qgis_server:download-zip', kwargs=params))
        self.assertEqual(response.status_code, 200)
        try:
            f = StringIO.StringIO(response.content)
            zipped_file = zipfile.ZipFile(f, 'r')

            for one_file in zipped_file.namelist():
                # We shoudn't get any QGIS project
                self.assertFalse(one_file.endswith('.qgs'))
            self.assertIsNone(zipped_file.testzip())
        finally:
            zipped_file.close()
            f.close()

        # Legend
        response = self.client.get(
            reverse('qgis_server:legend', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

        # Tile
        coordinates = {'z': '11', 'x': '1576', 'y': '1054'}
        coordinates.update(params)
        response = self.client.get(
            reverse('qgis_server:tile', kwargs=coordinates))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

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
        self.assertEqual(what('', h=response.content), 'tiff')

        response = self.client.get(
            reverse('qgis_server:geotiff', kwargs={
                'layername': vector_layer.name
            }))
        self.assertEqual(response.status_code, 404)

        # QML Styles
        # Request list of styles
        response = self.client.get(
            reverse('qgis_server:download-qml', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/json')
        # Should return a default style list
        actual_result = json.loads(response.content)
        actual_result = [s['name'] for s in actual_result]
        expected_result = ['default']
        self.assertEqual(set(expected_result), set(actual_result))

        # Get single styles
        response = self.client.get(
            reverse('qgis_server:download-qml', kwargs={
                'layername': params['layername'],
                'style_name': 'default'
            }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # Set thumbnail from viewed bbox
        response = self.client.get(
            reverse('qgis_server:set-thumbnail', kwargs=params))
        self.assertEqual(response.status_code, 400)
        data = {
            'bbox': '-5.54025,96.9406,-5.2820,97.1250'
        }
        response = self.client.post(
            reverse('qgis_server:set-thumbnail', kwargs=params),
            data=data)
        # User dont have permission
        self.assertEqual(response.status_code, 401)
        # Should log in
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse('qgis_server:set-thumbnail', kwargs=params),
            data=data)
        self.assertEqual(response.status_code, 200)
        retval = json.loads(response.content)
        expected_retval = {
            'success': True
        }
        self.assertEqual(retval, expected_retval)

        # OGC Server specific for THE layer
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphics',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
        }
        response = self.client.get(
            reverse('qgis_server:layer-request', kwargs=params), query_string)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

        # OGC Server for the Geonode instance
        # GetLegendGraphics is a shortcut when using the main OGC server.
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphics',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
        }
        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

        # WMS GetCapabilities
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetCapabilities'
        }

        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.content, 'GetCapabilities is not supported yet.')

        query_string['LAYERS'] = uploaded.name

        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        get_capabilities_content = response.content

        # Check xml content
        self.assertEqual(response.status_code, 200, response.content)
        root = etree.fromstring(response.content)
        layer_xml = root.xpath(
            'wms:Capability/wms:Layer/wms:Layer/wms:Name',
            namespaces={'wms': 'http://www.opengis.net/wms'})
        self.assertEqual(len(layer_xml), 1)
        self.assertEqual(layer_xml[0].text, uploaded.name)
        # GetLegendGraphic request returned must be valid
        layer_xml = root.xpath(
            'wms:Capability/wms:Layer/'
            'wms:Layer/wms:Style/wms:LegendURL/wms:OnlineResource',
            namespaces={
                'xlink': 'http://www.w3.org/1999/xlink',
                'wms': 'http://www.opengis.net/wms'
            })
        legend_url = layer_xml[0].attrib[
            '{http://www.w3.org/1999/xlink}href']

        response = self.client.get(legend_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=response.content), 'png')

        # Check get capabilities using helper returns the same thing
        response = requests.get(wms_get_capabilities_url(
            uploaded, internal=False))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_capabilities_content, response.content)

        # WMS GetMap
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'FORMAT': 'image/png',
            'LAYERS': uploaded.name,
            'HEIGHT': 250,
            'WIDTH': 250,
            'SRS': 'EPSG:4326',
            'BBOX': '-5.54025,96.9406,-5.2820,97.1250',
        }
        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.get('Content-Type'), 'image/png', response.content)
        self.assertEqual(what('', h=response.content), 'png')

        # End of the test, we should remove every files related to the test.
        uploaded.delete()
        vector_layer.delete()


class QGISServerStyleManagerTest(LiveServerTestCase):

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_list_style(self):
        """Test querying list of styles from QGIS Server."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        layer = file_upload(filename)
        """:type: geonode.layers.models.Layer"""

        actual_list_style = style_list(layer, internal=False)
        expected_list_style = ['default']

        # There will be a default style
        self.assertEqual(
            set(expected_list_style),
            set([style.name for style in actual_list_style])
        )


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
        self.assertTrue(remote_thumbnail_link.url)

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
        self.assertEqual(what(thumbnail_path), 'png')

        # Check that now we have thumbnail
        self.assertTrue(layer.has_thumbnail())

        missing_thumbnail_url = staticfiles.static(settings.MISSING_THUMBNAIL)

        self.assertTrue(layer.get_thumbnail_url() != missing_thumbnail_url)

        thumbnail_links = layer.link_set.filter(name__icontains='thumbnail')
        self.assertTrue(len(thumbnail_links) > 0)

        link_names = ['remote thumbnail', 'thumbnail']
        for link in thumbnail_links:
            self.assertIn(link.name.lower(), link_names)

        # cleanup
        layer.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_map_thumbnail(self):
        """Creating map will create thumbnail."""
        filename = os.path.join(
            gisdata.GOOD_DATA, 'raster/relief_san_andres.tif')
        layer1 = file_upload(filename)

        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        layer2 = file_upload(filename)
        """:type: geonode.layers.models.Layer"""

        # construct json request for new map
        json_payload = {
            "sources": {
                "source_OpenMapSurfer Roads": {
                    "url": "http://korona.geog.uni-heidelberg.de/tiles"
                           "/roads/x={x}&y={y}&z={z}"
                },
                "source_OpenStreetMap": {
                    "url": "http://{s}.tile.osm.org/{z}/{x}/{y}.png"
                },
                "source_san_andres_y_providencia_administrative": {
                    "url": "http://geonode.dev/qgis-server/tiles"
                           "/san_andres_y_providencia_administrative/"
                           "{z}/{x}/{y}.png"
                },
                "source_relief_san_andres": {
                    "url": "http://geonode.dev/qgis-server/tiles"
                           "/relief_san_andres/{z}/{x}/{y}.png"
                }
            },
            "about": {
                "title": "San Andreas",
                "abstract": "San Andreas sample map"
            },
            "map": {
                "center": [12.91890657418042, -81.298828125],
                "zoom": 6,
                "projection": "",
                "layers": [
                    {
                        "name": "OpenMapSurfer_Roads",
                        "title": "OpenMapSurfer Roads",
                        "visibility": True,
                        "url": "http://korona.geog.uni-heidelberg.de/tiles/"
                               "roads/x={x}&y={y}&z={z}",
                        "group": "background",
                        "source": "source_OpenMapSurfer Roads"
                    },
                    {
                        "name": "osm",
                        "title": "OpenStreetMap",
                        "visibility": False,
                        "url": "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
                        "group": "background",
                        "source": "source_OpenStreetMap"
                    },
                    {
                        "name": "geonode:"
                                "san_andres_y_providencia_administrative",
                        "title": "san_andres_y_providencia_administrative",
                        "visibility": True,
                        "url": "http://geonode.dev/qgis-server/tiles"
                               "/san_andres_y_providencia_administrative/"
                               "{z}/{x}/{y}.png",
                        "source": "source_"
                                  "san_andres_y_providencia_administrative"
                    },
                    {
                        "name": "geonode:relief_san_andres",
                        "title": "relief_san_andres",
                        "visibility": True,
                        "url": "http://geonode.dev/qgis-server/tiles"
                               "/relief_san_andres/{z}/{x}/{y}.png",
                        "source": "source_relief_san_andres"
                    }
                ]
            }
        }

        self.client.login(username='admin', password='admin')

        response = self.client.post(
            reverse('new_map_json'),
            json.dumps(json_payload),
            content_type='application/json')

        self.assertEqual(response.status_code, 200)

        map_id = json.loads(response.content).get('id')

        map = Map.objects.get(id=map_id)

        # check that we have remote thumbnail
        remote_thumbnail_link = map.link_set.get(
            name__icontains='remote thumbnail')
        self.assertTrue(remote_thumbnail_link.url)

        # thumbnail won't generate because remote thumbnail uses public
        # address

        remote_thumbnail_url = remote_thumbnail_link.url

        # Replace url's basename, we want to access it using django client
        parse_result = urlparse.urlsplit(remote_thumbnail_url)
        remote_thumbnail_url = urlparse.urlunsplit(
            ('', '', parse_result.path, parse_result.query, ''))

        response = self.client.get(remote_thumbnail_url)

        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbs')
        thumbnail_path = os.path.join(thumbnail_dir, 'map-thumb.png')

        map.save_thumbnail(thumbnail_path, response.content)

        # Check thumbnail created
        self.assertTrue(os.path.exists(thumbnail_path))
        self.assertEqual(what(thumbnail_path), 'png')

        # Check that now we have thumbnail
        self.assertTrue(map.has_thumbnail())

        missing_thumbnail_url = staticfiles.static(settings.MISSING_THUMBNAIL)

        self.assertTrue(map.get_thumbnail_url() != missing_thumbnail_url)

        thumbnail_links = map.link_set.filter(name__icontains='thumbnail')
        self.assertTrue(len(thumbnail_links) > 0)

        link_names = ['remote thumbnail', 'thumbnail']
        for link in thumbnail_links:
            self.assertIn(link.name.lower(), link_names)

        # cleanup
        map.delete()
        layer1.delete()
        layer2.delete()
