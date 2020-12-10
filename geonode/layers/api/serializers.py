# -*- coding: utf-8 -*-
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
from rest_framework import serializers

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField

from geonode.layers.models import Layer, Style, Attribute
from geonode.base.api.serializers import ResourceBaseSerializer

import logging

logger = logging.getLogger(__name__)


class StyleSerializer(DynamicModelSerializer):

    class Meta:
        model = Style
        name = 'style'
        fields = (
            'pk', 'name', 'workspace', 'sld_title', 'sld_body', 'sld_version', 'sld_url'
        )

    name = serializers.CharField(read_only=True)
    workspace = serializers.CharField(read_only=True)


class AttributeSerializer(DynamicModelSerializer):

    class Meta:
        model = Attribute
        name = 'attribute'
        fields = (
            'pk', 'attribute', 'description',
            'attribute_label', 'attribute_type', 'visible',
            'display_order', 'featureinfo_type',
            'count', 'min', 'max', 'average', 'median', 'stddev', 'sum',
            'unique_values', 'last_stats_updated'
        )

    attribute = serializers.CharField(read_only=True)


class LayerSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(LayerSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Layer
        name = 'layer'
        fields = (
            'pk', 'uuid', 'name', 'workspace', 'store', 'storeType', 'charset',
            'is_mosaic', 'has_time', 'has_elevation', 'time_regex', 'elevation_regex',
            'use_featureinfo_custom_template', 'featureinfo_custom_template',
            'default_style', 'styles', 'attribute_set'
        )

    name = serializers.CharField(read_only=True)
    workspace = serializers.CharField(read_only=True)
    store = serializers.CharField(read_only=True)
    storeType = serializers.CharField(read_only=True)
    charset = serializers.CharField(read_only=True)

    default_style = DynamicRelationField(StyleSerializer, embed=True, many=False, read_only=True)
    styles = DynamicRelationField(StyleSerializer, embed=True, many=True, read_only=True)

    attribute_set = DynamicRelationField(AttributeSerializer, embed=True, many=True, read_only=True)
