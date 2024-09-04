#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from geonode.metadata.engine import FieldsConverter, MetadataEngine
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.fields import empty

metadata_engine = MetadataEngine()


class MetadataListSerializer(serializers.ListSerializer):
    """
    This is the only method to override the listSerializer
    as documented in DRF documentation:
    https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
    """

    @property
    def data(self):
        """
        Return the data for the listing
        """
        return metadata_engine.get_data()


class MetadataSerializer(serializers.Serializer):

    class Meta:
        name = "metadata"
        view_name = "metadata_view"
        list_serializer_class = MetadataListSerializer

    def __new__(cls, *args, **kwargs):
        """
        When a field is instantiated, we store the arguments that were used,
        so that we can present a helpful representation of the object.
        """
        instance = super().__new__(cls, *args, **kwargs)
        if hasattr(instance, "get_fields"):
            instance.fields = instance.get_fields()
        return instance

    def get_fields(self):
        converter = FieldsConverter()
        metadata_fields = metadata_engine.get_fields()
        return converter.convert_fields(metadata_fields, bind=True)
