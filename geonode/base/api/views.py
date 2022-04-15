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
import ast
import json

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Subquery

from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet, WithDynamicViewSetMixin
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from geonode.favorite.models import Favorite
from geonode.thumbs.exceptions import ThumbnailError
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.base.models import ExtraMetadata, HierarchicalKeyword, Region, ResourceBase, TopicCategory, ThesaurusKeyword
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, FavoriteFilter
from geonode.groups.models import GroupProfile, GroupMember
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.security.utils import (
    get_geoapp_subtypes,
    get_visible_resources,
    get_user_visible_groups,
    get_resources_with_perms)

from guardian.shortcuts import get_objects_for_user

from .permissions import (
    IsSelfOrAdminOrReadOnly,
    IsOwnerOrAdmin,
    IsOwnerOrReadOnly,
    IsManagerEditOrAdmin,
    ResourceBasePermissionsFilter
)
from .serializers import (
    FavoriteSerializer,
    UserSerializer,
    PermSpecSerialiazer,
    GroupProfileSerializer,
    ResourceBaseSerializer,
    ResourceBaseTypesSerializer,
    OwnerSerializer,
    HierarchicalKeywordSerializer,
    TopicCategorySerializer,
    RegionSerializer,
    ThesaurusKeywordSerializer,
    ExtraMetadataSerializer
)
from .pagination import GeoNodeApiPagination
from geonode.base.utils import validate_extra_metadata

import logging

logger = logging.getLogger(__name__)


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filters and sorts users.
        """
        queryset = get_user_model().objects.all()
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset.order_by("username")

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Resources visible to the user.")
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

    @extend_schema(methods=['get'], responses={200: GroupProfileSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Groups the user is member of.")
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
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsManagerEditOrAdmin, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    serializer_class = GroupProfileSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filters the public groups and private ones the current user is member of.
        """
        metadata_author_groups = get_user_visible_groups(
            self.request.user, include_public_invite=True)
        if not isinstance(metadata_author_groups, list):
            metadata_author_groups = list(metadata_author_groups.all())
        queryset = GroupProfile.objects.filter(id__in=[_g.id for _g in metadata_author_groups])
        return queryset.order_by("title")

    @extend_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group members.")
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        members = get_user_model().objects.filter(id__in=group.member_queryset().values_list("user", flat=True))
        return Response(UserSerializer(embed=True, many=True).to_representation(members))

    @extend_schema(methods=['get'], responses={200: UserSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group managers.")
    @action(detail=True, methods=['get'])
    def managers(self, request, pk=None):
        group = self.get_object()
        managers = group.get_managers()
        return Response(UserSerializer(embed=True, many=True).to_representation(managers))

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the Group specific resources.")
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        group = self.get_object()
        resources = group.resources()
        return Response(ResourceBaseSerializer(embed=True, many=True).to_representation(resources))


class RegionViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists regions.
    """
    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    pagination_class = GeoNodeApiPagination


class HierarchicalKeywordViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists hierarchical keywords.
    """

    def get_queryset(self):
        resource_keywords = HierarchicalKeyword.resource_keywords_tree(self.request.user)

        def _get_kw_hrefs(keywords, slugs: list = []):
            for obj in keywords:
                if obj.get('tags', []):
                    slugs.append(obj.get('href'))
                _get_kw_hrefs(obj.get('nodes', []), slugs)
            return slugs

        slugs = _get_kw_hrefs(resource_keywords)
        return HierarchicalKeyword.objects.filter(slug__in=slugs)

    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    serializer_class = HierarchicalKeywordSerializer
    pagination_class = GeoNodeApiPagination


class ThesaurusKeywordViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists Thesaurus keywords.
    """
    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    queryset = ThesaurusKeyword.objects.all()
    serializer_class = ThesaurusKeywordSerializer
    pagination_class = GeoNodeApiPagination


class TopicCategoryViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists categories.
    """
    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    queryset = TopicCategory.objects.all()
    serializer_class = TopicCategorySerializer
    pagination_class = GeoNodeApiPagination


class OwnerViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists all possible owners.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    serializer_class = OwnerSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filter users with at least one resource
        """
        queryset = get_user_model().objects.exclude(pk=-1)
        filter_options = {}
        if self.request.query_params:
            filter_options = {
                'type_filter': self.request.query_params.get('type'),
                'title_filter': self.request.query_params.get('title__icontains')
            }
        queryset = queryset.filter(id__in=Subquery(
            get_resources_with_perms(self.request.user, filter_options).values('owner'))
        )
        return queryset.order_by("username")


class ResourceBaseViewSet(DynamicModelViewSet):
    """
    API endpoint that allows base resources to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, ResourceBasePermissionsFilter, FavoriteFilter
    ]
    queryset = ResourceBase.objects.all().order_by('-last_updated')
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination

    def _filtered(self, request, filter):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        resources = get_resources_with_perms(request.user).filter(**filter)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the approved Resources.")
    @action(detail=False, methods=['get'])
    def approved(self, request):
        return self._filtered(request, {"is_approved": True})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the published Resources.")
    @action(detail=False, methods=['get'])
    def published(self, request):
        return self._filtered(request, {"is_published": True})

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the featured Resources.")
    @action(detail=False, methods=['get'])
    def featured(self, request):
        return self._filtered(request, {"featured": True})

    @extend_schema(methods=['get'], responses={200: FavoriteSerializer(many=True)},
                   description="API endpoint allowing to retrieve the favorite Resources.")
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, ])
    def favorites(self, request, pk=None):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        favorites = Favorite.objects.favorites_for_user(user=request.user)
        result_page = paginator.paginate_queryset(favorites, request)
        serializer = FavoriteSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"favorites": serializer.data})

    @extend_schema(methods=['post', 'delete'], responses={200: FavoriteSerializer(many=True)},
                   description="API endpoint allowing to retrieve the favorite Resources.")
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk=None):
        resource = self.get_object()
        user = request.user

        if request.method == 'POST':
            try:
                Favorite.objects.get(user=user, object_id=resource.pk)
                return Response({"message": "Resource is already in favorites"}, status=400)
            except Favorite.DoesNotExist:
                Favorite.objects.create_favorite(resource, user)
                return Response({"message": "Successfuly added resource to favorites"}, status=201)

        if request.method == 'DELETE':
            try:
                Favorite.objects.get(user=user, object_id=resource.pk).delete()
                return Response({"message": "Successfuly removed resource from favorites"}, status=200)
            except Favorite.DoesNotExist:
                return Response({"message": "Resource not in favorites"}, status=404)

    @extend_schema(methods=['get'], responses={200: ResourceBaseTypesSerializer()},
                   description="""
        Returns the list of available ResourceBase polymorphic_ctypes.

        the mapping looks like:
        ```
        {
            "resource_types":[
                {
                    "name": "layer",
                    "count": <number of layers>
                },
                {
                    "name": "map",
                    "count": <number of maps>
                },
                {
                    "name": "document",
                    "count": <number of documents>
                },
                {
                    "name": "geostory",
                    "count": <number of geostories>
                }
            ]
        }
        ```
        """)
    @action(detail=False, methods=['get'])
    def resource_types(self, request):
        resource_types = []
        _types = []
        for _model in apps.get_models():
            if _model.__name__ == "ResourceBase":
                for _m in _model.__subclasses__():
                    if _m.__name__.lower() not in ['geoapp', 'service']:
                        _types.append(_m.__name__.lower())

        if settings.GEONODE_APPS_ENABLE:
            _types.extend(get_geoapp_subtypes())

        for _type in _types:
            resource_types.append({
                "name": _type,
                "count": get_resources_with_perms(request.user).filter(resource_type=_type).count()
            })
        return Response({"resource_types": resource_types})

    @extend_schema(methods=['get', 'put', 'patch', 'delete'],
                   request=PermSpecSerialiazer(),
                   responses={200: None},
                   description="""
        Sets an object's the permission levels based on the perm_spec JSON.

        the mapping looks like:
        ```
        {
            'users': {
                'AnonymousUser': ['view'],
                <username>: ['perm1','perm2','perm3'],
                <username2>: ['perm1','perm2','perm3']
                ...
            },
            'groups': {
                <groupname>: ['perm1','perm2','perm3'],
                <groupname2>: ['perm1','perm2','perm3'],
                ...
            }
        }
        ```
        """)
    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrAdmin, ])
    def get_perms(self, request, pk=None):
        resource = self.get_object()
        perms_spec = resource.get_all_level_info()
        perms_spec_obj = {}
        if "users" in perms_spec:
            perms_spec_obj["users"] = {}
            for user in perms_spec["users"]:
                perms = perms_spec["users"].get(user)
                perms_spec_obj["users"][str(user)] = perms
        if "groups" in perms_spec:
            perms_spec_obj["groups"] = {}
            for group in perms_spec["groups"]:
                perms = perms_spec["groups"].get(group)
                perms_spec_obj["groups"][str(group)] = perms
        return Response(perms_spec_obj)

    @extend_schema(methods=['put'],
                   request=PermSpecSerialiazer(),
                   responses={200: None},
                   description="""
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
    @action(detail=True, methods=['put'], permission_classes=[IsOwnerOrAdmin, ])
    def set_perms(self, request, pk=None):
        resource = self.get_object()
        resource.set_permissions(request.data)
        return Response(request.data)

    @extend_schema(
        methods=["post"], responses={200}, description="API endpoint allowing to set the thumbnail url for an existing dataset."
    )
    @action(
        detail=False,
        url_path=r"(?P<resource_id>\d+)/set_thumbnail_from_bbox",  # noqa
        url_name="set-thumb-from-bbox",
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
        ])
    def set_thumbnail_from_bbox(self, request, resource_id):
        import traceback
        from django.utils.datastructures import MultiValueDictKeyError
        try:
            resource = ResourceBase.objects.get(id=ast.literal_eval(resource_id))

            if not isinstance(resource.get_real_instance(), (Layer, Map)):
                raise NotImplementedError("Not implemented: Endpoint available only for Dataset and Maps")

            request_body = request.data if request.data else json.loads(request.body)
            try:
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)
            except MultiValueDictKeyError:
                for _k, _v in request_body.items():
                    request_body = json.loads(_k)
                    break
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)

            thumbnail_url = create_thumbnail(resource.get_real_instance(), bbox=bbox, background_zoom=zoom, overwrite=True)
            return Response({"message": "Thumbnail correctly created.", "success": True, "thumbnail_url": thumbnail_url}, status=200)
        except ResourceBase.DoesNotExist:
            traceback.print_exc()
            logger.error(f"Resource selected with id {resource_id} does not exists")
            return Response(
                data={"message": f"Resource selected with id {resource_id} does not exists", "success": False}, status=404, exception=True)
        except NotImplementedError as e:
            traceback.print_exc()
            logger.error(e)
            return Response(data={"message": e.args[0], "success": False}, status=405, exception=True)
        except ThumbnailError as e:
            traceback.print_exc()
            logger.error(e)
            return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)
        except Exception as e:
            traceback.print_exc()
            logger.error(e)
            return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)

    @extend_schema(
        methods=["get", "put", "delete", "post"], description="Get/Update/Delete/Add extra metadata for resource"
    )
    @action(
        detail=True,
        methods=["get", "put", "delete", "post"],
        permission_classes=[
            IsOwnerOrAdmin,
        ],
        url_path=r"extra_metadata",  # noqa
        url_name="extra-metadata",
    )
    def extra_metadata(self, request, pk=None):
        _obj = self.get_object()
        if request.method == "GET":
            # get list of available metadata
            queryset = _obj.metadata.all()
            _filters = [{f"metadata__{key}": value} for key, value in request.query_params.items()]
            if _filters:
                queryset = queryset.filter(**_filters[0])
            return Response(ExtraMetadataSerializer().to_representation(queryset))
        if not request.method == "DELETE":
            try:
                extra_metadata = validate_extra_metadata(request.data, _obj)
            except Exception as e:
                return Response(status=500, data=e.args[0])

        if request.method == "PUT":
            '''
            update specific metadata. The ID of the metadata is required to perform the update
            [
                {
                        "id": 1,
                        "name": "foo_name",
                        "slug": "foo_sug",
                        "help_text": "object",
                        "field_type": "int",
                        "value": "object",
                        "category": "object"
                }
            ]
            '''
            for _m in extra_metadata:
                _id = _m.pop('id')
                ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id=_id).update(metadata=_m)
            logger.info("metadata updated for the selected resource")
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "DELETE":
            # delete single metadata
            '''
            Expect a payload with the IDs of the metadata that should be deleted. Payload be like:
            [4, 3]
            '''
            ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id__in=request.data).delete()
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "POST":
            # add new metadata
            '''
            [
                {
                        "name": "foo_name",
                        "slug": "foo_sug",
                        "help_text": "object",
                        "field_type": "int",
                        "value": "object",
                        "category": "object"
                }
            ]
            '''
            for _m in extra_metadata:
                new_m = ExtraMetadata.objects.create(
                    resource=_obj,
                    metadata=_m
                )
                new_m.save()
                _obj.metadata.add(new_m)
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()), status=201)
