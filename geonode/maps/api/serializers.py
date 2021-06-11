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

from geonode.base.models import ResourceBase
from dynamic_rest.fields.fields import DynamicRelationField
from rest_framework import serializers

from dynamic_rest.serializers import DynamicModelSerializer

from geonode.maps.models import Map, MapData, MapLayer
from geonode.base.api.serializers import ResourceBaseSerializer

import logging
logger = logging.getLogger(__name__)


class MapLayerSerializer(DynamicModelSerializer):

    class Meta:
        model = MapLayer
        name = 'maplayer'
        fields = (
            'pk', 'name', 'store',
            'stack_order', 'format', 'opacity', 'styles',
            'transparent', 'fixed', 'group', 'visibility',
            'ows_url', 'layer_params', 'source_params', 'local'
        )

    name = serializers.CharField(read_only=True)
    store = serializers.CharField(read_only=True)


class MapDataField(DynamicRelationField):

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


class MapAppDataSerializer(DynamicModelSerializer):

    class Meta:
        ref_name = 'MapData'
        model = ResourceBase
        name = 'MapData'
        fields = ('pk', 'data')

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        data = Map.objects.filter(resourcebase_ptr_id=value)
        if data.exists():
            return data.first().data
        return {}


class MapSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(MapSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Map
        name = 'map'
        view_name = 'maps-list'
        fields = (
            'pk', 'uuid',
            'zoom', 'projection', 'center_x', 'center_y',
            'urlsuffix', 'featuredurl', 'data',
        )

    def to_internal_value(self, data):
        if 'data' in data:
            _data = data.pop('data')
            if self.is_valid():
                data['data'] = _data

        return data
    """
     - Deferred / not Embedded --> ?include[]=data
    """
    data = MapDataField(
        MapAppDataSerializer,
        source='id',
        many=False,
        embed=False,
        deferred=True)