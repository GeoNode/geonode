#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import json

from django.core.exceptions import ValidationError
from dynamic_rest.fields.fields import DynamicRelationField


class ComplexDynamicRelationField(DynamicRelationField):
    def to_internal_value_single(self, data, serializer):
        """Overwrite of DynamicRelationField implementation to handle complex data structure initialization

        Args:
            data (Optional[str, Dict]}): serialized or deserialized data from http calls (POST, GET ...)
            serializer (DynamicModelSerializer): Serializer for the given data

        Raises:
            ValidationError: raised when requested data does not exist

            django.db.models.QuerySet: return QuerySet object of the request or set data
        """
        related_model = serializer.Meta.model
        if isinstance(data, str):
            data = json.loads(data)

        if isinstance(data, dict):
            try:
                if hasattr(serializer, "many") and serializer.many is True:
                    return [serializer.get_model().objects.get(**d) for d in data]
                return serializer.get_model().objects.get(**data)
            except related_model.DoesNotExist:
                raise ValidationError(
                    "Invalid value for '%s': %s object with ID=%s not found"
                    % (self.field_name, related_model.__name__, data)
                )
        else:
            return super().to_internal_value_single(data, serializer)
