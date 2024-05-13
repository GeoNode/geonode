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

from django.contrib.auth import get_user_model

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicComputedField

from geonode.assets.models import (
    Asset,
    LocalAsset,
)

logger = logging.getLogger(__name__)


class ClassTypeField(DynamicComputedField):

    def get_attribute(self, instance):
        return type(instance).__name__


class SimpleUserSerializer(DynamicModelSerializer):
    class Meta:
        model = get_user_model()
        name = "user"
        fields = ("pk", "username")


class AssetSubclassField(DynamicComputedField):
    """
    Just an ugly hack.
    TODO: We need a way to automatically use a proper serializer for each Asset subclass
    in order to render different instances in a list
    """

    def get_attribute(self, instance):
        if type(instance).__name__ == "LocalAsset":
            return {"locations": instance.location}

        return None


class AssetSerializer(DynamicModelSerializer):

    owner = SimpleUserSerializer(embed=False)
    asset_type = ClassTypeField()
    subinfo = AssetSubclassField()

    class Meta:
        model = Asset
        name = "asset"
        # fields = ("pk", "title", "description", "type", "owner", "created")
        fields = ("pk", "title", "description", "type", "owner", "created", "asset_type", "subinfo")


class LocalAssetSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = LocalAsset
        name = "local_asset"
        fields = AssetSerializer.Meta.fields + ("location",)
