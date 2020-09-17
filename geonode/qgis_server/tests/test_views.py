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

import io
import json
import os
from urllib.parse import urlsplit, urlunsplit
import zipfile
from imghdr import what

import requests
from defusedxml import lxml as dlxml

import gisdata
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.files.storage import default_storage as storage
from django.urls import reverse

from geonode import qgis_server
from geonode.compat import ensure_string
from geonode.base.thumb_utils import thumb_path
from geonode.decorators import on_ogc_backend
from geonode.layers.utils import file_upload
from geonode.maps.models import Map
from geonode.qgis_server.helpers import wms_get_capabilities_url, style_list


class DefaultViewsTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
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
        self.assertIn('TIME_ENABLED', context)
        self.assertIn('MOSAIC_ENABLED', context)


class QGISServerViewsTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

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
            f = io.StringIO(ensure_string(response.content))
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
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

        # Tile
        coordinates = {'z': '11', 'x': '1576', 'y': '1054'}
        coordinates.update(params)
        response = self.client.get(
            reverse('qgis_server:tile', kwargs=coordinates))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'image/png')
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

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
        self.assertEqual(what('', h=ensure_string(response.content)), 'tiff')

        # Layer is already on the database
        # checking the Link
        links = uploaded.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_RASTER)

        # checks signals.py for the hardcoded names in QLR and QGS
        qlr_link = links.get(name='QGIS layer file (.qlr)')
        self.assertIn("download-qlr", qlr_link.url)
        qgs_link = links.get(name='QGIS project file (.qgs)')
        self.assertIn("download-qgs", qgs_link.url)

        # QLR
        response = self.client.get(
            reverse('qgis_server:download-qlr', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'),
            'application/x-qgis-layer-definition')
        # check file name's extension
        file_name = response.get('Content-Disposition').split('filename=')
        file_ext = file_name[1].split('.')
        self.assertEqual(file_ext[1], "qlr")

        # QGS
        response = self.client.get(
            reverse('qgis_server:download-qgs', kwargs=params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'),
            'application/x-qgis-project')
        # check file name's extension
        file_name = response.get('Content-Disposition').split('filename=')
        file_ext = file_name[1].split('.')
        self.assertEqual(file_ext[1], "qgs")

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
        content = ensure_string(response.content)
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        actual_result = json.loads(content)
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
        self.assertEqual(response.status_code, 403)
        # Should log in
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse('qgis_server:set-thumbnail', kwargs=params),
            data=data)
        self.assertEqual(response.status_code, 200)
        content = ensure_string(response.content)
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        retval = json.loads(content)
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
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

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
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

        # WMS GetCapabilities
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetCapabilities'
        }

        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        self.assertEqual(response.status_code, 200, ensure_string(response.content))
        self.assertEqual(
            ensure_string(response.content), 'GetCapabilities is not supported yet.')

        query_string['LAYERS'] = uploaded.name

        response = self.client.get(
            reverse('qgis_server:request'), query_string)
        get_capabilities_content = ensure_string(response.content)

        # Check xml content
        self.assertEqual(response.status_code, 200, ensure_string(response.content))
        root = dlxml.fromstring(ensure_string(response.content))
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
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

        # Check get capabilities using helper returns the same thing
        response = requests.get(wms_get_capabilities_url(
            uploaded, internal=False))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_capabilities_content, ensure_string(response.content))

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
        self.assertEqual(response.status_code, 200, ensure_string(response.content))
        self.assertEqual(
            response.get('Content-Type'), 'image/png', ensure_string(response.content))
        self.assertEqual(what('', h=ensure_string(response.content)), 'png')

        # End of the test, we should remove every files related to the test.
        uploaded.delete()
        vector_layer.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_download_map_qlr(self):
        """Test download QLR file for a map"""
        # 2 layers to be added to the map
        filename = os.path.join(
            gisdata.GOOD_DATA, 'raster/relief_san_andres.tif')
        layer1 = file_upload(filename)

        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        layer2 = file_upload(filename)

        # construct json request for new map
        json_payload = InitialSetup.generate_initial_map(layer1, layer2)

        self.client.login(username='admin', password='admin')

        response = self.client.post(
            reverse('new_map_json'),
            data=json.dumps(json_payload),
            content_type='application/json')
        # map is successfully saved
        self.assertEqual(response.status_code, 200)
        content = ensure_string(response.content)
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = json.loads(content).get('id')

        map = Map.objects.get(id=map_id)

        # check that QLR is added to the links
        links = map.link_set.download()
        map_qlr_link = links.get(name='Download QLR Layer file')
        self.assertIn('qlr', map_qlr_link.url)

        # QLR
        response = self.client.get(
            reverse('map_download_qlr', kwargs={'mapid': map_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type'),
            'application/x-qgis-layer-definition')

        # cleanup
        map.delete()
        layer1.delete()
        layer2.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_map_json(self):
        # 2 layers to be added to the map
        filename = os.path.join(
            gisdata.GOOD_DATA, 'raster/relief_san_andres.tif')
        layer1 = file_upload(filename)

        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        layer2 = file_upload(filename)

        json_payload = InitialSetup.generate_initial_map(layer1, layer2)
        # First, create a map with two layers
        # Need to log in for saving a map
        self.client.login(username='admin', password='admin')

        result_new_map = self.client.post(
            reverse('new_map_json'),
            json.dumps(json_payload),
            content_type='application/json')
        # the new map is successfully saved
        self.assertEqual(result_new_map.status_code, 200)

        map_id = json.loads(result_new_map.content).get('id')
        # try to remove one layer
        layers = json_payload['map']['layers']
        before_remove = len(layers)
        after_remove = before_remove - 1
        layer = layers[0]
        layers.remove(layer)

        # check if the layer is eliminated from the map
        result_update_map = self.client.post(
            reverse('map_json', kwargs={'mapid': map_id}),
            data=json.dumps(json_payload),
            content_type='application/json')
        # successfully updated
        self.assertEqual(result_update_map.status_code, 200)
        # the number of layers on the map decrease by 1
        self.assertEqual(
            len(result_update_map.context_data['map'].layers),
            after_remove)

        # clean up
        map = Map.objects.get(id=map_id)
        map.delete()
        layer1.delete()
        layer2.delete()


class QGISServerStyleManagerTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    def data_path(self, path):
        project_root = os.path.abspath(settings.PROJECT_ROOT)
        return os.path.join(
            project_root, 'qgis_server/tests/data', path)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_list_style(self):
        """Test querying list of styles from QGIS Server."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        layer = file_upload(filename)
        """:type: geonode.layers.models.Layer"""

        actual_list_style = style_list(layer, internal=False)
        expected_list_style = ['default']

        # There will be a default style
        if actual_list_style:
            self.assertEqual(
                set(expected_list_style),
                set([style.name for style in actual_list_style]))

            style_list_url = reverse(
                'qgis_server:download-qml',
                kwargs={
                    'layername': layer.name
                })
            response = self.client.get(style_list_url)
            self.assertEqual(response.status_code, 200)
            content = ensure_string(response.content)
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            actual_list_style = json.loads(content)

            # There will be a default style
            self.assertEqual(
                set(expected_list_style),
                set([style['name'] for style in actual_list_style]))

        layer.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_add_delete_style(self):
        """Test add new style using qgis_server views."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        layer = file_upload(filename)
        """:type: geonode.layers.models.Layer"""

        self.client.login(username='admin', password='admin')

        qml_path = self.data_path('test_grid.qml')
        add_style_url = reverse(
            'qgis_server:upload-qml',
            kwargs={
                'layername': layer.name})

        with open(qml_path) as file_handle:
            form_data = {
                'name': 'new_style',
                'title': 'New Style',
                'qml': file_handle
            }
            response = self.client.post(
                add_style_url,
                data=form_data)

        self.assertEqual(response.status_code, 201)

        actual_list_style = style_list(layer, internal=False)
        if actual_list_style:
            expected_list_style = ['default', 'new_style']
            self.assertEqual(
                set(expected_list_style),
                set([style.name for style in actual_list_style]))

        # Test delete request
        delete_style_url = reverse(
            'qgis_server:remove-qml',
            kwargs={
                'layername': layer.name,
                'style_name': 'default'})

        response = self.client.delete(delete_style_url)
        self.assertEqual(response.status_code, 200)

        actual_list_style = style_list(layer, internal=False)
        if actual_list_style:
            expected_list_style = ['new_style']
            self.assertEqual(
                set(expected_list_style),
                set([style.name for style in actual_list_style]))

        # Check new default
        default_style_url = reverse(
            'qgis_server:default-qml',
            kwargs={
                'layername': layer.name})

        response = self.client.get(default_style_url)

        self.assertEqual(response.status_code, 200)
        expected_default_style_retval = {
            'name': 'new_style',
        }
        content = ensure_string(response.content)
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        actual_default_style_retval = json.loads(content)

        for key, value in expected_default_style_retval.items():
            self.assertEqual(actual_default_style_retval[key], value)

        layer.delete()


class ThumbnailGenerationTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

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
        parse_result = urlsplit(remote_thumbnail_url)
        remote_thumbnail_url = urlunsplit(
            ('', '', parse_result.path, parse_result.query, ''))

        response = self.client.get(remote_thumbnail_url)

        thumbnail_path = thumb_path("layer-thumb.png")

        layer.save_thumbnail(thumbnail_path, ensure_string(response.content))

        # Check thumbnail created
        self.assertTrue(storage.exists(thumbnail_path))
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
        json_payload = InitialSetup.generate_initial_map(layer1, layer2)

        self.client.login(username='admin', password='admin')

        response = self.client.post(
            reverse('new_map_json'),
            json.dumps(json_payload),
            content_type='application/json')

        self.assertEqual(response.status_code, 200)
        content = ensure_string(response.content)
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = json.loads(content).get('id')

        map = Map.objects.get(id=map_id)

        # check that we have remote thumbnail
        remote_thumbnail_link = map.link_set.filter(
            name__icontains='remote thumbnail').first()
        self.assertTrue(remote_thumbnail_link.url)

        # thumbnail won't generate because remote thumbnail uses public
        # address

        remote_thumbnail_url = remote_thumbnail_link.url

        # Replace url's basename, we want to access it using django client
        parse_result = urlsplit(remote_thumbnail_url)
        remote_thumbnail_url = urlunsplit(
            ('', '', parse_result.path, parse_result.query, ''))

        response = self.client.get(remote_thumbnail_url)

        thumbnail_path = thumb_path("map-thumb.png")

        map.save_thumbnail(thumbnail_path, ensure_string(response.content))

        # Check thumbnail created
        self.assertTrue(storage.exists(thumbnail_path))
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


class InitialSetup():

    @classmethod
    def generate_initial_map(cls, layer1, layer2):
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
                        "name": layer2.alternate,
                        "title": layer2.name,
                        "visibility": True,
                        "url": "http://geonode.dev/qgis-server/tiles"
                               "/san_andres_y_providencia_administrative/"
                               "{z}/{x}/{y}.png",
                        "source": "source_"
                                  "san_andres_y_providencia_administrative"
                    },
                    {
                        "name": layer1.alternate,
                        "title": layer1.name,
                        "visibility": True,
                        "url": "http://geonode.dev/qgis-server/tiles"
                               "/relief_san_andres/{z}/{x}/{y}.png",
                        "source": "source_relief_san_andres"
                    }
                ]
            }
        }

        return json_payload
