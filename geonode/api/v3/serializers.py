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
from rest_framework import serializers

from geonode.api.v3.constants import CONTEXT_KEY  # noqa: F401 - re-exported for convenience


class FieldSelectionModelSerializer(serializers.ModelSerializer):
    """A ``ModelSerializer`` whose output can be narrowed to a subset of fields.
    This class implements the ``?fields=`` query parameter -- JSON:API calls the
    concept a "sparse fieldset", which is a request-time field selection, not a
    stored field.

    The subset comes either from the ``only_fields`` constructor kwarg or from
    ``context["only_fields"]``, which :class:`geonode.api.v3.viewsets.V3ModelViewSet`
    populates from the ``?fields=`` query parameter.

    Only read paths narrow the field set. The viewset does not set the context
    key for unsafe methods, so writes always see the full serializer and keep
    validating required fields.
    """

    def __init__(self, *args, only_fields=None, **kwargs):
        self._only_fields = set(only_fields) if only_fields is not None else None
        super().__init__(*args, **kwargs)

    @classmethod
    def available_field_names(cls):
        """The full set of field names, ignoring any narrowing."""
        return set(cls().get_fields())

    def get_fields(self):
        fields = super().get_fields()
        only = self._only_fields
        if only is None:
            only = self.context.get(CONTEXT_KEY)
        if only is None:
            return fields
        for name in [name for name in fields if name not in only]:
            fields.pop(name)
        return fields
