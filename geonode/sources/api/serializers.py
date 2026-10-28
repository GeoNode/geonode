#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import typing

from django.core.exceptions import ValidationError as DjangoValidationError
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework import serializers

from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.sources.base import Capability
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry
from geonode.sources.utils import public_payload


def capability_names(value: int) -> typing.List[str]:
    return [_cap.name for _cap in Capability if _cap.value and value & _cap]


class SourceProviderSerializer(serializers.Serializer):
    """A provider is code: it is read from the registry, never from the database"""

    key = serializers.CharField()
    label = serializers.CharField()
    declared_capabilities = serializers.SerializerMethodField()
    connection_fields = serializers.ListField()

    def get_declared_capabilities(self, obj):
        return capability_names(obj.declared_capabilities)


class SourceConnectionSerializer(DynamicModelSerializer):
    """
    A connection is an AuthConfig whose type is a source provider key.
    The payload is write only: secrets never leave the server
    """

    payload = serializers.DictField(write_only=True)
    connection = serializers.SerializerMethodField()
    data_items_count = serializers.SerializerMethodField()

    class Meta:
        model = AuthConfig
        name = "source_connection"
        fields = ("id", "type", "payload", "connection", "data_items_count")

    def get_connection(self, obj):
        return public_payload(obj)

    def get_data_items_count(self, obj):
        # annotated on lists, counted for the single object returned by a create or an update
        if hasattr(obj, "data_items_count"):
            return obj.data_items_count
        return obj.data_items.filter(is_available=True).count()

    def validate_type(self, value):
        if self.instance and self.instance.type != value:
            raise serializers.ValidationError("The provider of a connection cannot change.")
        if not source_provider_registry.get(value):
            raise serializers.ValidationError("Unknown source provider.")
        return value

    def validate(self, attrs):
        _type = attrs.get("type") or self.instance.type
        try:
            attrs["payload"] = auth_handler_registry.get_handler_class(_type).validate(
                attrs.get("payload") or {}, instance=self.instance
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError({"payload": e.messages})
        return attrs

    def create(self, validated_data):
        _handler_cls = auth_handler_registry.get_handler_class(validated_data["type"])
        return _handler_cls.create_auth_config(validated_data["payload"])

    def update(self, instance, validated_data):
        instance.payload = validated_data["payload"]
        instance.save()
        return instance


class DataItemSerializer(DynamicModelSerializer):
    """Data items are created by the discovery of their connection, the API only reads and removes them"""

    connection = serializers.PrimaryKeyRelatedField(source="auth_config", read_only=True)
    capabilities = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = DataItem
        name = "data_item"
        fields = (
            "id",
            "source_provider",
            "uri",
            "title",
            "details",
            "connection",
            "is_available",
            "capabilities",
            "last_seen",
            "created_by",
            "created",
            "updated",
        )
        read_only_fields = fields

    def get_capabilities(self, obj):
        # every item of a provider has its declared capabilities, an uninstalled provider reads nothing
        _provider = source_provider_registry.get(obj.source_provider)
        return capability_names(_provider.declared_capabilities) if _provider else []
