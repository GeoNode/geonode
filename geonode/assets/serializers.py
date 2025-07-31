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
import os
from django.contrib.auth import get_user_model

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicComputedField
from geonode.assets.local import LocalAssetHandler
from geonode.base.models import ResourceBase
from geonode.storage.manager import StorageManager
from geonode.assets.utils import create_asset, create_asset_and_link
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from geonode.security.registry import permissions_registry

from geonode.assets.models import (
    Asset,
    LocalAsset,
)
from rest_framework.exceptions import PermissionDenied
from django.conf import settings


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

    owner = SimpleUserSerializer(embed=False, required=False, read_only=True)
    asset_type = ClassTypeField(required=False)
    subinfo = AssetSubclassField(required=False)

    class Meta:
        model = Asset
        name = "asset"
        # fields = ("pk", "title", "description", "type", "owner", "created")
        fields = ("pk", "title", "description", "type", "owner", "created", "asset_type", "subinfo")
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "type": {"required": False},
            "created": {"required": False, "read_only": True},
        }


class LocalAssetSerializer(AssetSerializer):
    file = serializers.FileField(write_only=True, required=True)
    resource_id = serializers.IntegerField(required=False)

    class Meta(AssetSerializer.Meta):
        model = LocalAsset
        name = "local_asset"
        fields = AssetSerializer.Meta.fields + ("location", "file", "resource_id")
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "type": {"required": False},
            "location": {"required": False, "read_only": True},
        }

    def create(self, validated_data):
        file = validated_data.pop("file")
        resource_id = validated_data.pop("resource_id", None)
        title = validated_data.pop("title", None)
        description = validated_data.pop("description", None)
        asset_type = validated_data.pop("type", None)
        user = self.context["request"].user

        resource = None

        if file and not os.path.splitext(file.name)[1].lower()[1:] in settings.ALLOWED_DOCUMENT_TYPES:
            logger.debug("This file type is not allowed")
            raise serializers.ValidationError("This file type is not allowed")

        if resource_id:
            resource = get_object_or_404(ResourceBase, pk=resource_id)
            if not permissions_registry.user_has_perm(
                user, resource.get_self_resource(), "change_resourcebase", include_virtual=True
            ):
                logger.debug("The user does not have permissions to change the resource selected")
                raise PermissionDenied("The user does not have permissions to change the resource selected")

        if not title:
            title = file.name

        handler = LocalAssetHandler()
        asset_dir = handler._create_asset_dir()

        storage_manager = StorageManager(remote_files={"file": file})
        storage_manager.clone_remote_files(cloning_directory=asset_dir, create_tempdir=False)

        retrieved_paths = storage_manager.get_retrieved_paths()
        file_path = retrieved_paths.get("file")

        if not file_path:
            logger.debug("Could not save the file.")
            raise serializers.ValidationError("Could not save the file.")

        if resource:
            localasset, _ = create_asset_and_link(
                resource,
                user,
                [file_path],
                title=title,
                description=description,
                asset_type=asset_type,
                clone_files=False,
            )
        else:
            localasset = create_asset(
                user, [file_path], title=title, description=description, asset_type=asset_type, clone_files=False
            )

        return localasset
