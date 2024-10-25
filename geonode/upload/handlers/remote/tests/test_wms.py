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
from collections import namedtuple
from django.test import TestCase
from mock import MagicMock, patch
from geonode.upload.api.exceptions import ImportException
from django.contrib.auth import get_user_model
from geonode.upload.handlers.remote.serializers.wms import RemoteWMSSerializer
from geonode.upload.handlers.remote.wms import RemoteWMSResourceHandler
from geonode.upload.orchestrator import orchestrator
from geonode.resource.models import ExecutionRequest
from geonode.base.models import ResourceBase


class TestRemoteWMSResourceHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RemoteWMSResourceHandler()
        cls.valid_url = "http://geoserver:8080/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_payload = {
            "url": "http://invalid.com",
            "type": "invalid",
            "title": "This will fail",
            "lookup": "abc124",
            "bbox": ["1", "2", "3", "4"],
            "parse_remote_metadata": False,
        }
        cls.valid_payload_with_parse_false = {
            "url": cls.valid_url,
            "type": "wms",
            "title": "This will fail",
            "lookup": "abc124",
            "bbox": ["1", "2", "3", "4"],
            "parse_remote_metadata": False,
        }

        cls.valid_payload_with_parse_true = {
            "url": cls.valid_url,
            "type": "wms",
            "title": "This will fail",
            "lookup": "abc124",
            "bbox": ["1", "2", "3", "4"],
            "parse_remote_metadata": True,
        }
        cls.owner = get_user_model().objects.first()

    def test_can_handle_should_return_true_for_remote(self):
        actual = self.handler.can_handle(self.valid_payload_with_parse_false)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle(self.invalid_payload)
        self.assertFalse(actual)

    def test_should_get_the_specific_serializer(self):
        actual = self.handler.has_serializer(self.valid_payload_with_parse_false)
        self.assertEqual(type(actual), type(RemoteWMSSerializer))

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
            self.handler.is_valid_url(url=self.invalid_payload["url"])

        self.assertIsNotNone(_exc)
        self.assertTrue("The provided url is not reachable")

    def test_is_valid_should_pass_with_valid_url(self):
        self.handler.is_valid_url(url=self.valid_payload_with_parse_false["url"])

    def test_extract_params_from_data(self):
        actual, _data = self.handler.extract_params_from_data(
            _data={"defaults": f"{self.valid_payload_with_parse_true}"},
            action="upload",
        )
        self.assertTrue("title" in actual)
        self.assertTrue("url" in actual)
        self.assertTrue("type" in actual)
        self.assertTrue("lookup" in actual)
        self.assertTrue("parse_remote_metadata" in actual)
        self.assertTrue("bbox" in actual)

    @patch("geonode.upload.handlers.remote.wms.WmsServiceHandler")
    def test_prepare_import_should_not_update_the_execid(self, remote_wms):
        """
        prepare_import should update the execid
        if the parse_remote_metadata is False
        """
        fake_url = MagicMock(shema="http", netloc="fake", path="foo", query="bar")
        remote_wms.get_cleaned_url_params.return_value = fake_url, None, None, None

        try:
            exec_id = None
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params=self.valid_payload_with_parse_false,
            )

            self.handler.prepare_import(files=[], execution_id=str(exec_id))
            # Title and bbox should not be updated
            # since the wms is not called
            _exec_obj = orchestrator.get_execution_object(str(exec_id))
            expected_title = "This will fail"
            expected_bbox = ["1", "2", "3", "4"]
            self.assertEqual(expected_bbox, _exec_obj.input_params["bbox"])
            self.assertEqual(expected_title, _exec_obj.input_params["title"])
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    @patch("geonode.upload.handlers.remote.wms.WmsServiceHandler")
    @patch("geonode.upload.handlers.remote.wms.RemoteWMSResourceHandler.get_wms_resource")
    def test_prepare_import_should_update_the_execid(self, get_wms_resource, remote_wms):
        """
        prepare_import should update the execid
        if the parse_remote_metadata is True
        """
        # remote_wms = MagicMock(title="updated_title", bbox=[1,2,3,4])
        fake_url = MagicMock(shema="http", netloc="fake", path="foo", query="bar")
        remote_wms.get_cleaned_url_params.return_value = fake_url, None, None, None

        obj = namedtuple("WmsObj", field_names=["title", "boundingBoxWGS84"])
        get_wms_resource.return_value = obj(title="Updated title", boundingBoxWGS84=[9, 109, 5, 1563])

        try:
            exec_id = None
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params=self.valid_payload_with_parse_true,
            )

            self.handler.prepare_import(files=[], execution_id=str(exec_id))
            # Title and bbox should be updated
            # since the wms is called
            _exec_obj = orchestrator.get_execution_object(str(exec_id))
            expected_title = "Updated title"
            expected_bbox = [9, 109, 5, 1563]
            self.assertEqual(expected_bbox, _exec_obj.input_params["bbox"])
            self.assertEqual(expected_title, _exec_obj.input_params["title"])
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    @patch("geonode.upload.handlers.common.remote.import_orchestrator")
    def test_import_resource_should_work(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()
        try:
            exec_id = None
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params=self.valid_payload_with_parse_false,
            )

            self.handler.import_resource(files=self.valid_payload_with_parse_false, execution_id=str(exec_id))
            patch_upload.apply_async.assert_called_once()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    def test_generate_resource_payload(self):
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload_with_parse_false,
        )
        self.handler.prepare_import(files=[], execution_id=str(exec_id))
        exec_obj = orchestrator.get_execution_object(str(exec_id))
        resource = self.handler.generate_resource_payload(
            "layername",
            "layeralternate",
            _exec=exec_obj,
            workspace="geonode",
            asset=None,
        )
        self.assertIsNotNone(resource)
        self.assertEqual(resource["subtype"], "remote")

    def test_create_geonode_resource(self):
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload_with_parse_false,
        )
        self.handler.prepare_import(files=[], execution_id=str(exec_id))
        resource = self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type=ResourceBase,
            asset=None,
        )
        self.assertIsNotNone(resource)
        self.assertEqual(resource.subtype, "remote")
        self.assertTrue(ResourceBase.objects.filter(alternate="layeralternate").exists())
