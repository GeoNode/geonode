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
from urllib.parse import ParseResult
from django.test import TestCase
from mock import MagicMock, patch
from geonode.upload.api.exceptions import ImportException
from django.contrib.auth import get_user_model
from geonode.upload.handlers.remote.serializers.wms import RemoteWMSSerializer
from geonode.upload.handlers.remote.wms import RemoteWMSResourceHandler
from geonode.upload.orchestrator import orchestrator
from geonode.resource.models import ExecutionRequest
from geonode.base.models import ResourceBase
from geonode.harvesting.models import Harvester
from geonode.security.auth_handlers import BasicAuthHandler
from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.services import enumerations
from geonode.services.models import Service


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
            "identifier": "abc124",
            "bbox": ["1", "2", "3", "4"],
            "parse_remote_metadata": False,
        }
        cls.valid_payload_with_parse_false = {
            "url": cls.valid_url,
            "type": "wms",
            "title": "This will fail",
            "identifier": "abc124",
            "bbox": ["1", "2", "3", "4"],
            "parse_remote_metadata": False,
        }

        cls.valid_payload_with_parse_true = {
            "url": cls.valid_url,
            "type": "wms",
            "title": "This will fail",
            "identifier": "abc124",
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
        self.assertTrue("identifier" in actual)
        self.assertTrue("parse_remote_metadata" in actual)
        self.assertTrue("bbox" in actual)

    def test_extract_params_from_data_should_create_basic_auth_config(self):
        payload = self.valid_payload_with_parse_true.copy()
        payload.update(
            {
                "authentication": {
                    "type": BasicAuthHandler.handled_type,
                    "payload": {"username": "test_user", "password": "test_password"},
                }
            }
        )

        actual, _data = self.handler.extract_params_from_data(_data=payload, action="upload")

        auth_config = AuthConfig.objects.get(pk=actual["auth_config_id"])
        self.assertEqual(BasicAuthHandler.handled_type, auth_config.type)
        self.assertEqual({"username": "test_user", "password": "test_password"}, auth_config.payload)

    def test_create_geonode_resource_rollback_should_delete_created_auth_config(self):
        auth_config = BasicAuthHandler.create_auth_config({"username": "test_user", "password": "test_password"})
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={"auth_config_id": auth_config.pk},
        )

        self.handler._create_geonode_resource_rollback(exec_id, istance_name="missing-resource")

        self.assertFalse(AuthConfig.objects.filter(pk=auth_config.pk).exists())

    def test_create_geonode_resource_rollback_should_not_delete_attached_auth_config(self):
        auth_config = BasicAuthHandler.create_auth_config({"username": "test_user", "password": "test_password"})
        self._create_wms_service(self.valid_url, auth_config=auth_config)
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={"auth_config_id": auth_config.pk},
        )

        self.handler._create_geonode_resource_rollback(exec_id, istance_name="missing-resource")

        self.assertTrue(AuthConfig.objects.filter(pk=auth_config.pk).exists())

    def _create_wms_service(self, service_url, auth_config=None, owner=None):
        owner = owner or self.owner
        harvester = Harvester.objects.create(
            remote_url=service_url,
            name="test-wms-service",
            default_owner=owner,
            harvester_type="geonode.harvesting.harvesters.wms.OgcWmsHarvester",
        )
        return Service.objects.create(
            owner=owner,
            title="test-wms-service",
            type=enumerations.WMS,
            method=enumerations.HARVESTED,
            base_url=service_url,
            name="test-wms-service",
            harvester=harvester,
            auth_config=auth_config,
        )

    @patch("geonode.upload.handlers.remote.wms.WmsServiceHandler")
    def test_prepare_import_should_not_update_the_execid(self, remote_wms):
        """
        prepare_import should update the execid
        if the parse_remote_metadata is False
        """
        fake_url = ParseResult(scheme="http", netloc="fake", path="/foo", params="", query="bar", fragment="")
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
        fake_url = ParseResult(scheme="http", netloc="fake", path="/foo", params="", query="bar", fragment="")
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

    @patch("geonode.upload.handlers.remote.wms.WmsServiceHandler")
    @patch("geonode.upload.handlers.remote.wms.WebMapService")
    def test_prepare_import_should_use_matching_owned_service_auth_config(self, web_map_service, remote_wms):
        service_url = self.valid_url
        fake_url = ParseResult(scheme="http", netloc="fake", path="/foo", params="", query="bar", fragment="")
        remote_wms.get_cleaned_url_params.return_value = fake_url, None, None, None
        auth_config = AuthConfig.objects.create(
            type=BasicAuthHandler.handled_type,
            payload={"username": "service_user", "password": "service_password"},
        )
        self._create_wms_service(service_url, auth_config=auth_config)
        wms_resource = namedtuple("WmsObj", field_names=["title", "boundingBoxWGS84"])(
            title="Updated title",
            boundingBoxWGS84=[9, 109, 5, 1563],
        )
        web_map_service.return_value = (service_url, {self.valid_payload_with_parse_true["identifier"]: wms_resource})
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload_with_parse_true,
        )

        self.handler.pre_processing(files=[], execution_id=str(exec_id))
        self.handler.prepare_import(files=[], execution_id=str(exec_id))

        expected_auth = auth_handler_registry.build(auth_config).get_request_auth()
        web_map_service.assert_called_once_with(self.valid_url, auth=expected_auth)
        _exec_obj = orchestrator.get_execution_object(str(exec_id))
        self.assertEqual(auth_config.pk, _exec_obj.input_params["auth_config_id"])

    @patch("geonode.upload.handlers.remote.wms.WmsServiceHandler")
    @patch("geonode.upload.handlers.remote.wms.WebMapService")
    def test_prepare_import_should_not_use_service_auth_config_from_another_owner(self, web_map_service, remote_wms):
        service_url = self.valid_url
        fake_url = ParseResult(scheme="http", netloc="fake", path="/foo", params="", query="bar", fragment="")
        remote_wms.get_cleaned_url_params.return_value = fake_url, None, None, None
        auth_config = AuthConfig.objects.create(
            type=BasicAuthHandler.handled_type,
            payload={"username": "service_user", "password": "service_password"},
        )
        service_owner = get_user_model().objects.create(username="other-service-owner")
        self._create_wms_service(service_url, auth_config=auth_config, owner=service_owner)
        wms_resource = namedtuple("WmsObj", field_names=["title", "boundingBoxWGS84"])(
            title="Updated title",
            boundingBoxWGS84=[9, 109, 5, 1563],
        )
        web_map_service.return_value = (service_url, {self.valid_payload_with_parse_true["identifier"]: wms_resource})
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload_with_parse_true,
        )

        self.handler.pre_processing(files=[], execution_id=str(exec_id))
        self.handler.prepare_import(files=[], execution_id=str(exec_id))

        web_map_service.assert_called_once_with(self.valid_url, auth=None)
        _exec_obj = orchestrator.get_execution_object(str(exec_id))
        self.assertNotIn("auth_config_id", _exec_obj.input_params)

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

    def test_generate_resource_payload_should_include_auth_config_id(self):
        auth_config = AuthConfig.objects.create(
            type=BasicAuthHandler.handled_type,
            payload={"username": "test_user", "password": "test_password"},
        )
        payload = self.valid_payload_with_parse_false.copy()
        payload["auth_config_id"] = auth_config.pk
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=payload,
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

        self.assertEqual(auth_config.pk, resource["auth_config_id"])

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

    @patch("geonode.upload.handlers.remote.wms.create_harvestable_resource")
    @patch("geonode.upload.handlers.common.remote.BaseRemoteResourceHandler.create_geonode_resource")
    def test_create_geonode_resource_should_connect_harvestable_resource_for_service_owner(
        self, create_resource, create_harvestable
    ):
        service_url = "http://geoserver:8080/geoserver/ows?service=WMS"
        resource = MagicMock()
        create_resource.return_value = resource
        self._create_wms_service(service_url)
        payload = self.valid_payload_with_parse_false.copy()
        payload["ows_url"] = service_url
        payload["bbox"] = None
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=payload,
        )

        self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type=ResourceBase,
            asset=None,
        )

        create_harvestable.assert_called_once_with(resource, service_url=service_url)

    @patch("geonode.upload.handlers.remote.wms.create_harvestable_resource")
    @patch("geonode.upload.handlers.common.remote.BaseRemoteResourceHandler.create_geonode_resource")
    def test_create_geonode_resource_should_not_connect_harvestable_resource_for_another_service_owner(
        self, create_resource, create_harvestable
    ):
        service_url = "http://geoserver:8080/geoserver/ows?service=WMS"
        create_resource.return_value = MagicMock()
        service_owner = get_user_model().objects.create(username="other-service-owner-connect")
        self._create_wms_service(service_url, owner=service_owner)
        payload = self.valid_payload_with_parse_false.copy()
        payload["ows_url"] = service_url
        payload["bbox"] = None
        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=payload,
        )

        self.handler.create_geonode_resource(
            "layername",
            "layeralternate",
            execution_id=exec_id,
            resource_type=ResourceBase,
            asset=None,
        )

        create_harvestable.assert_not_called()
