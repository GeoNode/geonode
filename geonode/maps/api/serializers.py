#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import ast
import logging

from dynamic_rest.fields.fields import DynamicField, DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ParseError, ValidationError

from geonode.base.api.serializers import (
    DetailUrlField,
    BaseDynamicModelSerializer,
    ResourceBaseSerializer,
    PermsSerializer,
    LinksSerializer,
)
from geonode.layers.api.serializers import FeatureInfoTemplateField, StyleSerializer
from geonode.layers.models import Dataset
from geonode.maps.models import Map, MapLayer

logger = logging.getLogger(__name__)


class DynamicListAsStringField(DynamicField):
    def to_representation(self, value):
        return ast.literal_eval(value) if isinstance(value, str) else value

    def to_internal_value(self, data):
        return str(data)


class DynamicFullyEmbedM2MRelationField(DynamicRelationField):
    def __init__(self, serializer_class, queryset=None, sideloading=None, debug=False, **kwargs):
        kwargs["queryset"] = queryset
        kwargs["sideloading"] = sideloading
        kwargs["debug"] = debug
        # Assures embed and many are always true
        kwargs["many"] = True
        kwargs["embed"] = True
        super(DynamicFullyEmbedM2MRelationField, self).__init__(serializer_class, **kwargs)

    def to_internal_value_single(self, data, serializer):
        """Return the underlying object, given the serialized form."""
        related_model = serializer.Meta.model
        instance = None

        # When updating a Map element, it's possible to update or create new m2m elements
        if self.root_serializer.instance and ("pk" in data or "id" in data):
            instance_pk = data["pk"] if "pk" in data else data["id"]
            # Get object
            if instance_pk is not None:
                try:
                    instance = related_model.objects.get(pk=instance_pk)
                except related_model.DoesNotExist:
                    raise ValidationError(
                        f"Invalid value for '{self.field_name}': {related_model.__name__} object with ID={data} not found"
                    )

        # If we found a instance, we should update it instead of creating a new one
        if instance and not serializer.instance:
            serializer.instance = instance

        # Save object
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return instance

    def to_internal_value(self, data):
        """Return the underlying object(s), given the serialized form."""
        if not isinstance(data, list):
            raise ParseError(f"'{self.field_name}' value must be a list")

        instance_list = []
        instance_pk_list = []
        for instance_data in data:
            if isinstance(instance_data, self.serializer_class.Meta.model):
                return instance_data
            serializer = self.get_serializer(data=instance_data, many=False)
            instance = self.to_internal_value_single(instance_data, serializer)
            instance_list.append(instance)
            instance_pk_list.append(instance.pk)

        # Delete removed instances
        if self.root_serializer.instance:
            m2m_field_manager = getattr(self.root_serializer.instance, self.field_name)
            m2m_field_manager.exclude(pk__in=instance_pk_list).delete()

        return instance_list


class MapLayerDatasetSerializer(DynamicModelSerializer):
    default_style = DynamicRelationField(StyleSerializer, embed=True, many=False, read_only=True)
    styles = DynamicRelationField(StyleSerializer, embed=True, many=True, read_only=True)
    featureinfo_custom_template = FeatureInfoTemplateField()

    perms = DynamicRelationField(PermsSerializer, source="id", read_only=True)
    links = DynamicRelationField(LinksSerializer, source="id", read_only=True)

    class Meta:
        model = Dataset
        name = "dataset"
        fields = (
            "alternate",
            "featureinfo_custom_template",
            "title",
            "perms",
            "links",
            "pk",
            "has_time",
            "default_style",
            "styles",
            "ptype",
        )


class MapLayerSerializer(DynamicModelSerializer):
    dataset = DynamicRelationField(MapLayerDatasetSerializer, embed=True)

    class Meta:
        model = MapLayer
        name = "maplayer"
        fields = (
            "pk",
            "extra_params",
            "current_style",
            "dataset",
            "name",
            "order",
            "visibility",
            "opacity",
        )


class SimpleMapLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        name = "maplayer"
        fields = ("pk", "name", "extra_params", "current_style", "order", "visibility", "opacity")


class MapSerializer(ResourceBaseSerializer):
    maplayers = DynamicFullyEmbedM2MRelationField(MapLayerSerializer, deferred=False)

    class Meta:
        model = Map
        name = "map"
        view_name = "maps-list"
        fields = list(
            set(
                ResourceBaseSerializer.Meta.fields
                + (
                    "uuid",
                    "urlsuffix",
                    "featuredurl",
                    "data",
                    "maplayers",
                )
            )
        )


class SimpleMapSerializer(BaseDynamicModelSerializer):
    detail_url = DetailUrlField(read_only=True)

    class Meta:
        model = Map
        name = "map"
        view_name = "maps-list"
        fields = (
            "pk",
            "title",
            "detail_url",
        )
