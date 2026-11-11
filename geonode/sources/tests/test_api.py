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
        # the handshake of a new connection must never reach a real host
        _patcher = patch.object(PostgresSourceProvider, "test_connection", return_value=(True, ""))
        self.test_connection = _patcher.start()
        self.addCleanup(_patcher.stop)

    def _browse_entries(self, *tables):
        return [BrowseEntry(uri=entry_uri(_table), title=f"public.{_table}") for _table in tables]

    def test_anonymous_cannot_list_connections(self):
        response = self.client.get(CONNECTIONS_URL)
        self.assertIn(response.status_code, (401, 403))

    def test_user_cannot_list_connections(self):
        self.client.force_login(self.user)
        self.assertEqual(403, self.client.get(CONNECTIONS_URL).status_code)

    def test_user_cannot_browse_a_connection(self):
        self.client.force_login(self.user)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")) as _browse:
            response = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/browse/")
        self.assertEqual(403, response.status_code)
        _browse.assert_not_called()

    def test_user_cannot_adopt_the_entries_of_a_connection(self):
        self.client.force_login(self.user)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")) as _browse:
            response = self.client.post(
                f"{CONNECTIONS_URL}{self.connection.pk}/adopt/", {"uris": [entry_uri("roads")]}, format="json"
            )
        self.assertEqual(403, response.status_code)
        _browse.assert_not_called()
        self.assertFalse(DataItem.objects.exists())

    def test_staff_can_list_the_providers_with_their_connection_fields(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/v2/source-providers/")
        self.assertEqual(200, response.status_code, response.json())
        _provider = response.json()[0]
        self.assertEqual("postgresql", _provider["key"])
        self.assertListEqual(["READ"], _provider["declared_capabilities"])
        self.assertIn("password", [_field["name"] for _field in _provider["connection_fields"]])

    def test_staff_can_get_a_provider_by_key(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/v2/source-providers/postgresql/")
        self.assertEqual(200, response.status_code, response.json())
        self.assertEqual("postgresql", response.json()["key"])
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
        _data = self.client.get(f"{DATA_ITEMS_URL}{_item.pk}/").json()
        self.assertEqual("uninstalled", _data["source_provider"])
        self.assertListEqual([], _data["capabilities"])

    def test_staff_can_create_a_connection_without_getting_the_secrets_back(self):
        self.client.force_login(self.staff)
        response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(201, response.status_code, response.json())
        _connection = response.json()
        self.assertNotIn("payload", _connection)
        self.assertNotIn("password", _connection["connection"])
        self.assertEqual("db.example.com", _connection["connection"]["host"])

    def test_create_connection_should_not_store_any_data_item(self):
        """Data items are created only when an entry is adopted"""
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")) as _browse:
            response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(201, response.status_code, response.json())
        self.assertEqual(0, response.json()["data_items_count"])
        _browse.assert_not_called()
        self.assertFalse(DataItem.objects.exists())

    def test_create_connection_should_not_save_a_source_that_cannot_be_reached(self):
        """Like a remote service registration: wrong parameters must not leave a connection behind"""
        self.client.force_login(self.staff)
        _connections = AuthConfig.objects.count()
        self.test_connection.return_value = (False, "Could not connect with the provided parameters")
        response = self.client.post(CONNECTIONS_URL, {"type": "postgresql", "payload": PAYLOAD}, format="json")
        self.assertEqual(502, response.status_code)
        self.assertDictEqual({"detail": "Could not reach the source, the connection was not saved."}, response.json())
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
        self.assertListEqual([self.connection.pk], [_item["id"] for _item in response.json()["results"]])

    def test_connection_list_should_use_the_plain_drf_pagination(self):
        """The sources API is plain DRF, without the dynamic-rest envelope"""
        self.client.force_login(self.staff)
        response = self.client.get(CONNECTIONS_URL, {"page_size": 1000})
        self.assertEqual(200, response.status_code, response.json())
        self.assertSetEqual({"count", "next", "previous", "results"}, set(response.json()))
        self.assertEqual(1, response.json()["count"])

    def test_connections_should_report_their_data_items_count(self):
        DataItem.objects.create(source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection)
        DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=create_connection(database="other")
        )
        self.client.force_login(self.staff)
        listed = self.client.get(CONNECTIONS_URL).json()["results"][0]
        detail = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/").json()
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
        """Data items come from the adoption only: title and details are read from the source"""
        self.client.force_login(self.staff)
        response = self.client.post(
            DATA_ITEMS_URL, {"connection": self.connection.pk, "uri": entry_uri("roads")}, format="json"
        )
        self.assertEqual(405, response.status_code)
        self.assertFalse(DataItem.objects.exists())

    def _adopt(self, *tables):
        return self.client.post(
            f"{CONNECTIONS_URL}{self.connection.pk}/adopt/",
            {"uris": [entry_uri(_table) for _table in tables]},
            format="json",
        )

    def test_browse_should_list_the_entries_without_storing_them(self):
        """Browsing is live: the entries already adopted are only flagged"""
        DataItem.objects.create(source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection)
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads", "rivers")):
            response = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/browse/")
        self.assertEqual(200, response.status_code, response.json())
        expected = [
            {"uri": entry_uri("roads"), "title": "public.roads", "details": {}, "adopted": True},
            {"uri": entry_uri("rivers"), "title": "public.rivers", "details": {}, "adopted": False},
        ]
        self.assertListEqual(expected, response.json())
        self.assertEqual(1, DataItem.objects.count())

    def test_browse_should_not_flag_the_items_of_other_connections(self):
        DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=create_connection(database="other")
        )
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")):
            response = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/browse/")
        self.assertFalse(response.json()[0]["adopted"])

    def test_browse_should_not_expose_the_gdal_error(self):
        self.client.force_login(self.staff)
        _error = RuntimeError("PQconnectdb failed: db.example.com")
        with (
            patch.object(PostgresSourceProvider, "browse", side_effect=_error),
            self.assertLogs("geonode.sources.api.views", level="ERROR"),
        ):
            response = self.client.get(f"{CONNECTIONS_URL}{self.connection.pk}/browse/")
        self.assertEqual(502, response.status_code)
        self.assertDictEqual({"detail": "Could not browse the connection."}, response.json())

    def test_adopt_should_store_only_the_chosen_entries(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads", "rivers")):
            response = self._adopt("roads")
        self.assertEqual(201, response.status_code, response.json())
        self.assertListEqual([entry_uri("roads")], [_data["uri"] for _data in response.json()])
        _item = DataItem.objects.get()
        self.assertEqual("public.roads", _item.title)
        self.assertEqual("postgresql", _item.source_provider)
        self.assertEqual(self.staff, _item.created_by)
        self.assertListEqual(["READ"], response.json()[0]["capabilities"])

    def test_adopt_should_be_idempotent(self):
        """Adopting a known entry again must not duplicate nor change it"""
        _item = DataItem.objects.create(
            source_provider="postgresql", uri=entry_uri("roads"), auth_config=self.connection, title="kept"
        )
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")):
            response = self._adopt("roads")
        self.assertEqual(201, response.status_code, response.json())
        self.assertListEqual([_item.pk], [_data["id"] for _data in response.json()])
        _item.refresh_from_db()
        self.assertEqual("kept", _item.title)
        self.assertEqual(1, DataItem.objects.count())

    def test_adopt_should_refuse_an_entry_the_connection_does_not_expose(self):
        """Nothing is stored, not even the valid entries of the same request"""
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")):
            response = self._adopt("roads", "lakes")
        self.assertEqual(400, response.status_code, response.json())
        self.assertFalse(DataItem.objects.exists())

    def test_adopt_should_refuse_an_empty_list(self):
        self.client.force_login(self.staff)
        with patch.object(PostgresSourceProvider, "browse", return_value=self._browse_entries("roads")) as _browse:
            response = self._adopt()
        self.assertEqual(400, response.status_code, response.json())
        _browse.assert_not_called()

    def test_adopt_should_not_expose_the_gdal_error(self):
        self.client.force_login(self.staff)
        _error = RuntimeError("PQconnectdb failed: db.example.com")
        with (
            patch.object(PostgresSourceProvider, "browse", side_effect=_error),
            self.assertLogs("geonode.sources.api.views", level="ERROR"),
        ):
            response = self._adopt("roads")
        self.assertEqual(502, response.status_code)
        self.assertDictEqual({"detail": "Could not browse the connection."}, response.json())
        self.assertFalse(DataItem.objects.exists())

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
        self.assertListEqual([_item.pk], [_data["id"] for _data in response.json()["results"]])

    def test_data_items_filter_should_refuse_a_non_numeric_connection(self):
        self.client.force_login(self.staff)
        response = self.client.get(DATA_ITEMS_URL, {"connection": "abc"})
        self.assertEqual(400, response.status_code)
