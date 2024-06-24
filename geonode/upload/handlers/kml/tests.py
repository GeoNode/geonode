from django.test import TestCase
from django.contrib.auth import get_user_model
from geonode.upload.handlers.kml.exceptions import InvalidKmlException
from geonode.upload.handlers.kml.handler import KMLFileHandler
from importer import project_dir
from geonode.upload.models import UploadParallelismLimit
from geonode.upload.api.exception import UploadParallelismLimitException
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
        cls.valid_files = {"base_file": cls.valid_kml}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="extruded_polygon", owner=cls.owner)

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "importer.import_resource",
            "importer.publish_resource",
            "importer.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.ACTIONS["import"]), 4)
        self.assertTupleEqual(expected, self.handler.ACTIONS["import"])

    def test_task_list_is_the_expected_one_geojson(self):
        expected = (
            "start_copy",
            "importer.copy_dynamic_model",
            "importer.copy_geonode_data_table",
            "importer.publish_resource",
            "importer.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.ACTIONS["copy"]), 5)
        self.assertTupleEqual(expected, self.handler.ACTIONS["copy"])

    def test_is_valid_should_raise_exception_if_the_kml_is_invalid(self):
        with self.assertRaises(InvalidKmlException) as _exc:
            self.handler.is_valid(files=self.invalid_files, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("The kml provided is invalid" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, _ = UploadParallelismLimit.objects.get_or_create(
            slug="default_max_parallel_uploads"
        )
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(
                slug="default_max_parallel_uploads"
            ).update(max_number=0)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_raise_exception_if_layer_are_greater_than_max_parallel_upload(
        self,
    ):
        parallelism, _ = UploadParallelismLimit.objects.get_or_create(
            slug="default_max_parallel_uploads"
        )
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(
                slug="default_max_parallel_uploads"
            ).update(max_number=1)

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

    def test_can_handle_should_return_true_for_geopackage(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)
