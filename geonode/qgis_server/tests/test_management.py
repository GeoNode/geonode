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
from urllib.parse import unquote
from imghdr import what

import gisdata
from django.core.management import call_command
from geonode import qgis_server
from geonode.qgis_server.models import QGISServerLayer, QGISServerStyle
from geonode.decorators import on_ogc_backend

from geonode.layers.models import Layer


class TestManagementCommands(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_import_layers(self):
        """Importlayers management command should properly overwrite."""
        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        call_command('importlayers', filename, overwrite=True)

        # Check that layer is created
        self.assertEqual(Layer.objects.count(), 1)
        layer = Layer.objects.first()
        self.assertEqual(
            layer.name, 'san_andres_y_providencia_administrative')

        # Check that QGIS Project is created
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
        qgs_path = qgis_layer.qgis_project_path
        self.assertTrue(os.path.exists(qgs_path))
        qgis_project_modified_time = os.path.getmtime(qgs_path)

        # Save all modified time of files
        modified_time = {}
        for f in qgis_layer.files:
            modified_time[f] = os.path.getmtime(f)
        layer_modified_time = {}
        for f in layer.upload_session.layerfile_set.all():
            layer_modified_time[f.file.path] = os.path.getmtime(
                f.file.path)

        # Check that no cache is generated yet
        self.assertFalse(os.path.exists(qgis_layer.cache_path))

        # Check that tiles link is created
        tiles_link = layer.link_set.get(name='Tiles')
        """:type: geonode.base.models.Link"""
        self.assertEqual(tiles_link.extension, 'tiles')
        tiles_url = unquote(tiles_link.url)
        tiles = {
            'z': 7,
            'x': 34,
            'y': 59
        }

        # Try request a tile so a cache is generated
        self.client.login(username='admin', password='admin')
        self.client.get(tiles_url.format(**tiles))

        # Check tiles cache generated
        self.assertTrue(os.path.exists(qgis_layer.cache_path))
        tiles_png = os.path.join(
            qgis_layer.cache_path, 'default', str(tiles['z']), str(tiles['x']),
            f"{str(tiles['y'])}.png")
        self.assertTrue(os.path.exists(tiles_png))
        self.assertEqual(what(tiles_png), 'png')

        # Now, re-import the same file
        call_command('importlayers', filename, overwrite=True)

        # Check that it is still registered as the same layer
        self.assertEqual(Layer.objects.count(), 1)
        layer = Layer.objects.first()
        self.assertEqual(
            layer.name, 'san_andres_y_providencia_administrative')

        # Check that QGIS Project is created and new
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
        qgs_path = qgis_layer.qgis_project_path
        self.assertTrue(os.path.exists(qgs_path))
        self.assertNotEqual(
            qgis_project_modified_time, os.path.getmtime(qgs_path))

        # Compare modified time and it should be different
        for f in qgis_layer.files:
            # for qgis_layer the filename will be the same (overwritten)
            self.assertNotEqual(modified_time[f], os.path.getmtime(f))
        for f in layer.upload_session.layerfile_set.all():
            # for geonode layers, filename might not be the same, so compare
            # extension instead
            filepath = f.file.path
            __, extension = os.path.splitext(filepath)
            old_mtime = [
                v for k, v in layer_modified_time.items()
                if k.endswith(extension)][0]
            self.assertNotEqual(old_mtime, os.path.getmtime(filepath))

        # New geonode layers might not be the same name, but in that case
        # previous files should not exists
        for f in layer.upload_session.layerfile_set.all():
            filepath = f.file.path
            if filepath not in layer_modified_time.keys():
                __, extension = os.path.splitext(filepath)
                old_filepath = [
                    k for k in layer_modified_time.keys()
                    if k.endswith(extension)][0]
                self.assertFalse(os.path.exists(old_filepath))

        # Tile caches should be deleted
        self.assertFalse(os.path.exists(qgis_layer.cache_path))

        # Cleanup
        layer.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_import_qgis_styles(self):
        """import_qgis_styles management commands should run properly."""
        filename = os.path.join(
            gisdata.GOOD_DATA,
            'vector/san_andres_y_providencia_administrative.shp')
        call_command('importlayers', filename, overwrite=True)

        # Check layer have default style after importing
        layer = Layer.objects.get(
            name='san_andres_y_providencia_administrative')

        qgis_layer = layer.qgis_layer
        self.assertTrue(qgis_layer.default_style)

        self.assertTrue(QGISServerStyle.objects.count() == 1)

        # Delete styles
        qgis_layer.default_style.delete()

        self.assertTrue(QGISServerStyle.objects.count() == 0)

        qgis_layer.refresh_from_db()

        self.assertFalse(qgis_layer.default_style)

        # Import styles

        call_command('import_qgis_styles')

        layer.refresh_from_db()
        qgis_layer = layer.qgis_layer
        qgis_layer.refresh_from_db()

        self.assertTrue(qgis_layer.default_style)

        self.assertTrue(QGISServerStyle.objects.count() == 1)

        # Cleanup
        layer.delete()
