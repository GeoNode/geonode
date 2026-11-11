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

from rest_framework import serializers

from geonode.api.v3.constants import CONTEXT_KEY


class FieldSelectionMixin:
    """
    Narrows the output to the fields asked with ``?fields=``.
    Only the root serializer reads the requested set, a nested one returns its own ``Meta.default_fields``
    """

    def __init__(self, *args, only_fields=None, **kwargs):
        self._only_fields = set(only_fields) if only_fields is not None else None
        super().__init__(*args, **kwargs)

    @classmethod
    def available_field_names(cls) -> typing.Set[str]:
        """The fields a read can return: write-only ones never appear in a response"""
        return {_name for _name, _field in cls().get_fields().items() if not _field.write_only}

    @classmethod
    def default_field_names(cls) -> typing.Optional[typing.Set[str]]:
        """The fields returned when ``?fields=`` is absent, ``None`` means all of them"""
        _default = getattr(getattr(cls, "Meta", None), "default_fields", None)
        return set(_default) if _default is not None else None

    def get_fields(self):
        _fields = super().get_fields()
        if (_selected := self.__selected_field_names()) is None:
            return _fields
        return {_name: _field for _name, _field in _fields.items() if _name in _selected}

    def __selected_field_names(self) -> typing.Optional[typing.Set[str]]:
        if self._only_fields is not None:
            return self._only_fields
        # the viewset sets the key on reads only, so writes always validate the full serializer
        if CONTEXT_KEY not in self.context:
            return None
        # the context is shared with nested serializers, the requested names belong to the root only
        if self.__is_root():
            return self.context[CONTEXT_KEY]
        return self.default_field_names()

    def __is_root(self) -> bool:
        if self.parent is None:
            return True
        return isinstance(self.parent, serializers.ListSerializer) and self.parent.parent is None


class FieldSelectionSerializer(FieldSelectionMixin, serializers.Serializer):
    """A serializer narrowed by ``?fields=``, for data not read from a model"""


class FieldSelectionModelSerializer(FieldSelectionMixin, serializers.ModelSerializer):
    """A model serializer narrowed by ``?fields=``, which also prepares the queryset its selected fields need"""

    @classmethod
    def setup_queryset(cls, queryset, fields: typing.Set[str], request):
        """Return the queryset with the joins and annotations needed by ``fields``, a nested serializer reuses it"""
        return queryset
