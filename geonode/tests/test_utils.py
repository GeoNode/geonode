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
from unittest import TestCase
import zipfile
import tempfile
from django.test import override_settings

from osgeo import ogr
from unittest.mock import patch
from datetime import datetime, timedelta

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.auth import get_user_model
from django.core.management import call_command

from geonode.maps.models import Dataset
from geonode.layers.models import Attribute
from geonode.geoserver.helpers import set_attributes
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.br.management.commands.utils.utils import ignore_time
from geonode.utils import copy_tree, fixup_shp_columnnames, get_supported_datasets_file_types, unzip_file, bbox_to_wkt
from geonode import settings


class TestCopyTree(GeoNodeBaseTestSupport):
    @patch("shutil.copy2")
    @patch("os.path.getmtime", return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch("os.listdir", return_value=["Erling_Haaland.jpg"])
    @patch("os.path.isdir", return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_less_than_filter_criteria(
        self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2
    ):
        """
        Test that all root directories whose modification dates meet the 'data_dt_filter'
        less-than iso timestamp are backed-up successfully
        """
        copy_tree("/src", "/dst", ignore=ignore_time("<", datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch("shutil.copy2")
    @patch("os.path.getmtime", return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch("os.listdir", return_value=["Sancho.jpg"])
    @patch("os.path.isdir", return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_less_than_filter_criteria(
        self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2
    ):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree("/src", "/dst", ignore=ignore_time("<", datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch("shutil.copy2")
    @patch("os.path.getmtime", return_value=(datetime.now() - timedelta(days=1)).timestamp())
    @patch("os.listdir", return_value=["Saala.jpg"])
    @patch("os.path.isdir", return_value=False)
    def test_backup_of_root_files_with_modification_dates_meeting_greater_than_filter_criteria(
        self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2
    ):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        greater-than iso timestamp are backed-up successfully
        """
        copy_tree("/src", "/dst", ignore=ignore_time(">", datetime.now().isoformat()))
        self.assertFalse(patch_shutil_copy2.called)

    @patch("shutil.copy2")
    @patch("os.path.getmtime", return_value=(datetime.now() + timedelta(days=1)).timestamp())
    @patch("os.listdir", return_value=["Sadio.jpg"])
    @patch("os.path.isdir", return_value=False)
    def test_skipped_backup_of_root_files_with_modification_dates_not_meeting_greater_than_filter_criteria(
        self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copy2
    ):
        """
        Test that all root directories whose modification dates do not meet the 'data_dt_filter'
        less-than iso timestamp are not backed-up
        """
        copy_tree("/src", "/dst", ignore=ignore_time(">", datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copy2.called)

    @patch("os.path.exists", return_value=True)
    @patch("shutil.copytree")
    @patch("os.path.getmtime", return_value=0)
    @patch("os.listdir", return_value=["an_awesome_directory"])
    @patch("os.path.isdir", return_value=True)
    def test_backup_of_child_directories(
        self, patch_isdir, patch_listdir, patch_getmtime, patch_shutil_copytree, path_os_exists
    ):
        """
        Test that all directories which meet the 'ignore criteria are backed-up'
        """
        copy_tree("/src", "/dst", ignore=ignore_time(">=", datetime.now().isoformat()))
        self.assertTrue(patch_shutil_copytree.called)


class TestFixupShp(GeoNodeBaseTestSupport):
    def test_fixup_shp_columnnames(self):
        project_root = os.path.abspath(os.path.dirname(__file__))
        dataset_zip = os.path.join(project_root, "data", "ming_female_1.zip")

        self.failUnless(zipfile.is_zipfile(dataset_zip))

        dataset_shp = unzip_file(dataset_zip)

        expected_fieldnames = [
            "ID",
            "_f",
            "__1",
            "__2",
            "m",
            "_",
            "_M2",
            "_M2_1",
            "l",
            "x",
            "y",
            "_WU",
            "_1",
        ]
        _, _, fieldnames = fixup_shp_columnnames(dataset_shp, "windows-1258")

        inDriver = ogr.GetDriverByName("ESRI Shapefile")
        inDataSource = inDriver.Open(dataset_shp, 0)
        inLayer = inDataSource.GetLayer()
        inLayerDefn = inLayer.GetLayerDefn()

        self.assertEqual(inLayerDefn.GetFieldCount(), len(expected_fieldnames))

        for i, fn in enumerate(expected_fieldnames):
            self.assertEqual(inLayerDefn.GetFieldDefn(i).GetName(), fn)

        inDataSource.Destroy()

        # Cleanup temp dir
        shp_parent = os.path.dirname(dataset_shp)
        if shp_parent.startswith(tempfile.gettempdir()):
            shutil.rmtree(shp_parent, ignore_errors=True)


class TestSetAttributes(GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()
        # Load users to log in as
        call_command("loaddata", "people_data", verbosity=0)
        self.user = get_user_model().objects.get(username="admin")

    def test_set_attributes_creates_attributes(self):
        """Test utility function set_attributes() which creates Attribute instances attached
        to a Dataset instance.
        """
        # Creating a dataset requires being logged in
        self.client.login(username="norman", password="norman")

        # Create dummy dataset to attach attributes to
        _l = Dataset.objects.create(
            owner=self.user,
            name="dummy_dataset",
            bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
            srid="EPSG:4326",
        )

        attribute_map = [
            ["id", "Integer"],
            ["date", "IntegerList"],
            ["enddate", "Real"],
            ["date_as_date", "xsd:dateTime"],
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
                la = Attribute.objects.create(dataset=_l, attribute=field)
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
            ["id", "Integer"],
            ["date_as_date", "xsd:dateTime"],
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


class TestSupportedTypes(TestCase):
    def setUp(self):
        self.replaced = [
            {
                "id": "shp",
                "label": "Replaced type",
                "format": "vector",
                "ext": ["shp"],
                "requires": ["shp", "prj", "dbf", "shx"],
                "optional": ["xml", "sld"],
            },
        ]

    @override_settings(
        ADDITIONAL_DATASET_FILE_TYPES=[
            {"id": "dummy_type", "label": "Dummy Type", "format": "dummy", "ext": ["dummy"]},
        ]
    )
    def test_should_append_additional_type_if_config_is_provided(self):
        prev_count = len(settings.SUPPORTED_DATASET_FILE_TYPES)
        supported_types = get_supported_datasets_file_types()
        supported_keys = [t.get("id") for t in supported_types]
        self.assertIn("dummy_type", supported_keys)
        self.assertEqual(len(supported_keys), prev_count + 1)

    @override_settings(
        ADDITIONAL_DATASET_FILE_TYPES=[
            {
                "id": "shp",
                "label": "Replaced type",
                "format": "vector",
                "ext": ["shp"],
                "requires": ["shp", "prj", "dbf", "shx"],
                "optional": ["xml", "sld"],
            },
        ]
    )
    def test_should_replace_the_type_id_if_already_exists(self):
        prev_count = len(settings.SUPPORTED_DATASET_FILE_TYPES)
        supported_types = get_supported_datasets_file_types()
        supported_keys = [t.get("id") for t in supported_types]
        self.assertIn("shp", supported_keys)
        self.assertEqual(len(supported_keys), prev_count)
        shp_type = [t for t in supported_types if t["id"] == "shp"][0]
        self.assertEqual(shp_type["label"], "Replaced type")


class TestRegionsCrossingDateLine(TestCase):
    def setUp(self):
        self.test_region_coords = [
            [112.921111999999994, -108.872910000000005, -54.640301000000001, 20.417120000000001],  # Pacific
            [174.866196000000002, -178.203156000000007, -21.017119999999998, -12.466220000000000],  # Fiji
            [158.418335000000013, -150.208359000000002, -11.437030000000000, 4.719560000000000],  # Kiribati
            [165.883803999999998, -175.987198000000006, -52.618591000000002, -29.209969999999998],  # New Zeland
        ]

        self.region_across_idl = [
            112.921111999999994,
            -108.872910000000005,
            -54.640301000000001,
            20.417120000000001,
        ]  # Pacific
        self.region_not_across_idl = [
            -31.266000999999999,
            39.869301000000000,
            27.636310999999999,
            81.008797000000001,
        ]  # Europe

        self.dataset_crossing = GEOSGeometry(
            "POLYGON ((-179.30100799101168718 -17.31310259828852693, -170.41740336774466869 -9.63481116511300328, -164.30155495876181249 -19.7237289784715415, \
            -177.91712988386967709 -30.43762400150689018, -179.30100799101168718 -17.31310259828852693))",
            srid=4326,
        )
        self.dataset_not_crossing = GEOSGeometry(
            "POLYGON ((-41.86461347546176626 5.43160371103088835, 34.20404118809119609 4.3602142087273279, 9.56208263510924894 -48.8521310723496498,  \
            -42.22174330956295307 -32.42415870369499942, -41.86461347546176626 5.43160371103088835))",
            srid=4326,
        )

    def test_region_across_dateline_do_not_intersect_areas_outside(self):
        for i, region_coords in enumerate(self.test_region_coords):
            geographic_bounding_box = bbox_to_wkt(
                region_coords[0], region_coords[1], region_coords[2], region_coords[3]
            )
            _, wkt = geographic_bounding_box.split(";")
            poly = GEOSGeometry(wkt, srid=4326)

            self.assertFalse(
                poly.intersection(self.dataset_crossing).empty, f"True intersection not detected for region {i}"
            )
            self.assertTrue(poly.intersection(self.dataset_not_crossing).empty, "False intersection detected")

    def test_region_wkt_multipolygon_if_across_idl(self):
        bbox_across_idl = bbox_to_wkt(
            self.region_not_across_idl[0],
            self.region_not_across_idl[1],
            self.region_not_across_idl[2],
            self.region_not_across_idl[3],
        )
        _, wkt = bbox_across_idl.split(";")
        poly = GEOSGeometry(wkt, srid=4326)
        self.assertEqual(poly.geom_type, "Polygon", f"Expexted 'Polygon' type but received {poly.geom_type}")

        bbox_across_idl = bbox_to_wkt(
            self.region_across_idl[0], self.region_across_idl[1], self.region_across_idl[2], self.region_across_idl[3]
        )
        _, wkt = bbox_across_idl.split(";")
        poly = GEOSGeometry(wkt, srid=4326)
        self.assertEqual(poly.geom_type, "MultiPolygon", f"Expexted 'MultiPolygon' type but received {poly.geom_type}")
