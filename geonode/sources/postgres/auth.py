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
import typing

from geonode.sources.auth import FormAuthHandler


class PostgresAuthHandler(FormAuthHandler):
    """Connection parameters of a PostgreSQL/PostGIS source, the type matches the source provider key"""

    handled_type = "postgresql"

    def _init_from_config(self):
        payload = self.config.payload
        self.host = payload.get("host")
        self.port = payload.get("port")
        self.database = payload.get("database")
        self.username = payload.get("username")
        self.password = payload.get("password")
        self.sslmode = payload.get("sslmode")
        self.schema = payload.get("schema")

    def get_credentials(self):
        return (self.username, self.password)

    def get_connection_params(self) -> typing.Dict:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.username,
            "password": self.password,
            "sslmode": self.sslmode,
        }
