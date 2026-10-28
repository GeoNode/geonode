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
from geonode.sources.postgres.auth import PostgresAuthHandler

# RFC 2606 host: the tests never reach a real database, every connection is mocked
PAYLOAD = {"host": "db.example.com", "port": 5432, "database": "gis", "username": "reader", "password": "secret"}


def create_connection(**overrides):
    return PostgresAuthHandler.create_auth_config({**PAYLOAD, **overrides})


def entry_uri(table, schema="public"):
    return f"postgresql:?schema={schema}&table={table}"
