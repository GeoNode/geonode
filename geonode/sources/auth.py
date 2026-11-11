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
from django.core.exceptions import ValidationError
from rest_framework.settings import api_settings

from geonode.security.auth_handlers import AuthHandler


class SourceConnectionAuthHandler(AuthHandler):
    """
    Connection of a source provider: the payload is validated by the connection serializer of the provider
    whose key is the handled type, so the serializer stays the only definition of the connection parameters
    """

    @classmethod
    def validate(cls, payload, instance=None):
        # here to avoid circular import
        from geonode.sources.registry import source_provider_registry

        # edited in place, the admin form keeps the dict it passed instead of the returned one
        _stored = instance.payload if getattr(instance, "pk", None) else {}
        for key in [key for key, value in payload.items() if value in ("", None)]:
            del payload[key]
        # a blank value keeps the stored one, so the password is not sent back on every edit
        for key, value in _stored.items():
            payload.setdefault(key, value)

        _serializer = source_provider_registry.get(cls.handled_type).connection_serializer(data=payload)
        _serializer.is_valid()
        _errors = dict(_serializer.errors)
        # unknown keys are silently dropped by a serializer, the payload must not carry them
        if extra := sorted(set(payload) - set(_serializer.fields)):
            _errors.setdefault(api_settings.NON_FIELD_ERRORS_KEY, []).append(f"Unknown keys: {', '.join(extra)}.")
        if _errors:
            # flattened: keyed errors raised inside the admin form clean() would name fields it does not have
            raise ValidationError(
                [
                    str(message) if field == api_settings.NON_FIELD_ERRORS_KEY else f"{field}: {message}"
                    for field, messages in _errors.items()
                    for message in messages
                ]
            )
        payload.clear()
        payload.update(_serializer.validated_data)
        return payload
