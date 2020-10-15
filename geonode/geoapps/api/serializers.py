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
import json

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField

from geonode.geoapps.models import GeoApp, GeoAppData
from geonode.base.api.serializers import ResourceBaseSerializer

import logging

logger = logging.getLogger(__name__)


class AppTypePolymorphicSerializer(DynamicModelSerializer):

    class Meta:
        ref_name = 'GeoApp'
        model = GeoApp
        name = 'GeoApp'

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        _instance = GeoApp.objects.get(id=value)
        _ct = _instance.polymorphic_ctype
        _child = _ct.model_class().objects.filter(pk=value).first()
        if _child:
            return _child.app_type


class GeoAppDataSerializer(DynamicModelSerializer):

    class Meta:
        ref_name = 'GeoAppData'
        model = GeoAppData
        name = 'GeoAppData'
        fields = ('pk', 'blob')

    def to_representation(self, value):
        data = GeoAppData.objects.filter(resource__id=value).first()
        return json.loads(data.blob) if data else {}


class GeoAppSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(GeoAppSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = GeoApp
        name = 'geoapp'
        fields = (
            'pk', 'uuid', 'app_type',
            'zoom', 'projection', 'center_x', 'center_y',
            'urlsuffix', 'data'
        )

    app_type = DynamicRelationField(
        AppTypePolymorphicSerializer,
        source='id',
        read_only=True)

    """
     - Deferred / not Embedded --> ?include[]=data
    """
    data = DynamicRelationField(
        GeoAppDataSerializer,
        source='id',
        many=False,
        embed=False,
        deferred=True)
