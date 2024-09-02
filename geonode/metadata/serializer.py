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

from geonode.base.api.fields import ComplexDynamicRelationField
from geonode.base.api.serializers import (
    LicenseSerializer,
    ResourceManagementField,
    SimpleHierarchicalKeywordSerializer,
    SimpleRegionSerializer,
    SimpleTopicCategorySerializer,
    DynamicRelationField,
)
from geonode.base.models import ResourceBase as RB
from django.conf import settings
from dynamic_rest.serializers import DynamicModelSerializer


class MetadataModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RB  # TODO replace with the metadata model
        name = "metadata"
        view_name = "metadata_view"

    def get_fields(self):
        """
        Dynamically retrieve fields
        """
        return {
            "title": serializers.CharField(max_length=255, help_text="name by which the cited resource is known"),
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
