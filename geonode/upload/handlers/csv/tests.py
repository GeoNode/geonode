import uuid
from unittest.mock import MagicMock, patch
import os
from django.contrib.auth import get_user_model
from django.test import TestCase
from geonode.base.populate_test_data import create_single_dataset
from geonode.upload.api.exception import UploadParallelismLimitException
from geonode.upload.models import UploadParallelismLimit
from geonode.upload import project_dir
from geonode.upload.handlers.common.vector import import_with_ogr2ogr
from geonode.upload.handlers.csv.exceptions import InvalidCSVException
from geonode.upload.handlers.csv.handler import CSVFileHandler
from osgeo import ogr


class TestCSVHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = CSVFileHandler()
        cls.valid_csv = f"{project_dir}/tests/fixture/valid.csv"
        cls.invalid_csv = f"{project_dir}/tests/fixture/invalid.csv"
        cls.missing_lat = f"{project_dir}/tests/fixture/missing_lat.csv"
        cls.missing_long = f"{project_dir}/tests/fixture/missing_long.csv"
        cls.missing_geom = f"{project_dir}/tests/fixture/missing_geom.csv"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_csv}
        cls.valid_files = {"base_file": cls.valid_csv}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="test", owner=cls.owner)

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

    def test_is_valid_should_raise_exception_if_the_csv_is_invalid(self):
        with self.assertRaises(InvalidCSVException) as _exc:
            self.handler.is_valid(files=self.invalid_files, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("The CSV provided is invalid, no layers found" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_csv_missing_geom(self):
        with self.assertRaises(InvalidCSVException) as _exc:
            self.handler.is_valid(files={"base_file": self.missing_geom}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Not enough geometry field are set" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_csv_missing_lat(self):
        with self.assertRaises(InvalidCSVException) as _exc:
            self.handler.is_valid(files={"base_file": self.missing_lat}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Latitude is missing" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_csv_missing_long(self):
        with self.assertRaises(InvalidCSVException) as _exc:
            self.handler.is_valid(files={"base_file": self.missing_long}, user=self.user)

        self.assertIsNotNone(_exc)
        self.assertTrue("Longitude is missing" in str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
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
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=1)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_pass_with_valid_csv(self):
        self.handler.is_valid(files=self.valid_files, user=self.user)

    def test_get_ogr2ogr_driver_should_return_the_expected_driver(self):
        expected = ogr.GetDriverByName("CSV")
        actual = self.handler.get_ogr2ogr_driver()
        self.assertEqual(type(expected), type(actual))

    def test_can_handle_should_return_true_for_geopackage(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)

    @patch("importer.handlers.common.vector.Popen")
    def test_import_with_ogr2ogr_without_errors_should_call_the_right_command(self, _open):
        _uuid = uuid.uuid4()

        comm = MagicMock()
        comm.communicate.return_value = b"", b""
        _open.return_value = comm

        _task, alternate, execution_id = import_with_ogr2ogr(
            execution_id=str(_uuid),
            files=self.valid_files,
            original_name="dataset",
            handler_module_path=str(self.handler),
            ovverwrite_layer=False,
            alternate="alternate",
        )

        self.assertEqual("ogr2ogr", _task)
        self.assertEqual(alternate, "alternate")
        self.assertEqual(str(_uuid), execution_id)

        _open.assert_called_once()
        _open.assert_called_with(
            "/usr/bin/ogr2ogr --config PG_USE_COPY YES -f PostgreSQL PG:\" dbname='test_geonode_data' host="
            + os.getenv("DATABASE_HOST", "localhost")
            + " port=5432 user='geonode_data' password='geonode_data' \" \""
            + self.valid_csv
            + '" -nln alternate "dataset" -oo KEEP_GEOM_COLUMNS=NO -lco GEOMETRY_NAME=geometry  -oo "GEOM_POSSIBLE_NAMES=geom*,the_geom*,wkt_geom" -oo "X_POSSIBLE_NAMES=x,long*" -oo "Y_POSSIBLE_NAMES=y,lat*"',  # noqa
            stdout=-1,
            stderr=-1,
            shell=True,  # noqa
        )
