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
        ret = super().data
        # return metadata_engine.get_data()
        return ReturnList([{"title": "abc"}], serializer=self)


class MetadataModelSerializer(serializers.Serializer):
    class Meta:
        name = "metadata"
        view_name = "metadata_view"
        list_serializer_class = MetadataListSerializer

    def to_representation(self, instance):
        return super().to_representation(instance)

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def get_fields(self):
        converter = FieldsConverter()
        metadata_fields = metadata_engine.get_fields()
        converter.convert_fields(metadata_fields)
        return {}
        """
        Dynamically retrieve fields
        engine = MetadataEngine()
        fields = engine.get_fields() # this should return the list of fields.
        # for example 
        # Field(
        #     name="title", # mandatory
        #     type="int", # mandatory
        #     kwargs={ # optional
        #         "max_length": 255,
        #         "help_text": "name by which the cited resource is known"
        #     }
        # )

        FieldConverted.convert(fields) # internally will convert to a serializer-like object. Take example from https://github.com/encode/django-rest-framework/blob/f593f5752c45e06147231bbfd74c02384791e074/rest_framework/serializers.py#L905
        (the converted should expose the mapping)
        internally the mapping will be something like this:

        mapping = {
            "int": serializers.IntegerField,
            "str": serializers.CharField,
            "choice": serializers.ChoiceField
        }

        internally the convertion can do something like this:
        
        seeing the above field, we expect an output like this
        
        output = {
            "title": serializers.CharField(max_length=255, help_text="name by which the cited resource is known")
        }

        Validations:
         - It can be just one field with a specific name even if are coming from different metadata
         - For some specific fields, some attributes are mandatory so we have to enforce it, otherwise we can add a default
         - if one of the kwargs is not in the field attribute, we just discard it
        '''


        
        return {
            "title": serializers.CharField(help_text="name by which the cited resource is known"),
            "abstract": serializers.CharField(required=False, max_length=2000, help_text=RB.abstract_help_text),
            "attribution": serializers.CharField(
                required=False, max_length=2048, allow_null=True, help_text=RB.attribution_help_text
            ),
            "category": ComplexDynamicRelationField(SimpleTopicCategorySerializer, embed=True),
            "data_quality_statement": serializers.CharField(
                required=False, max_length=2000, allow_null=True, help_text=RB.data_quality_statement_help_text
            ),
            "date": serializers.CharField(required=False, help_text=RB.date_help_text),
            "date_type": serializers.ChoiceField(
                required=False,
                choices=RB.VALID_DATE_TYPES,
                default="publication",
                help_text=RB.date_type_help_text,
            ),
            "keywords": ComplexDynamicRelationField(SimpleHierarchicalKeywordSerializer, many=True),
            "language": serializers.ChoiceField(
                required=False,
                choices=settings.LANGUAGES,
                default="eng",
                help_text=RB.language_help_text,
            ),
            "license": ComplexDynamicRelationField(LicenseSerializer, embed=True),
            "other_constraints": serializers.CharField(
                required=False, allow_null=True, help_text=RB.constraints_other_help_text
            ),
            "regions": DynamicRelationField(
                SimpleRegionSerializer, embed=True, many=True, read_only=True, required=False
            ),
            "featured": ResourceManagementField(
                required=False,
                read_only=False,
                default=False,
                help_text="Should this resource be advertised in home page?",
            ),
            "is_published": ResourceManagementField(
                required=False,
                read_only=False,
                default=True,
                help_text="Should this resource be published and searchable?",
            ),
            "is_approved": ResourceManagementField(
                required=False,
                read_only=False,
                default=True,
                help_text="Is this resource validated from a publisher or editor?",
            ),
        }

        """
