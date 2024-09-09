import os
from django.test import TestCase
from mock import patch
from geonode.upload import project_dir
from geonode.upload.publisher import DataPublisher
from unittest.mock import MagicMock


class TestDataPublisher(TestCase):
    """
    Test to get the information and publish the resource in geoserver
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.publisher = DataPublisher(handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        cls.gpkg_path = f"{project_dir}/tests/fixture/valid.gpkg"

    def setUp(self):
        layer = self.publisher.cat.get_resources("stazioni_metropolitana", workspaces="geonode")
        print("delete layer")
        if layer:
            res = self.publisher.cat.delete(layer.resource, purge="all", recurse=True)
            print(res.status_code)
            print(res.json)

    def tearDown(self):
        layer = self.publisher.cat.get_resources("stazioni_metropolitana", workspaces="geonode")
        print("delete layer teardown")
        if layer:
            self.publisher.cat.delete(layer)

            res = self.publisher.cat.delete(layer.resource, purge="all", recurse=True)
            print(res.status_code)
            print(res.json)

    def test_extract_resource_name_and_crs(self):
        """
        Given a layer and the original file, should extract the crs and the name
        to let it publish in Geoserver
        """
        values_found = self.publisher.extract_resource_to_publish(
            files={"base_file": self.gpkg_path},
            action="import",
            layer_name="stazioni_metropolitana",
        )
        expected = {"crs": "EPSG:32632", "name": "stazioni_metropolitana"}
        self.assertDictEqual(expected, values_found[0])

    def test_extract_resource_name_and_crs_return_empty_if_the_file_does_not_exists(
        self,
    ):
        """
        Given a layer and the original file, should extract the crs and the name
        to let it publish in Geoserver
        """
        values_found = self.publisher.extract_resource_to_publish(
            files={"base_file": "/wrong/path/file.gpkg"},
            action="import",
            layer_name="stazioni_metropolitana",
        )
        self.assertListEqual([], values_found)

    @patch("geonode.upload.publisher.create_geoserver_db_featurestore")
    def test_get_or_create_store_creation_should_called(self, datastore):
        with patch.dict(os.environ, {"GEONODE_GEODATABASE": "not_existsing_db"}, clear=True):
            self.publisher.get_or_create_store()
            datastore.assert_called_once()

    @patch("geonode.upload.publisher.Catalog.publish_featuretype")
    def test_publish_resources_should_raise_exception_if_any_error_happen(self, publish_featuretype):
        publish_featuretype.side_effect = Exception("Exception")

        with self.assertRaises(Exception):
            self.publisher.publish_resources(resources=[{"crs": "EPSG:32632", "name": "stazioni_metropolitana"}])
        publish_featuretype.assert_called_once()

    @patch("geonode.upload.publisher.Catalog.publish_featuretype")
    def test_publish_resources_should_work(self, publish_featuretype):
        publish_featuretype.return_value = True
        self.publisher.sanity_checks = MagicMock()
        result = self.publisher.publish_resources(resources=[{"crs": "EPSG:32632", "name": "stazioni_metropolitana"}])

        self.assertTrue(result)
        publish_featuretype.assert_called_once()
