#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from unittest.mock import MagicMock, call, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from geoserver.catalog import FailedRequestError

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.resource.models import ExecutionRequest
from geonode.sources.models import DataItem
from geonode.sources.tests.utils import PAYLOAD, create_connection
from geonode.upload.api.exceptions import ImportException
from geonode.upload.celery_tasks import import_orchestrator, import_resource, publish_resource
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.postgres.handler import PostgresUploadHandler
from geonode.upload.orchestrator import orchestrator
from geonode.upload.publisher import DataPublisher
from geonode.upload.utils import ImporterRequestAction as ira


class PostgresUploadHandlerTests(TestCase):
    def test_handler_should_be_registered(self):
        self.assertIn(PostgresUploadHandler, BaseHandler.get_registry())

    def test_upload_should_only_name_and_publish(self):
        """The table is read in place: no copy into the datastore and no GeoNode resource"""
        expected = ("start_import", "geonode.upload.import_resource", "geonode.upload.publish_resource")
        self.assertTupleEqual(expected, PostgresUploadHandler.get_task_list(exa.UPLOAD.value))

    def test_rollback_should_go_through_the_rollback_task(self):
        expected = ("start_rollback", "geonode.upload.rollback")
        self.assertTupleEqual(expected, PostgresUploadHandler.get_task_list(ira.ROLLBACK.value))

    def test_upload_endpoint_should_never_select_it(self):
        """Only geonode.sources starts it, with the connection it has already validated"""
        _data = {"type": "postgresql", "url": "postgresql:?schema=public&table=roads", "action": exa.UPLOAD.value}
        self.assertNotIsInstance(orchestrator.get_handler(_data), PostgresUploadHandler)


class PostgresUploadPublishTests(TestCase):
    def setUp(self):
        self.sut = PostgresUploadHandler()
        self.user = get_user_model().objects.create(username="publisher")
        self.connection = create_connection(sslmode="verify-full", schema="gis")

    def create_execution(self, geometries=None):
        _details = {
            "schema": "public",
            "table": "Roads",
            "geometries": (
                [{"column": "geom", "type": "Line String", "srid": "3857"}] if geometries is None else geometries
            ),
        }
        return ExecutionRequest.objects.create(
            user=self.user,
            func_name="start_import",
            step="start_import",
            action=exa.UPLOAD.value,
            input_params={
                "handler_module_path": str(self.sut),
                "files": {},
                "source_provider": "postgresql",
                "auth_config_id": self.connection.pk,
                "layer_name": "roads_7",
                "uri": "postgresql:?schema=public&table=Roads",
                "title": "public.Roads",
                "details": _details,
            },
        )

    def test_extract_resource_to_publish_should_read_the_table_of_the_execution(self):
        _exec = self.create_execution()
        actual = self.sut.extract_resource_to_publish(
            None, exa.UPLOAD.value, "roads_7", "roads_7", exec_id=_exec.exec_id
        )
        self.assertListEqual([{"name": "roads_7", "crs": "EPSG:3857", "native_name": "Roads"}], actual)
        self.assertEqual(self.connection, self.sut.auth_config)

    def test_store_should_be_created_on_the_connection_of_the_table(self):
        self.sut.auth_config = self.connection
        self.assertTupleEqual((f"postgis_{self.connection.pk}", True), self.sut.get_geoserver_store_name())
        expected = {
            "host": PAYLOAD["host"],
            "port": "5432",
            "database": PAYLOAD["database"],
            "user": PAYLOAD["username"],
            "passwd": PAYLOAD["password"],
            "schema": "gis",
            "SSL mode": "VERIFY_FULL",
            "Session startup SQL": "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY",
            "min connections": 1,
        }
        self.assertDictEqual(expected, self.sut.get_geoserver_store_parameters())

    @patch("geonode.upload.publisher.create_geoserver_db_featurestore")
    @patch("geonode.upload.publisher.Catalog")
    def test_publisher_should_create_the_missing_store_with_the_connection(self, catalog, create_store):
        catalog.return_value.get_store.return_value = None
        _publisher = DataPublisher(str(self.sut))
        _publisher.handler.auth_config = self.connection
        _publisher.get_or_create_store(default="roads_7")
        create_store.assert_called_once_with(
            store_name=f"postgis_{self.connection.pk}",
            workspace=_publisher.workspace.name,
            connection_parameters=_publisher.handler.get_geoserver_store_parameters(),
        )

    def test_extract_resource_to_publish_should_skip_a_table_without_srid(self):
        """publish_resource refuses an empty list: a layer without CRS would be misconfigured in GeoServer"""
        _exec = self.create_execution(geometries=[{"column": "geom", "type": "Unknown", "srid": None}])
        actual = self.sut.extract_resource_to_publish(
            None, exa.UPLOAD.value, "roads_7", "roads_7", exec_id=_exec.exec_id
        )
        self.assertListEqual([], actual)

    def test_publish_resources_should_keep_the_table_name(self):
        _catalog, _store = MagicMock(), MagicMock()
        self.sut.publish_resources(
            [{"name": "roads_7", "crs": "EPSG:3857", "native_name": "Roads"}], _catalog, _store, MagicMock()
        )
        _catalog.publish_featuretype.assert_called_once_with(
            name="roads_7", store=_store, native_crs="EPSG:3857", native_name="Roads"
        )

    def test_publish_resources_should_reuse_the_layer_left_by_a_crashed_run(self):
        """Publishing it again fails with "already exists in store", the layer is the one of the table"""
        _catalog = MagicMock()
        _catalog.publish_featuretype.side_effect = FailedRequestError(
            "Failed to publish feature type roads_7 : 500, Resource named 'roads_7' already exists in store: 'postgis_7'"
        )
        actual = self.sut.publish_resources(
            [{"name": "roads_7", "crs": "EPSG:3857", "native_name": "Roads"}], _catalog, MagicMock(), MagicMock()
        )
        self.assertTrue(actual)
        _catalog.get_resource.assert_not_called()

    def test_publish_resources_should_raise_any_other_geoserver_error(self):
        _catalog = MagicMock()
        _catalog.publish_featuretype.side_effect = FailedRequestError("Failed to publish feature type roads_7 : 500")
        with self.assertRaises(FailedRequestError):
            self.sut.publish_resources(
                [{"name": "roads_7", "crs": "EPSG:3857", "native_name": "Roads"}], _catalog, MagicMock(), MagicMock()
            )

    @patch.object(import_resource, "apply_async")
    def test_start_import_should_go_to_import_resource(self, apply_async):
        _exec = self.create_execution()
        orchestrator.perform_next_step(str(_exec.exec_id), exa.UPLOAD.value, str(self.sut), step="start_import")
        self.assertTupleEqual((str(_exec.exec_id), str(self.sut), exa.UPLOAD.value), apply_async.call_args.args[0])

    @patch.object(publish_resource, "apply_async")
    def test_import_resource_should_go_to_publish_with_the_layer_name(self, apply_async):
        _exec = self.create_execution()
        orchestrator.perform_next_step(
            str(_exec.exec_id),
            exa.UPLOAD.value,
            str(self.sut),
            step="geonode.upload.import_resource",
            layer_name="roads_7",
            alternate="roads_7",
        )
        expected = (
            str(_exec.exec_id),
            "geonode.upload.publish_resource",
            "roads_7",
            "roads_7",
            str(self.sut),
            exa.UPLOAD.value,
        )
        self.assertTupleEqual(expected, apply_async.call_args.args[0])

    @patch.object(import_orchestrator, "apply_async")
    def test_import_resource_should_name_the_layer_after_the_table_and_the_connection(self, apply_async):
        _exec = self.create_execution()
        actual = self.sut.import_resource({}, str(_exec.exec_id))
        _name = f"roads_{self.connection.pk}"
        self.assertTupleEqual((_name, _name, str(_exec.exec_id)), actual)
        _exec.refresh_from_db()
        self.assertEqual(_name, _exec.input_params["layer_name"])
        expected = (
            {},
            str(_exec.exec_id),
            str(self.sut),
            "geonode.upload.import_resource",
            _name,
            _name,
            exa.UPLOAD.value,
        )
        self.assertTupleEqual(expected, apply_async.call_args.args[0])

    def test_is_valid_should_accept_a_table_with_a_crs(self):
        _exec = self.create_execution()
        self.assertTrue(PostgresUploadHandler.is_valid({}, self.user, execution_id=str(_exec.exec_id)))

    def test_is_valid_should_refuse_a_table_without_crs(self):
        _exec = self.create_execution(geometries=[{"column": "geom", "type": "Unknown", "srid": None}])
        with self.assertRaisesRegex(ImportException, "Only tables with a CRS can be published."):
            PostgresUploadHandler.is_valid({}, self.user, execution_id=str(_exec.exec_id))

    def test_is_valid_should_refuse_a_deleted_connection(self):
        _exec = self.create_execution()
        self.connection.delete()
        with self.assertRaisesRegex(ImportException, "The connection of the table does not exist anymore."):
            PostgresUploadHandler.is_valid({}, self.user, execution_id=str(_exec.exec_id))

    @patch("geonode.upload.celery_tasks.DataPublisher")
    def test_chain_should_publish_the_table_and_store_the_data_item(self, publisher):
        _exec = self.create_execution()
        import_orchestrator.apply(
            args=({}, str(_exec.exec_id)),
            kwargs={"handler": str(self.sut), "action": exa.UPLOAD.value, "step": "start_import"},
            throw=True,
        )
        publisher.return_value.publish_resources.assert_called_once()
        _exec.refresh_from_db()
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, _exec.status)
        _item = DataItem.objects.get()
        self.assertEqual(f"{settings.DEFAULT_WORKSPACE}:roads_{self.connection.pk}", _item.layer)

    @patch("geonode.upload.celery_tasks.DataPublisher")
    def test_chain_should_stop_before_geoserver_on_a_table_without_crs(self, publisher):
        _exec = self.create_execution(geometries=[{"column": "geom", "type": "Unknown", "srid": None}])
        with self.assertRaises(Exception):
            import_orchestrator.apply(
                args=({}, str(_exec.exec_id)),
                kwargs={"handler": str(self.sut), "action": exa.UPLOAD.value, "step": "start_import"},
                throw=True,
            )
        publisher.assert_not_called()
        _exec.refresh_from_db()
        self.assertEqual(ExecutionRequest.STATUS_FAILED, _exec.status)
        self.assertFalse(DataItem.objects.exists())

    def test_execution_should_finish_after_publish(self):
        """No GeoNode resource is created, the orchestrator must close the execution anyway"""
        _exec = self.create_execution()
        orchestrator.perform_next_step(
            str(_exec.exec_id),
            exa.UPLOAD.value,
            str(self.sut),
            step="geonode.upload.publish_resource",
            layer_name="roads_7",
            alternate="roads_7",
        )
        _exec.refresh_from_db()
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, _exec.status)
        self.assertEqual(DataItem.objects.get().pk, _exec.output_params["data_item"])

    @patch.object(PostgresUploadHandler, "_publish_resource_rollback")
    @patch("geonode.upload.celery_tasks.DataPublisher")
    def test_publish_failure_should_roll_back_the_execution(self, publisher, publish_rollback):
        publisher.return_value.publish_resources.side_effect = Exception("GeoServer refused the layer")
        _exec = self.create_execution()
        _args = (
            str(_exec.exec_id),
            "geonode.upload.publish_resource",
            "roads_7",
            "roads_7",
            str(self.sut),
            exa.UPLOAD.value,
        )
        with self.assertRaises(Exception):
            publish_resource.apply(args=_args, throw=True)

        self.assertEqual(str(_exec.exec_id), publish_rollback.call_args.args[0])
        self.assertEqual("roads_7", publish_rollback.call_args.args[1])
        _exec.refresh_from_db()
        self.assertEqual(ExecutionRequest.STATUS_FAILED, _exec.status)
        self.assertFalse(DataItem.objects.exists())

    def test_data_item_should_be_stored_once_published(self):
        _exec = self.create_execution()
        PostgresUploadHandler.perform_last_step(str(_exec.exec_id))
        _item = DataItem.objects.get()
        self.assertEqual("postgresql", _item.source_provider)
        self.assertEqual(self.connection, _item.auth_config)
        self.assertEqual("postgresql:?schema=public&table=Roads", _item.uri)
        self.assertEqual("public.Roads", _item.title)
        self.assertEqual(_exec.input_params["details"], _item.details)
        self.assertEqual(self.user, _item.created_by)
        self.assertEqual(f"{settings.DEFAULT_WORKSPACE}:roads_7", _item.layer)

    def test_data_item_should_not_be_stored_while_publishing(self):
        """A layer that fails to publish leaves no data item behind"""
        _exec = self.create_execution()
        with patch.object(import_resource, "apply_async"):
            orchestrator.perform_next_step(str(_exec.exec_id), exa.UPLOAD.value, str(self.sut), step="start_import")
        self.assertFalse(DataItem.objects.exists())


@patch("geonode.upload.handlers.postgres.handler.DataPublisher")
class PostgresUploadRollbackTests(TestCase):
    def setUp(self):
        self.sut = PostgresUploadHandler()
        self.connection = create_connection()
        self.item = DataItem.objects.create(source_provider="postgresql", uri="roads", auth_config=self.connection)
        self.other = DataItem.objects.create(source_provider="postgresql", uri="rivers", auth_config=self.connection)
        self.exec = ExecutionRequest.objects.create(
            func_name="rollback",
            action=exa.UPLOAD.value,
            input_params={"auth_config_id": self.connection.pk},
            output_params={"data_item": self.item.pk},
        )

    def rollback(self):
        # the arguments the rollback task receives from the publish_resource failure
        _args = (str(self.exec.exec_id), "start_rollback", "roads_7", "roads_7", str(self.sut), ira.ROLLBACK.value)
        self.sut.rollback(str(self.exec.exec_id), "geonode.upload.publish_resource", exa.UPLOAD.value, *_args)

    def test_rollback_should_remove_the_layer_and_the_data_item_of_the_execution(self, publisher):
        _catalog = publisher.return_value.cat
        _store, _layer = MagicMock(), MagicMock()
        _catalog.get_store.return_value = _store
        _catalog.get_resource.return_value = _layer
        _store.get_resources.return_value = [MagicMock()]

        self.rollback()

        _catalog.get_store.assert_called_once_with(
            f"postgis_{self.connection.pk}", workspace=settings.DEFAULT_WORKSPACE
        )
        _catalog.get_resource.assert_called_once_with("roads_7", store=_store, workspace=settings.DEFAULT_WORKSPACE)
        _catalog.delete.assert_called_once_with(_layer, recurse=True)
        self.assertListEqual([self.other], list(DataItem.objects.all()))

    def test_rollback_should_drop_the_store_left_without_layers(self, publisher):
        _catalog = publisher.return_value.cat
        _store, _layer = MagicMock(), MagicMock()
        _catalog.get_store.return_value = _store
        _catalog.get_resource.return_value = _layer
        _store.get_resources.return_value = []

        self.rollback()

        self.assertListEqual([call(_layer, recurse=True), call(_store)], _catalog.delete.call_args_list)

    def test_rollback_should_stop_when_the_store_was_never_created(self, publisher):
        publisher.return_value.cat.get_store.return_value = None
        self.rollback()
        publisher.return_value.cat.delete.assert_not_called()
        self.assertFalse(DataItem.objects.filter(pk=self.item.pk).exists())
