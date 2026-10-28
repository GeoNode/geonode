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

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from geonode.security.auth_handlers import AuthHandler
from geonode.sources.postgres.forms import PostgresConnectionForm


class PostgresAuthHandler(AuthHandler):
    """Connection parameters of a PostgreSQL/PostGIS source, the type matches the source provider key"""

    handled_type = "postgresql"

    @classmethod
    def validate(cls, payload, instance=None):
        # edited in place, the admin form keeps the dict it passed instead of the returned one
        _stored = instance.payload if getattr(instance, "pk", None) else {}
        for key in [key for key, value in payload.items() if value in ("", None)]:
            del payload[key]
        # a blank value keeps the stored one, so the password is not sent back on every edit
        for key, value in _stored.items():
            payload.setdefault(key, value)

        form = PostgresConnectionForm(data=payload)
        form.is_valid()
        # a form silently drops what it does not know, the payload must not carry it
        if extra := sorted(set(payload) - set(form.fields)):
            form.add_error(None, f"Unknown keys: {', '.join(extra)}.")
        if form.errors:
            # flattened: keyed errors raised inside the admin form clean() would name fields it does not have
            raise ValidationError(
                [
                    message if field == NON_FIELD_ERRORS else f"{field}: {message}"
                    for field, messages in form.errors.items()
                    for message in messages
                ]
            )
        payload.clear()
        payload.update(form.cleaned_data)
        return payload

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
