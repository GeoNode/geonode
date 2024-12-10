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
from geonode.upload.handlers.geotiff.exceptions import InvalidGeoTiffException
from django.contrib.auth import get_user_model
from geonode.upload import project_dir
from geonode.upload.models import UploadParallelismLimit
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.base.populate_test_data import create_single_dataset

from geonode.upload.handlers.geotiff.handler import GeoTiffFileHandler


class TestGeoTiffFileHandler(TestCase):
    databases = ("default",)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = GeoTiffFileHandler()
        cls.valid_tiff = f"{project_dir}/tests/fixture/test_raster.tif"
        cls.valid_files = {"base_file": cls.valid_tiff, "action": "upload"}
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_tiff = {"base_file": "invalid.file.foo"}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="test_grid", owner=cls.owner)

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["upload"]), 4)
        self.assertTupleEqual(expected, self.handler.TASKS["upload"])

    def test_task_list_is_the_expected_one_copy(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_raster_file",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["copy"]), 4)
        self.assertTupleEqual(expected, self.handler.TASKS["copy"])

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=0)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_tiff, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_pass_with_valid_tif(self):
        self.handler.is_valid(files=self.valid_files, user=self.user)

    def test_is_valid_should_raise_exception_if_the_tif_is_invalid(self):
        data = {"base_file": "/using/double/dot/in/the/name/is/an/error/file.invalid.tif"}
        with self.assertRaises(InvalidGeoTiffException) as _exc:
            self.handler.is_valid(files=data, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Please remove the additional dots in the filename" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_tif_is_invalid_format(self):
        with self.assertRaises(InvalidGeoTiffException) as _exc:
            self.handler.is_valid(files=self.invalid_tiff, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Please remove the additional dots in the filename" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_tif_not_provided(self):
        with self.assertRaises(InvalidGeoTiffException) as _exc:
            self.handler.is_valid(files={"foo": "bar"}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("base file is not provided" in str(_exc.exception.detail))

    def test_can_handle_should_return_true_for_tif(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.gpkg"})
        self.assertFalse(actual)
