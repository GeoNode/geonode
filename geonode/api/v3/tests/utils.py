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
from django.contrib.auth.models import Group
from django.db.models import Count
from rest_framework import mixins, serializers
from rest_framework.permissions import AllowAny

from geonode.api.v3.serializers import FieldSelectionModelSerializer
from geonode.api.v3.viewsets import V3GenericViewSet, V3ModelViewSet

GROUP_PREFIX = "v3-test-"


class GroupSerializer(FieldSelectionModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")
        default_fields = ("id",)


class NestingSerializer(FieldSelectionModelSerializer):
    nested = GroupSerializer(source="*", read_only=True)
    nested_list = GroupSerializer(source="related_groups", many=True, read_only=True)

    class Meta:
        model = Group
        fields = ("id", "name", "nested", "nested_list")


class CountingGroupSerializer(FieldSelectionModelSerializer):
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ("id", "name", "user_count")
        default_fields = ("id", "user_count")

    @classmethod
    def setup_queryset(cls, queryset, fields, request):
        if "user_count" in fields:
            queryset = queryset.annotate(user_count=Count("user"))
        return queryset


class GroupViewSet(V3ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CountingGroupSerializer

    def get_base_queryset(self):
        return Group.objects.filter(name__startswith=GROUP_PREFIX).order_by("id")


class PlainGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")


class PlainGroupViewSet(GroupViewSet):
    serializer_class = PlainGroupSerializer


class ReadOnlyGroupViewSet(mixins.ListModelMixin, V3GenericViewSet):
    serializer_class = CountingGroupSerializer

    def get_base_queryset(self):
        return Group.objects.filter(name__startswith=GROUP_PREFIX).order_by("id")
