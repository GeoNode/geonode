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
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from geonode.security.auth_handlers import AuthHandler


class FormAuthHandler(AuthHandler):
    """
    Connection of a source provider: the payload is validated by the connection form of the provider
    whose key is the handled type, so the form stays the only definition of the connection parameters
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

        form = source_provider_registry.get(cls.handled_type).connection_form(data=payload)
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
