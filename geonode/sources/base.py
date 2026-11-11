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
import enum
import typing
from abc import ABC, abstractmethod

from rest_framework import serializers
from rest_framework.fields import empty

from geonode.security.models import AuthConfig
from geonode.sources.models import DataItem


class Capability(enum.IntFlag):
    """
    What a provider can do with its items, stored as bits so that a provider declares a combination
    (e.g. READ | SCHEMA).
    A missing capability is a statement, not a gap: an item without SCHEMA has no attributes to read.
    """

    NONE = 0
    READ = 1  # the content can be read (features, pixels or raw bytes)
    WRITE = 2  # the content can be changed upstream
    SCHEMA = 4  # the structure can be described (attributes, geometry type, srid)
    TRANSACTIONAL = 8  # several writes can be committed or rolled back together


# a RuntimeError, like the GDAL errors, so that one except catches what any provider raises
class SourceProviderError(RuntimeError):
    """The source could not be reached or read. The cause may expose server details: log it, never return it"""


@dataclasses.dataclass
class BrowseEntry:
    """An item found while browsing a connection, stored as a data item once published"""

    uri: str
    title: str
    details: typing.Dict = dataclasses.field(default_factory=dict)


def serializer_to_connection_fields(serializer_class) -> typing.List[typing.Dict]:
    """Describe a connection serializer for the UI, so that validation and UI come from one definition"""
    fields = []
    for name, field in serializer_class().fields.items():
        if field.style.get("input_type") == "password":
            _type = "password"
        elif isinstance(field, serializers.ChoiceField):
            _type = "choice"
        elif isinstance(field, serializers.IntegerField):
            _type = "integer"
        elif isinstance(field, serializers.URLField):
            _type = "url"
        else:
            _type = "string"
        _field = {"name": name, "label": str(field.label), "type": _type, "required": field.required}
        if field.default is not empty:
            _field["default"] = field.default
        if _type == "choice":
            _field["choices"] = list(field.choices)
        fields.append(_field)
    return fields


class BaseSourceProvider(ABC):
    """
    Reads (and may write) data items of one kind of source.
    The connection parameters live in an AuthConfig whose type is the provider key.
    """

    key: str = None
    label: str = None
    declared_capabilities: Capability = Capability.NONE

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    # serializer validating the AuthConfig payload of a connection, also rendered by the pages
    connection_serializer: typing.Type[serializers.Serializer] = None

    @property
    def connection_fields(self) -> typing.List[typing.Dict]:
        """
        Fields the UI renders to build the AuthConfig payload, each as
        {"name", "label", "type": "string|integer|url|password|choice", "required", "choices"?, "default"?}
        """
        return serializer_to_connection_fields(self.connection_serializer)

    @abstractmethod
    def test_connection(self, auth_config: AuthConfig) -> typing.Tuple[bool, str]:
        """Return (reachable, reason)"""

    @abstractmethod
    def browse(self, auth_config: AuthConfig) -> typing.List[BrowseEntry]:
        """List what the connection exposes, live. Raises a RuntimeError when the source cannot be read"""

    def publish(self, auth_config: AuthConfig, entries: typing.List[BrowseEntry], user) -> typing.Dict[str, str]:
        """
        Store the entries as data items. A provider publishing them somewhere first (e.g. in the local GeoServer)
        overrides it, stores each item once its publication is done and returns the execution id of each uri
        """
        # publishing twice is a no-op: the unique constraint skips the known items
        DataItem.objects.bulk_create(
            [
                DataItem(
                    source_provider=self.key,
                    uri=_entry.uri,
                    auth_config=auth_config,
                    title=_entry.title,
                    details=_entry.details,
                    created_by=user,
                )
                for _entry in entries
            ],
            ignore_conflicts=True,
        )
        return {}

    def unpublish(self, data_item: DataItem) -> None:
        """Hook run before a data item is removed, e.g. to remove its layer from the local GeoServer"""
