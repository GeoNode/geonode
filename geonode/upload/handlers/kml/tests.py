#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from django.test import TestCase
from django.contrib.auth import get_user_model
from geonode.upload.handlers.kml.exceptions import InvalidKmlException
from geonode.upload.handlers.kml.handler import KMLFileHandler
from geonode.upload import project_dir
from geonode.upload.models import UploadParallelismLimit
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.base.populate_test_data import create_single_dataset
from osgeo import ogr


class TestKMLHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = KMLFileHandler()
        cls.valid_kml = f"{project_dir}/tests/fixture/valid.kml"
        cls.invalid_kml = f"{project_dir}/tests/fixture/inva.lid.kml"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_kml}
        cls.valid_files = {"base_file": cls.valid_kml, "action": "upload"}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="extruded_polygon", owner=cls.owner)

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["upload"]), 4)
        self.assertTupleEqual(expected, self.handler.TASKS["upload"])

    def test_task_list_is_the_expected_one_geojson(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_dynamic_model",
            "geonode.upload.copy_geonode_data_table",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["copy"]), 5)
        self.assertTupleEqual(expected, self.handler.TASKS["copy"])

    def test_is_valid_should_raise_exception_if_the_kml_is_invalid(self):
        with self.assertRaises(InvalidKmlException) as _exc:
            self.handler.is_valid(files=self.invalid_files, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("The kml provided is invalid" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, _ = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=0)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_raise_exception_if_layer_are_greater_than_max_parallel_upload(
        self,
    ):
        parallelism, _ = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=1)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_pass_with_valid_gpkg(self):
        self.handler.is_valid(files=self.valid_files, user=self.user)

    def test_get_ogr2ogr_driver_should_return_the_expected_driver(self):
        expected = ogr.GetDriverByName("KML")
        actual = self.handler.get_ogr2ogr_driver()
        self.assertEqual(type(expected), type(actual))

    def test_can_handle_should_return_true_for_kml(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)
