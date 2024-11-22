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
from mock import MagicMock, patch
from geonode.upload.api.exceptions import ImportException
from django.contrib.auth import get_user_model
from geonode.upload.handlers.common.serializer import RemoteResourceSerializer
from geonode.upload.handlers.remote.tiles3d import RemoteTiles3DResourceHandler
from geonode.upload.handlers.tiles3d.exceptions import Invalid3DTilesException
from geonode.upload.orchestrator import orchestrator
from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest
from geonode.base.models import ResourceBase


class TestRemoteTiles3DFileHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RemoteTiles3DResourceHandler()
        cls.valid_url = (
            "https://raw.githubusercontent.com/CesiumGS/3d-tiles-samples/main/1.1/TilesetWithFullMetadata/tileset.json"
        )
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {
            "url": "http://abc123defsadsa.org",
            "title": "Remote Title",
            "type": "3dtiles",
        }
        cls.valid_files = {
            "url": cls.valid_url,
            "title": "Remote Title",
            "type": "3dtiles",
        }
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="stazioni_metropolitana", owner=cls.owner)

    def test_can_handle_should_return_true_for_remote(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)

    def test_should_get_the_specific_serializer(self):
        actual = self.handler.has_serializer(self.valid_files)
        self.assertEqual(type(actual), type(RemoteResourceSerializer))

    def test_create_error_log(self):
        """
        Should return the formatted way for the log of the handler
        """
        actual = self.handler.create_error_log(
            Exception("my exception"),
            "foo_task_name",
            *["exec_id", "layer_name", "alternate"],
        )
        expected = "Task: foo_task_name raised an error during actions for layer: alternate: my exception"
        self.assertEqual(expected, actual)

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["upload"]), 3)
        self.assertTupleEqual(expected, self.handler.TASKS["upload"])

    def test_task_list_is_the_expected_one_geojson(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["copy"]), 2)
        self.assertTupleEqual(expected, self.handler.TASKS["copy"])

    def test_is_valid_should_raise_exception_if_the_url_is_invalid(self):
        with self.assertRaises(ImportException) as _exc:
            self.handler.is_valid_url(url=self.invalid_files["url"])

        self.assertIsNotNone(_exc)
        self.assertTrue("The provided url is not reachable")

    def test_is_valid_should_pass_with_valid_url(self):
        self.handler.is_valid_url(url=self.valid_files["url"])

    def test_extract_params_from_data(self):
        actual, _data = self.handler.extract_params_from_data(
            _data={"defaults": '{"url": "http://abc123defsadsa.org", "title": "Remote Title", "type": "3dtiles"}'},
            action="upload",
        )
        self.assertTrue("title" in actual)
        self.assertTrue("url" in actual)
        self.assertTrue("type" in actual)

    @patch("geonode.upload.handlers.common.remote.import_orchestrator")
    def test_import_resource_should_work(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()
        try:
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params=self.valid_files,
            )

            # start the resource import
            self.handler.import_resource(files=self.valid_files, execution_id=str(exec_id))
            patch_upload.apply_async.assert_called_once()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    def test_create_geonode_resource_raise_error_if_url_is_not_reachabel(self):
        with self.assertRaises(Invalid3DTilesException):
            exec_id = orchestrator.create_execution_request(
                user=self.owner,
                func_name="funct1",
                step="step",
                input_params={
                    "url": "http://abc123defsadsa.org",
                    "title": "Remote Title",
                    "type": "3dtiles",
                },
            )

            self.handler.create_geonode_resource(
                "layername",
                "layeralternate",
                execution_id=exec_id,
                resource_type=ResourceBase,
                asset=None,
            )

    def test_create_geonode_resource(self):
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params={
                "url": "https://dummyjson.com/users",
                "title": "Remote Title",
                "type": "3dtiles",
            },
        )

        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type=ResourceBase,
            asset=None,
        )
        self.assertIsNotNone(resource)
        self.assertEqual(resource.subtype, "3dtiles")
