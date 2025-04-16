#########################################################################
#
# Copyright (C) 2025 OSGeo
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
from django.conf import settings
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from geonode.base.models import ResourceBase
from geonode.base.api.filters import DynamicSearchFilter
from geonode.groups.models import GroupProfile, GroupMember
from geonode.base.api.permissions import IsOwnerOrAdmin
from geonode.base.api.serializers import GroupProfileSerializer, ResourceBaseSerializer
from geonode.base.api.pagination import GeoNodeApiPagination
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from geonode.security.utils import get_visible_resources
from guardian.shortcuts import get_objects_for_user
from rest_framework.exceptions import PermissionDenied
from geonode.people.utils import check_user_deletion_rules
from geonode.people.api.serializers import UserSerializer
from geonode.people.utils import get_available_users
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from geonode.resource.manager import resource_manager
from geonode.security.registry import permissions_registry


logger = logging.getLogger()


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    http_method_names = ["get", "post", "patch", "delete"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrAdmin,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filters and sorts users.
        """
        if self.request and self.request.user:
            queryset = get_available_users(self.request.user)
        else:
            queryset = get_user_model().objects.all()

        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset.order_by("username")

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            raise PermissionDenied()
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return instance

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("User deleted sucessfully", status=200)

    def perform_destroy(self, instance):
        deletable, errors = check_user_deletion_rules(instance)
        if not deletable:
            raise PermissionDenied(f"One or more validation rules are violated: {errors}")
        instance.delete()

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the Resources visible to the user.",
    )
    @action(detail=True, methods=["get"])
    def resources(self, request, pk=None):
        user = self.get_object()
        permitted = get_objects_for_user(user, "base.view_resourcebase")
        qs = ResourceBase.objects.all().filter(id__in=permitted).order_by("title")

        resources = get_visible_resources(
            qs,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )

        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True, context={"request": request})
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(
        methods=["get"],
        responses={200: GroupProfileSerializer(many=True)},
        description="API endpoint allowing to retrieve the Groups the user is member of.",
    )
    @action(detail=True, methods=["get"])
    def groups(self, request, pk=None):
        user = self.get_object()
        qs_ids = GroupMember.objects.filter(user=user).values_list("group", flat=True)
        groups = GroupProfile.objects.filter(id__in=qs_ids)
        return Response(GroupProfileSerializer(embed=True, many=True).to_representation(groups))

    @action(detail=True, methods=["post"])
    def remove_from_group_manager(self, request, pk=None):
        user = self.get_object()
        target_ids = request.data.get("groups", [])
        user_groups = []
        invalid_groups = []

        if not target_ids:
            return Response({"error": "No groups IDs were provided"}, status=400)

        if target_ids == "ALL":
            user_groups = GroupProfile.groups_for_user(user)
        else:
            target_ids = set(target_ids)
            user_groups = GroupProfile.groups_for_user(user).filter(group_id__in=target_ids)
            # check for groups that user is not part of:
            invalid_groups.extend(target_ids - set(ug.group_id for ug in user_groups))

        for group in user_groups:
            group.demote(user)
        group_names = [group.title for group in user_groups]

        payload = {"success": f"User removed as a group manager from : {', '.join(group_names)}"}

        if invalid_groups:
            payload["error"] = f"User is not manager of the following groups: : {invalid_groups}"
            return Response(payload, status=400)
        return Response(payload, status=200)

    @action(detail=True, methods=["post"])
    def transfer_resources(self, request, pk=None):
        user = self.get_object()
        admin = get_user_model().objects.filter(is_superuser=True, is_staff=True).first()
        target_user = request.data.get("newOwner")  # the new owner
        previous_owner = request.data.get("currentOwner")  # the previous owner, usually it match the user
        transfer_resource_subset = (
            request.data.get("resources", None)
            if not hasattr(request.data, "getlist")
            else request.data.getlist("resources", None)
        )
        target = None

        if not target_user and previous_owner:
            return Response("Payload not passed", status=400)

        if user.is_superuser or (
            not user.is_superuser
            and ResourceBase.objects.filter(owner=user, pk__in=transfer_resource_subset).count()
            == len(transfer_resource_subset)
        ):

            if target_user == "DEFAULT":
                if not admin:
                    return Response("Principal User not found", status=500)
                target = admin
            else:
                target = get_object_or_404(get_user_model(), id=target_user)

            if target == user:
                return Response("Cannot reassign to self", status=400)

            # we need to filter by the previous owner id
            filter_payload = dict(owner=previous_owner or user)

            if transfer_resource_subset:
                # transfer_resources
                filter_payload["pk__in"] = transfer_resource_subset

            for instance in ResourceBase.objects.filter(**filter_payload).iterator():
                """
                We should reassing all the permissions to the new resource owner
                we can use the resource manager because inside it will automatically update
                the owner
                """
                try:
                    # putting the resource in dirty state
                    instance.set_dirty_state()
                    # updating the perms with the new owner
                    perms = permissions_registry.get_perms(instance=instance, include_virtual=False)
                    prev_owner = get_user_model().objects.filter(pk=previous_owner).first()

                    if prev_owner and not prev_owner.is_superuser:
                        perms["users"].pop(prev_owner)
                    # calling the registry to update the perms
                    resource_manager.set_permissions(instance.uuid, instance, owner=target or user, permissions=perms)
                except Exception as e:
                    logger.exeption(e)
                finally:
                    # clearing the dirty state
                    instance.clear_dirty_state()

            return Response("Resources transfered successfully", status=200)

        return Response(
            {"error": "The user does not have any right to perform this action on this resource"}, status=403
        )
