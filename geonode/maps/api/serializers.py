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

from geonode.maps.models import Map, MapLayer
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


class MapSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    class Meta:
        model = Map
        name = 'map'
        view_name = 'maps-list'
        fields = (
            'pk', 'uuid',
            'zoom', 'projection', 'center_x', 'center_y',
            'urlsuffix', 'featuredurl'
        )
