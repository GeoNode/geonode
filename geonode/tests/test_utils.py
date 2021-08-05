#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import copy
import shutil
import zipfile
import tempfile

from osgeo import ogr
from unittest.mock import patch
from datetime import datetime, timedelta

from django.db.models import signals
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon
from django.core.management import call_command

from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.maps.models import Layer
from geonode.layers.models import Attribute
from geonode.geoserver.helpers import set_attributes
from geonode.geoserver.signals import geoserver_post_save
from geonode.br.management.commands.utils.utils import ignore_time
from geonode.utils import copy_tree, fixup_shp_columnnames, unzip_file


class TestCopyTree(GeoNodeBaseTestSupport):
    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Erling_Haaland.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_less_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates meet the 'data_dt_filter'
        less-than iso timestamp are backed-up successfully
        """
        copy_tree('/src', '/dst', ignore=ignore_time('<', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Sancho.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_less_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree('/src', '/dst', ignore=ignore_time('<', datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Saala.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_greater_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        greater-than iso timestamp are backed-up successfully
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>', datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch('shutil.copy2')
    @patch('os.path.getmtime', return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch('os.listdir', return_value=['Sadio.jpg'])
    @patch('os.path.isdir', return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_greater_than_filter_criteria(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch('os.path.exists', return_value=True)
    @patch('shutil.copytree')
    @patch('os.path.getmtime', return_value=0)
    @patch('os.listdir', return_value=['an_awesome_directory'])
    @patch('os.path.isdir', return_value=True)
    def test_backup_of_child_directories(
            self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copytree, path_os_exists):
        """
        Test that all directories which meet the 'ignore criteria are backed-up'
        """
        copy_tree('/src', '/dst', ignore=ignore_time('>=', datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copytree.called)


class TestFixupShp(GeoNodeBaseTestSupport):
    def test_fixup_shp_columnnames(self):
        project_root = os.path.abspath(os.path.dirname(__file__))
        layer_zip = os.path.join(project_root, "data", "ming_female_1.zip")

        self.failUnless(zipfile.is_zipfile(layer_zip))

        layer_shp = unzip_file(layer_zip)

        expected_fieldnames = [
            "ID", "_f", "__1", "__2", "m", "_", "_M2", "_M2_1", "l", "x", "y", "_WU", "_1",
        ]
        _, _, fieldnames = fixup_shp_columnnames(layer_shp, "windows-1258")

        inDriver = ogr.GetDriverByName("ESRI Shapefile")
        inDataSource = inDriver.Open(layer_shp, 0)
        inLayer = inDataSource.GetLayer()
        inLayerDefn = inLayer.GetLayerDefn()

        self.assertEqual(inLayerDefn.GetFieldCount(), len(expected_fieldnames))

        for i, fn in enumerate(expected_fieldnames):
            self.assertEqual(inLayerDefn.GetFieldDefn(i).GetName(), fn)

        inDataSource.Destroy()

        # Cleanup temp dir
        shp_parent = os.path.dirname(layer_shp)
        if shp_parent.startswith(tempfile.gettempdir()):
            shutil.rmtree(shp_parent, ignore_errors=True)


class TestSetAttributes(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        # Load users to log in as
        call_command('loaddata', 'people_data', verbosity=0)
        self.user = get_user_model().objects.get(username='admin')

    def test_set_attributes_creates_attributes(self):
        """ Test utility function set_attributes() which creates Attribute instances attached
            to a Layer instance.
        """
        # Creating a layer requires being logged in
        self.client.login(username='norman', password='norman')

        # Disconnect the geoserver-specific post_save signal attached to Layer creation.
        # The geoserver signal handler assumes things about the store where the Layer is placed.
        # this is a workaround.
        disconnected_post_save = signals.post_save.disconnect(geoserver_post_save, sender=Layer)

        # Create dummy layer to attach attributes to
        _l = Layer.objects.create(
            owner=self.user,
            name='dummy_layer',
            bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
            srid='EPSG:4326')

        # Reconnect the signal if it was disconnected
        if disconnected_post_save:
            signals.post_save.connect(geoserver_post_save, sender=Layer)

        attribute_map = [
            ['id', 'Integer'],
            ['date', 'IntegerList'],
            ['enddate', 'Real'],
            ['date_as_date', 'xsd:dateTime'],
        ]

        # attribute_map gets modified as a side-effect of the call to set_attributes()
        expected_results = copy.deepcopy(attribute_map)

        # set attributes for resource
        set_attributes(_l, attribute_map.copy())

        # 2 items in attribute_map should translate into 2 Attribute instances
        self.assertEqual(_l.attributes.count(), len(expected_results))

        # The name and type should be set as provided by attribute map
        for a in _l.attributes:
            self.assertIn([a.attribute, a.attribute_type], expected_results)

        # GeoNode cleans up local duplicated attributes
        for attribute in attribute_map:
            field = attribute[0]
            ftype = attribute[1]
            if field:
                la = Attribute.objects.create(layer=_l, attribute=field)
                la.visible = ftype.find("gml:") != 0
                la.attribute_type = ftype
                la.description = None
                la.attribute_label = None
                la.display_order = 0

        # set attributes for resource
        set_attributes(_l, attribute_map.copy())

        # 2 items in attribute_map should translate into 2 Attribute instances
        self.assertEqual(_l.attributes.count(), len(expected_results))

        # The name and type should be set as provided by attribute map
        for a in _l.attributes:
            self.assertIn([a.attribute, a.attribute_type], expected_results)

        # Test that deleted attributes from GeoServer gets deleted on GeoNode too
        attribute_map = [
            ['id', 'Integer'],
            ['date_as_date', 'xsd:dateTime'],
        ]

        # attribute_map gets modified as a side-effect of the call to set_attributes()
        expected_results = copy.deepcopy(attribute_map)

        # set attributes for resource
        set_attributes(_l, attribute_map.copy())

        # 2 items in attribute_map should translate into 2 Attribute instances
        self.assertEqual(_l.attributes.count(), len(expected_results))

        # The name and type should be set as provided by attribute map
        for a in _l.attributes:
            self.assertIn([a.attribute, a.attribute_type], expected_results)
