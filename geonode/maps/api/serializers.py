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
import logging
import ast

from dynamic_rest.fields.fields import DynamicRelationField, DynamicField
from dynamic_rest.serializers import DynamicModelSerializer

from geonode.base.api.serializers import (
    BaseDynamicModelSerializer,
    ResourceBaseSerializer,
    ResourceBaseToRepresentationSerializerMixin,
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


class MapLayerDatasetSerializer(
    ResourceBaseToRepresentationSerializerMixin,
    BaseDynamicModelSerializer,
):
    default_style = DynamicRelationField(StyleSerializer, embed=True, many=False, read_only=True)
    styles = DynamicRelationField(StyleSerializer, embed=True, many=True, read_only=True)
    featureinfo_custom_template = FeatureInfoTemplateField()

    class Meta:
        model = Dataset
        name = "dataset"
        view_name = "datasets-list"
        fields = (
            "alternate",
            "featureinfo_custom_template",
            "title",
            "perms",
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
        )


class MapSerializer(ResourceBaseSerializer):
    maplayers = DynamicRelationField(MapLayerSerializer, embed=True, many=True, deferred=False)

    class Meta:
        model = Map
        name = "map"
        view_name = "maps-list"
        fields = (
            "pk",
            "uuid",
            "urlsuffix",
            "featuredurl",
            "data",
            "maplayers",
        )
