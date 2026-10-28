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
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from geonode.security.auth_handlers import BasicAuthHandler
from geonode.security.models import AuthConfig, URLPatternAuthConfig
from geonode.sources.base import BrowseEntry
from geonode.sources.models import DataItem
from geonode.sources.postgres.provider import PostgresSourceProvider
from geonode.sources.tests.utils import PAYLOAD, create_connection, entry_uri

CONNECTIONS_URL = "/api/v2/source-connections/"
DATA_ITEMS_URL = "/api/v2/data-items/"


class SourcesApiTests(APITestCase):
    # GeoNode drops sessions without an OAuth token, created on login from these apps
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        self.staff = get_user_model().objects.create_user(username="sources_staff", password="password", is_staff=True)
        self.user = get_user_model().objects.create_user(username="sources_user", password="password")
        self.connection = create_connection()

    def _browse_entries(self, *tables):
        return [BrowseEntry(uri=entry_uri(_table), title=f"public.{_table}") for _table in tables]

    def test_anonymous_cannot_list_connections(self):
        response = self.client.get(CONNECTIONS_URL)
        self.assertIn(response.status_code, (401, 403))

    def test_user_cannot_list_connections(self):
        self.client.force_login(self.user)
        self.assertEqual(403, self.client.get(CONNECTIONS_URL).status_code)

    def test_user_cannot_discover_a_connection(self):
        self.client.force_login(self.user)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")) as _browse:
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(403, response.status_code)
        _browse.assert_not_called()
        self.assertFalse(DataItem.objects.exists())

    def test_staff_can_list_the_providers_with_their_connection_fields(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/v2/source-providers/")
        self.assertEqual(200, response.status_code, response.json())
        _provider = response.json()["source_providers"][0]
        self.assertEqual("postgresql", _provider["key"])
        self.assertListEqual(["READ"], _provider["declared_capabilities"])
        self.assertIn("password", [_field["name"] for _field in _provider["connection_fields"]])

    def test_staff_can_get_a_provider_by_key(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/v2/source-providers/postgresql/")
        self.assertEqual(200, response.status_code, response.json())
        self.assertEqual("postgresql", response.json()["source_provider"]["key"])
        self.assertEqual(404, self.client.get("/api/v2/source-providers/unknown/").status_code)

    def test_user_cannot_list_the_providers(self):
        self.client.force_login(self.user)
        self.assertEqual(403, self.client.get("/api/v2/source-providers/").status_code)

    def test_data_item_of_an_uninstalled_provider_should_have_no_capabilities(self):
        """The row stays, but nothing can read it anymore"""
        _item = DataItem.objects.create(
            source_provider="uninstalled", uri=entry_uri("roads"), auth_config=self.connection
        )
        self.client.force_login(self.staff)
        _data = self.client.get(f"{DATA_ITEMS_URL}{_item.pk}/").json()["data_item"]
        self.assertEqual("uninstalled", _data["source_provider"])
        self.assertListEqual([], _data["capabilities"])

    def test_staff_can_create_a_connection_without_getting_the_secrets_back(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=[]):
            response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(201, response.status_code, response.json())
        _connection = response.json()["source_connection"]
        self.assertNotIn("payload", _connection)
        self.assertNotIn("password", _connection["connection"])
        self.assertEqual("db.example.com", _connection["connection"]["host"])

    def test_create_connection_should_discover_its_data_items_at_once(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads", "rivers")):
            response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(201, response.status_code, response.json())
        self.assertDictEqual({"found": 2, "created": 2, "missing": 0}, response.json()["discovery"])
        self.assertEqual(2, response.json()["source_connection"]["data_items_count"])
        _connection_id = response.json()["source_connection"]["id"]
        self.assertSetEqual(
            {entry_uri("roads"), entry_uri("rivers")},
            set(DataItem.objects.filter(auth_config_id=_connection_id).values_list("uri", flat=True)),
        )

    def test_create_connection_should_not_save_a_source_that_cannot_be_read(self):
        """Like a remote service registration: wrong parameters must not leave a connection behind"""
        self.client.force_login(self.staff)
        _connections = AuthConfig.objects.count()
        with (
            patch.object(
                PostgresSourceProvider, "browse", side_effect=RuntimeError("PQconnectdb failed: db.example.com")
            ),
            self.assertLogs("geonode.sources.api.views", level="ERROR"),
        ):
            response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(502, response.status_code)
        self.assertDictEqual({"detail": "Could not browse the connection, it was not saved."}, response.json())
        self.assertEqual(_connections, AuthConfig.objects.count())

    def test_create_connection_should_fail_with_an_invalid_payload(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            CONNECTIONS_URL, {"type": "postgresql", "payload": {**PAYLOAD, "port": 0, "foo": 1}}, format="json"
        )
        self.assertEqual(400, response.status_code, response.json())

    def test_connection_list_should_not_expose_other_auth_configs(self):
        """AuthConfig is shared with the remote services: only the source provider ones are connections"""
        BasicAuthHandler.create_auth_config({"username": "service", "password": "secret"})
        self.client.force_login(self.staff)
        response = self.client.get(CONNECTIONS_URL)
        self.assertEqual(200, response.status_code, response.json())
        self.assertListEqual([self.connection.pk], [_item["id"] for _item in response.json()["source_connections"]])

    def test_connections_should_report_their_data_items_count(self):
        """Only the available items are counted"""
        DataItem.objects.create(source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection)
        DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("lakes"), auth_config=self.connection, is_available=False
        )
        self.client.force_login(self.staff)
        listed = self.client.get(CONNECTIONS_URL).json()["source_connections"][0]
        detail = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/").json()["source_connection"]
        self.assertEqual(1, listed["data_items_count"])
        self.assertEqual(1, detail["data_items_count"])

    def test_delete_should_remove_the_connection_along_with_its_data_items(self):
        DataItem.objects.create(source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection)
        self.client.force_login(self.staff)
        self.assertEqual(204, self.client.delete(f"{CONNECTIONS_URL}{self.connection.pk}/").status_code)
        self.assertFalse(AuthConfig.objects.filter(pk=self.connection.pk).exists())
        self.assertFalse(DataItem.objects.exists())

    def test_delete_should_refuse_a_connection_used_elsewhere(self):
        """A connection also used by a url pattern must not disappear along with its pattern"""
        URLPatternAuthConfig.objects.create(auth_config=self.connection, pattern="https://data.example.com/.*")
        self.client.force_login(self.staff)
        response = self.client.delete(f"{CONNECTIONS_URL}{self.connection.pk}/")
        self.assertEqual(400, response.status_code, response.json())
        self.assertTrue(AuthConfig.objects.filter(pk=self.connection.pk).exists())
        self.assertTrue(URLPatternAuthConfig.objects.filter(auth_config=self.connection).exists())

    def test_data_items_should_not_be_created_through_the_api(self):
        """Data items come from the discovery only"""
        self.client.force_login(self.staff)
        response = self.client.post(
            DATA_ITEMS_URL, {"connection": self.connection.pk, "uri": entry_uri("roads")}, format="json"
        )
        self.assertEqual(405, response.status_code)
        self.assertFalse(DataItem.objects.exists())

    def test_discover_should_store_every_entry_as_a_data_item(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads", "rivers")):
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(200, response.status_code, response.json())
        self.assertDictEqual({"found": 2, "created": 2, "missing": 0}, response.json())
        _item = DataItem.objects.get(uri=entry_uri("roads"))
        self.assertEqual("public.roads", _item.title)
        _data = self.client.get(f"{DATA_ITEMS_URL}{_item.pk}/").json()["data_item"]
        self.assertEqual("postgresql", _data["source_provider"])
        self.assertListEqual(["READ"], _data["capabilities"])
        self.assertTrue(_item.is_available)
        self.assertIsNotNone(_item.last_seen)
        self.assertEqual(self.staff, _item.created_by)

    def test_discover_should_refresh_the_known_items_and_flag_the_missing_ones(self):
        """A table gone upstream is kept as not available, one coming back is available again"""
        _roads = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection, title="old"
        )
        _lakes = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("lakes"), auth_config=self.connection
        )
        _rivers = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("rivers"), auth_config=self.connection, is_available=False
        )
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads", "rivers")):
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(200, response.status_code, response.json())
        self.assertDictEqual({"found": 2, "created": 0, "missing": 1}, response.json())
        for _item in (_roads, _lakes, _rivers):
            _item.refresh_from_db()
        self.assertEqual("public.roads", _roads.title)
        self.assertTrue(_roads.is_available)
        self.assertTrue(_rivers.is_available)
        self.assertFalse(_lakes.is_available)
        self.assertEqual(3, DataItem.objects.count())

    def test_discover_should_not_touch_the_items_of_other_connections(self):
        _other = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("lakes"), auth_config=create_connection(database="other")
        )
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")):
            self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        _other.refresh_from_db()
        self.assertTrue(_other.is_available)

    def test_discover_should_not_expose_the_gdal_error(self):
        self.client.force_login(self.staff)
        _error = RuntimeError("PQconnectdb failed: db.example.com")
        with (
            patch.object(PostgresSourceProvider, "browse", side_effect=_error),
            self.assertLogs("geonode.sources.api.views", level="ERROR"),
        ):
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(502, response.status_code)
        self.assertDictEqual({"detail": "Could not browse the connection."}, response.json())

    def test_discover_should_refuse_an_empty_answer_if_the_connection_has_available_items(self):
        """A mistyped schema returns nothing: the known items must not be flagged as missing"""
        _item = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection
        )
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=[]):
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(400, response.status_code, response.json())
        _item.refresh_from_db()
        self.assertTrue(_item.is_available)

    def test_discover_should_accept_an_empty_answer_if_the_connection_has_no_available_items(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=[]):
            response = self.client.post(f"{CONNECTIONS_URL}{self.connection.pk}/discover/")
        self.assertEqual(200, response.status_code, response.json())
        self.assertDictEqual({"found": 0, "created": 0, "missing": 0}, response.json())

    def test_data_items_should_be_filtered_by_connection(self):
        _item = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection
        )
        DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=create_connection(database="other")
        )
        self.client.force_login(self.staff)
        response = self.client.get(DATA_ITEMS_URL, {"connection": self.connection.pk})
        self.assertEqual(200, response.status_code, response.json())
        self.assertListEqual([_item.pk], [_data["id"] for _data in response.json()["data_items"]])

    def test_data_items_filter_should_refuse_a_non_numeric_connection(self):
        self.client.force_login(self.staff)
        response = self.client.get(DATA_ITEMS_URL, {"connection": "abc"})
        self.assertEqual(400, response.status_code)
