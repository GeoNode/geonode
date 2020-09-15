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
from django.conf import settings
from django.contrib.auth import get_user_model

from drf_yasg.utils import swagger_auto_schema
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly  # noqa
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from geonode.base.models import ResourceBase
from geonode.base.api.filters import DynamicSearchFilter
from geonode.groups.models import GroupProfile, GroupMember
from geonode.security.utils import get_visible_resources

from guardian.shortcuts import get_objects_for_user

from .permissions import (
    IsOwnerOrReadOnly,
    ResourceBasePermissionsFilter
)
from .serializers import (
    UserSerializer,
    PermSpecSerialiazer,
    GroupProfileSerializer,
    ResourceBaseSerializer
)
from .pagination import GeoNodeApiPagination

import logging

logger = logging.getLogger(__name__)


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAdminUser,)
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = get_user_model().objects.all()
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset

    @swagger_auto_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                         operation_description="API endpoint allowing to retrieve the Resources visible to the user.")
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        user = self.get_object()
        permitted = get_objects_for_user(user, 'base.view_resourcebase')
        qs = ResourceBase.objects.all().filter(id__in=permitted).order_by('title')

        resources = get_visible_resources(
            qs,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
        return Response(ResourceBaseSerializer(embed=True, many=True).to_representation(resources))

    @swagger_auto_schema(methods=['get'], responses={200: GroupProfileSerializer(many=True)},
                         operation_description="API endpoint allowing to retrieve the Groups the user is member of.")
    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        user = self.get_object()
        qs_ids = GroupMember.objects.filter(user=user).values_list("group", flat=True)
        groups = GroupProfile.objects.filter(id__in=qs_ids)
        return Response(GroupProfileSerializer(embed=True, many=True).to_representation(groups))


class GroupViewSet(DynamicModelViewSet):
    """
    API endpoint that allows gropus to be viewed or edited.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAdminUser,)
    queryset = GroupProfile.objects.all()
    serializer_class = GroupProfileSerializer
    pagination_class = GeoNodeApiPagination

    @swagger_auto_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                         operation_description="API endpoint allowing to retrieve the Group members.")
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        members = get_user_model().objects.filter(id__in=group.member_queryset().values_list("user", flat=True))
        return Response(UserSerializer(embed=True, many=True).to_representation(members))

    @swagger_auto_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                         operation_description="API endpoint allowing to retrieve the Group managers.")
    @action(detail=True, methods=['get'])
    def managers(self, request, pk=None):
        group = self.get_object()
        managers = group.get_managers()
        return Response(UserSerializer(embed=True, many=True).to_representation(managers))

    @swagger_auto_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                         operation_description="API endpoint allowing to retrieve the Group specific resources.")
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        group = self.get_object()
        resources = group.resources()
        return Response(ResourceBaseSerializer(embed=True, many=True).to_representation(resources))


class ResourceBaseViewSet(DynamicModelViewSet):
    """
    API endpoint that allows base resources to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter, ResourceBasePermissionsFilter]
    queryset = ResourceBase.objects.all()
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination

    @swagger_auto_schema(methods=['get'], responses={200: PermSpecSerialiazer()},
                         operation_description="""
        Gets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': [
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            ],
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }
        ```
        """)
    @action(detail=True, methods=['get'])
    def get_perms(self, request, pk=None):
        resource = self.get_object()
        perms_spec = resource.get_all_level_info()
        for user in perms_spec["users"]:
            perms = perms_spec["users"].pop(user)
            perms_spec["users"][str(user)] = perms
        for group in perms_spec["groups"]:
            perms = perms_spec["groups"].pop(group)
            perms_spec["groups"][str(group)] = perms
        return Response(perms_spec)

    @swagger_auto_schema(methods=['put'],
                         request_body=PermSpecSerialiazer(),
                         responses={200: None},
                         operation_description="""
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': [
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            ],
            'groups': [
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            ]
        }
        ```
        """)
    @action(detail=True, methods=['put'])
    def set_perms(self, request, pk=None):
        resource = self.get_object()
        resource.set_permissions(request.data)
        return Response(request.data)
