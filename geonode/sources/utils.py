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
import typing

from django.db.models import QuerySet

from geonode.security.models import AuthConfig
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry


def source_connections():
    """AuthConfig is shared with other apps, only the ones of a source provider are connections"""
    return AuthConfig.objects.filter(type__in=source_provider_registry.keys)


def public_payload(auth_config: AuthConfig) -> typing.Dict:
    """The connection parameters that are safe to show: everything but the password fields"""
    _provider = source_provider_registry.get(auth_config.type)
    if not _provider:
        return {}
    _secrets = {_field["name"] for _field in _provider.connection_fields if _field["type"] == "password"}
    return {_key: _value for _key, _value in auth_config.payload.items() if _key not in _secrets}


class UnknownEntryError(Exception):
    """Some of the requested uris are not exposed by the connection"""


def browse_connection(auth_config: AuthConfig) -> typing.List[typing.Dict]:
    """List what the connection exposes, live: nothing is stored"""
    _provider = source_provider_registry.get(auth_config.type)
    _published = set(DataItem.objects.filter(auth_config=auth_config).values_list("uri", flat=True))

    _entries = []
    for _entry in _provider.browse(auth_config):
        _data = dataclasses.asdict(_entry)
        _data["published"] = _entry.uri in _published
        _entries.append(_data)
    return _entries


def publish_entries(auth_config: AuthConfig, uris: typing.List[str], user) -> typing.Tuple[QuerySet, typing.Dict]:
    """Publish the given entries of the connection: the data items, and the executions still publishing the others"""
    _provider = source_provider_registry.get(auth_config.type)
    # title and details come from the source, never from the caller
    _entries = {_entry.uri: _entry for _entry in _provider.browse(auth_config)}
    _uris = set(uris)
    if _uris - set(_entries):
        raise UnknownEntryError()
    _known = set(DataItem.objects.filter(auth_config=auth_config, uri__in=_uris).values_list("uri", flat=True))
    _executions = _provider.publish(auth_config, [_entries[_uri] for _uri in sorted(_uris - _known)], user)
    return DataItem.objects.filter(auth_config=auth_config, uri__in=uris).order_by("title", "id"), _executions
