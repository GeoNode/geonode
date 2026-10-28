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
from unittest.mock import MagicMock, patch

import psycopg2
from django.core.exceptions import ValidationError
from django.test import TestCase
from osgeo import ogr

from geonode.sources.postgres.auth import PostgresAuthHandler
from geonode.sources.postgres.forms import PostgresConnectionForm
from geonode.sources.registry import source_provider_registry
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

    def test_connection_fields_should_come_from_the_connection_form(self):
        actual = self.sut.connection_fields
        self.assertListEqual(list(PostgresConnectionForm.base_fields), [_field["name"] for _field in actual])
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
