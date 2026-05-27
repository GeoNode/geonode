#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from geonode.groups.models import GroupCategory, GroupProfile
from django.contrib.auth.models import Group
from django.db.models import Q
from .api import _get_resource_counts
from django.urls import reverse


class GroupCategorySerializer(DynamicModelSerializer):
    detail_url = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    resource_counts = serializers.SerializerMethodField()

    class Meta:
        model = GroupCategory
        fields = ["id", "slug", "name", "detail_url", "member_count", "resource_counts"]

    def get_detail_url(self, obj):
        return obj.get_absolute_url()

    def get_member_count(self, obj):
        request = self.context["request"]
        user = request.user
        filtered = obj.groups.all()

        if not user.is_authenticated:
            filtered = filtered.exclude(access="private")
        elif not user.is_superuser:
            category_ids = user.group_list_all().values("categories")
            filtered = filtered.filter(Q(id__in=category_ids) | ~Q(access="private"))

        return filtered.count()

    def get_resource_counts(self, obj):
        request = self.context["request"]
        return _get_resource_counts(
            request,
            resourcebase_filter_kwargs={"group__groupprofile__categories": obj},
        )


class GroupProfileSerializer(DynamicModelSerializer):
    categories = GroupCategorySerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    manager_count = serializers.SerializerMethodField()
    logo_url = serializers.CharField(read_only=True)
    detail_url = serializers.CharField(source="get_absolute_url", read_only=True)
    resource_uri = serializers.SerializerMethodField()

    class Meta:
        model = GroupProfile
        fields = [
            "id",
            "resource_uri",
            "title",
            "slug",
            "description",
            "email",
            "access",
            "created",
            "last_modified",
            "categories",
            "member_count",
            "manager_count",
            "logo_url",
            "detail_url",
        ]

    def get_resource_uri(self, obj):
        return reverse("group-profile-detail", args=[obj.pk])

    def get_member_count(self, obj):
        return obj.member_queryset().count()

    def get_manager_count(self, obj):
        return obj.get_managers().count()


class GroupSerializer(DynamicModelSerializer):
    group_profile = GroupProfileSerializer(source="groupprofile", read_only=True, allow_null=True)
    resource_counts = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "group_profile",
            "resource_counts",
        ]

    def get_resource_counts(self, obj):
        return _get_resource_counts(
            self.context["request"],
            resourcebase_filter_kwargs={"group": obj, "metadata_only": False},
        )
