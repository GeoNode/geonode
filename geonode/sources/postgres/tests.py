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
import dataclasses
from unittest.mock import MagicMock, patch

import psycopg2
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from osgeo import ogr

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.resource.models import ExecutionRequest
from geonode.sources.base import BrowseEntry
from geonode.sources.models import DataItem
from geonode.sources.postgres.auth import PostgresAuthHandler
from geonode.sources.postgres.serializers import PostgresConnectionSerializer
from geonode.sources.registry import source_provider_registry
from geonode.upload.handlers.postgres.handler import PostgresUploadHandler
from geonode.sources.tests.utils import PAYLOAD, create_connection, entry_uri


class PostgresAuthHandlerTests(TestCase):
    def test_validate_should_fill_the_defaults(self):
        expected = {**PAYLOAD, "port": 5432, "sslmode": "prefer", "schema": "public"}
        actual = PostgresAuthHandler.validate({_key: _value for _key, _value in PAYLOAD.items() if _key != "port"})
        self.assertDictEqual(expected, actual)

    def test_validate_should_keep_the_spaces_of_the_password(self):
        self.assertEqual(" s3 cret ", PostgresAuthHandler.validate({**PAYLOAD, "password": " s3 cret "})["password"])

    def test_validate_should_fail_on_unknown_keys(self):
        with self.assertRaises(ValidationError) as ctx:
            PostgresAuthHandler.validate({**PAYLOAD, "foo": "bar"})
        self.assertIn("Unknown keys: foo.", ctx.exception.messages)

    def test_validate_should_raise_a_flat_list_of_messages(self):
        """Keyed errors would crash the admin AuthConfig form, which has no field named like ours"""
        with self.assertRaises(ValidationError) as ctx:
            PostgresAuthHandler.validate({**PAYLOAD, "port": 0})
        self.assertFalse(hasattr(ctx.exception, "error_dict"))
        self.assertTrue(any(_message.startswith("port: ") for _message in ctx.exception.messages))

    def test_validate_should_keep_the_stored_password_when_left_blank(self):
        _connection = create_connection()
        actual = PostgresAuthHandler.validate({**PAYLOAD, "password": ""}, instance=_connection)
        self.assertEqual(PAYLOAD["password"], actual["password"])


class PostgresSourceProviderTests(TestCase):
    def setUp(self):
        self.sut = source_provider_registry.get("postgresql")
        self.connection = create_connection()

    @staticmethod
    def _layer(name, geometries):
        _fields = []
        for _column, _type, _srid in geometries:
            _field = MagicMock()
            _field.GetName.return_value = _column
            _field.GetType.return_value = _type
            _field.GetSpatialRef.return_value.GetAuthorityCode.return_value = _srid
            _fields.append(_field)
        _layer = MagicMock()
        _layer.GetName.return_value = name
        _layer.GetLayerDefn.return_value.GetGeomFieldCount.return_value = len(_fields)
        _layer.GetLayerDefn.return_value.GetGeomFieldDefn.side_effect = lambda idx: _fields[idx]
        return _layer

    def test_connection_fields_should_come_from_the_connection_serializer(self):
        actual = self.sut.connection_fields
        self.assertListEqual(list(PostgresConnectionSerializer().fields), [_field["name"] for _field in actual])
        self.assertEqual("password", next(_field for _field in actual if _field["name"] == "password")["type"])

    @patch("geonode.sources.postgres.provider.psycopg2.connect")
    def test_test_connection_should_open_a_read_only_session(self, connect):
        self.assertTupleEqual((True, ""), self.sut.test_connection(self.connection))
        connect.assert_called_once()
        self.assertIn("default_transaction_read_only=on", connect.call_args.args[0])

    @patch("geonode.sources.postgres.provider.psycopg2.connect")
    def test_test_connection_should_not_expose_the_driver_message(self, connect):
        connect.side_effect = psycopg2.OperationalError('password authentication failed for user "reader"')
        success, message = self.sut.test_connection(self.connection)
        self.assertFalse(success)
        self.assertNotIn("reader", message)

    @patch("geonode.sources.postgres.provider.gdal.OpenEx")
    def test_browse_should_return_one_entry_per_table_of_the_connection_schema(self, open_ex):
        _dataset = MagicMock()
        _dataset.GetLayerCount.return_value = 2
        _dataset.GetLayer.side_effect = [
            self._layer("roads", [("geom", ogr.wkbLineString, "4326")]),
            self._layer("lookup", []),
        ]
        open_ex.return_value.__enter__.return_value = _dataset

        actual = self.sut.browse(self.connection)

        self.assertListEqual([entry_uri("roads"), entry_uri("lookup")], [_entry.uri for _entry in actual])
        self.assertListEqual(
            [{"column": "geom", "type": ogr.GeometryTypeToName(ogr.wkbLineString), "srid": "4326"}],
            actual[0].details["geometries"],
        )
        self.assertListEqual([], actual[1].details["geometries"])
        self.assertIn("SCHEMAS=public", open_ex.call_args.kwargs["open_options"])


class PostgresSourceProviderPublishTests(TestCase):
    @patch("geonode.sources.postgres.provider.import_orchestrator.apply_async")
    def test_publish_should_start_one_execution_per_table(self, apply_async):
        _connection = create_connection()
        _entries = [
            BrowseEntry(uri=entry_uri(_table), title=f"public.{_table}", details={"schema": "public", "table": _table})
            for _table in ("Roads", "rivers")
        ]
        actual = source_provider_registry.get("postgresql").publish(
            _connection, _entries, get_user_model().objects.create(username="publisher")
        )

        self.assertEqual(2, apply_async.call_count)
        self.assertListEqual([_call.args[0][1] for _call in apply_async.call_args_list], list(actual.values()))
        for _entry, _call in zip(_entries, apply_async.call_args_list):
            _exec_id = _call.args[0][1]
            self.assertDictEqual(
                {
                    "handler_module_path": "geonode.upload.handlers.postgres.handler.PostgresUploadHandler",
                    "files": {},
                    "source_provider": "postgresql",
                    "auth_config_id": _connection.pk,
                    **dataclasses.asdict(_entry),
                },
                ExecutionRequest.objects.get(exec_id=_exec_id).input_params,
            )
            # the same start as the upload API: the importer names the layer in its import_resource step
            self.assertTupleEqual(({}, _exec_id), _call.args[0])
            expected = {
                "handler": "geonode.upload.handlers.postgres.handler.PostgresUploadHandler",
                "action": exa.UPLOAD.value,
                "step": "start_import",
            }
            self.assertDictEqual(expected, _call.args[1])

    @patch("geonode.sources.postgres.provider.import_orchestrator.apply_async")
    def test_publish_should_skip_a_table_still_being_published(self, apply_async):
        """A second execution would fail as a duplicate, and its rollback would remove the layer of the first"""
        _connection = create_connection()
        _entry = BrowseEntry(
            uri=entry_uri("roads"), title="public.roads", details={"schema": "public", "table": "roads"}
        )
        _running = ExecutionRequest.objects.create(
            func_name="start_import",
            status=ExecutionRequest.STATUS_RUNNING,
            input_params={"auth_config_id": _connection.pk, "uri": _entry.uri},
        )
        actual = source_provider_registry.get("postgresql").publish(
            _connection, [_entry], get_user_model().objects.create(username="publisher")
        )
        apply_async.assert_not_called()
        self.assertDictEqual({_entry.uri: str(_running.exec_id)}, actual)

    @patch.object(PostgresUploadHandler, "remove_layer")
    def test_unpublish_should_remove_the_layer_of_the_item(self, remove_layer):
        _connection = create_connection()
        _item = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=_connection, layer="geonode:roads_9"
        )
        source_provider_registry.get("postgresql").unpublish(_item)
        remove_layer.assert_called_once_with(_connection.pk, "geonode:roads_9")

    @patch.object(PostgresUploadHandler, "remove_layer")
    def test_unpublish_should_skip_an_item_without_layer(self, remove_layer):
        _item = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=create_connection()
        )
        source_provider_registry.get("postgresql").unpublish(_item)
        remove_layer.assert_not_called()
