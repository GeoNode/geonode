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

from dynamic_rest.fields.fields import DynamicComputedField, DynamicMethodField, DynamicRelationField
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
    styles = DynamicComputedField(source="styles_set", requires=("styles",))
    dataset = DynamicMethodField(
        requires=(
            "store",
            "alternate",
        )
    )

    class Meta:
        model = MapLayer
        name = "maplayer"
        fields = (
            "pk",
            "extra_params",
            "current_style",
            "styles",
            "dataset",
        )

    def get_dataset(self, instance):
        dataset = instance.dataset
        return MapLayerDatasetSerializer(instance=dataset).data


class MapSerializer(ResourceBaseSerializer):
    maplayers = DynamicRelationField(MapLayerSerializer, source="dataset_set", embed=True, many=True)

    class Meta:
        model = Map
        name = "map"
        view_name = "maps-list"
        fields = (
            "pk",
            "uuid",
            "zoom",
            "projection",
            "center_x",
            "center_y",
            "urlsuffix",
            "featuredurl",
            "data",
            "maplayers",
        )
