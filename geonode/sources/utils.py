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

from django.db import transaction
from django.utils import timezone

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


class EmptyDiscoveryError(Exception):
    """The connection exposes nothing while it still has available items"""


def discover_connection(auth_config: AuthConfig, user) -> typing.Dict[str, int]:
    """
    Store every entry of the connection as a data item, refreshing the cached ones.
    Items gone upstream are flagged as not available instead of being deleted
    """
    _provider = source_provider_registry.get(auth_config.type)
    # keyed by uri: the upsert fails if the same row is touched twice in one statement
    _entries = {_entry.uri: _entry for _entry in _provider.browse(auth_config)}
    # an empty answer is more likely a wrong parameter (e.g. a mistyped schema) than every table dropped at once
    if not _entries and DataItem.objects.filter(auth_config=auth_config, is_available=True).exists():
        raise EmptyDiscoveryError()
    _known = set(DataItem.objects.filter(auth_config=auth_config).values_list("uri", flat=True))
    _now = timezone.now()
    with transaction.atomic():
        DataItem.objects.bulk_create(
            [
                DataItem(
                    source_provider=_provider.key,
                    uri=_entry.uri,
                    auth_config=auth_config,
                    title=_entry.title,
                    details=_entry.details,
                    is_available=True,
                    last_seen=_now,
                    created_by=user,
                )
                for _entry in _entries.values()
            ],
            update_conflicts=True,
            unique_fields=["auth_config", "uri"],
            update_fields=["title", "details", "is_available", "last_seen", "updated"],
        )
        _missing = (
            DataItem.objects.filter(auth_config=auth_config, is_available=True)
            .exclude(last_seen=_now)
            .update(is_available=False)
        )
    return {"found": len(_entries), "created": len(_entries.keys() - _known), "missing": _missing}
