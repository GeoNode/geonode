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
import re

from decimal import Decimal
from uuid import uuid1
from urllib.parse import urljoin, urlparse
from PIL import Image

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.db import models
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.db.models import Subquery
from django.http.request import QueryDict
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet, WithDynamicViewSetMixin
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from pinax.ratings.categories import category_value
from pinax.ratings.models import OverallRating, Rating
from pinax.ratings.views import NUM_OF_RATINGS

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.favorite.models import Favorite
from geonode.base.models import Configuration
from geonode.thumbs.exceptions import ThumbnailError
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.thumbs.utils import _decode_base64, BASE64_PATTERN
from geonode.groups.conf import settings as groups_settings
from geonode.base.models import HierarchicalKeyword, Region, ResourceBase, TopicCategory, ThesaurusKeyword
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, FavoriteFilter
from geonode.groups.models import GroupProfile, GroupMember
from geonode.security.permissions import (
    PermSpec,
    PermSpecCompact,
    get_compact_perms_list)
from geonode.security.utils import (
    get_visible_resources,
    get_resources_with_perms,
    get_user_visible_groups)

from geonode.resource.models import ExecutionRequest
from geonode.resource.api.tasks import resouce_service_dispatcher
from geonode.resource.manager import resource_manager

from guardian.shortcuts import get_objects_for_user

from .permissions import (
    IsSelfOrAdminOrReadOnly,
    IsOwnerOrAdmin,
    IsOwnerOrReadOnly,
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
)
from .pagination import GeoNodeApiPagination

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
    permission_classes = [IsAuthenticatedOrReadOnly, ]
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
    permission_classes = [AllowAny, ]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    queryset = HierarchicalKeyword.objects.all()
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
    queryset = ResourceBase.objects.all().order_by('-date')
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

        def _to_compact_perms_list(allowed_perms: dict, resource_type: str, resource_subtype: str) -> list:
            _compact_perms_list = {}
            for _k, _v in allowed_perms.items():
                _is_owner = _k not in ["anonymous", groups_settings.REGISTERED_MEMBERS_GROUP_NAME]
                _is_none_allowed = not _is_owner
                _compact_perms_list[_k] = get_compact_perms_list(_v, resource_type, resource_subtype, _is_owner, _is_none_allowed)
            return _compact_perms_list

        resource_types = []
        _types = []
        _allowed_perms = {}
        for _model in apps.get_models():
            if _model.__name__ == "ResourceBase":
                for _m in _model.__subclasses__():
                    if _m.__name__.lower() not in ['service']:
                        _types.append(_m.__name__.lower())
                        _allowed_perms[_m.__name__.lower()] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(_m.allowed_permissions, _m.__name__.lower(), _m.__name__.lower())
                        }

        if settings.GEONODE_APPS_ENABLE and 'geoapp' in _types:
            _types.remove('geoapp')
            if hasattr(settings, 'CLIENT_APP_LIST') and settings.CLIENT_APP_LIST:
                _types += settings.CLIENT_APP_LIST
            else:
                from geonode.geoapps.models import GeoApp
                geoapp_types = [x for x in GeoApp.objects.values_list('resource_type', flat=True).all().distinct()]
                _types += geoapp_types

            if hasattr(settings, 'CLIENT_APP_ALLOWED_PERMS') and settings.CLIENT_APP_ALLOWED_PERMS:
                for _type in settings.CLIENT_APP_ALLOWED_PERMS:
                    for _type_name, _type_perms in _type.items():
                        _allowed_perms[_type_name] = {
                            "perms": _type_perms,
                            "compact": _to_compact_perms_list(_type_perms, _type_name, _type_name)
                        }
            else:
                from geonode.geoapps.models import GeoApp
                for _m in GeoApp.objects.filter(resource_type__in=_types).iterator():
                    if hasattr(_m, 'resource_type') and _m.resource_type and _m.resource_type not in _allowed_perms:
                        _allowed_perms[_m.resource_type] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(_m.allowed_permissions, _m.resource_type, _m.subtype)
                        }

        for _type in _types:
            resource_types.append({
                "name": _type,
                "count": get_resources_with_perms(request.user).filter(resource_type=_type).count(),
                "allowed_perms": _allowed_perms[_type] if _type in _allowed_perms else []
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
    @action(
        detail=True,
        url_path="permissions",  # noqa
        url_name="perms-spec",
        methods=['get', 'put', 'patch', 'delete'],
        permission_classes=[
            IsOwnerOrAdmin,
        ])
    def resource_service_permissions(self, request, pk=None):
        """Instructs the Async dispatcher to execute a 'DELETE' or 'UPDATE' on the permissions of a valid 'uuid'

        - GET input_params: {
            id: "<str: ID>"
        }

        - DELETE input_params: {
            id: "<str: ID>"
        }

        - PUT input_params: {
            id: "<str: ID>"
            owner: str = None
            permissions: dict = {}
            created: bool = False
        }

        - output_params: {
            output: {
                uuid: "<str: UUID>"
            }
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Requests:
        - Removes all the permissions (except owner and admin ones) from a Resource:
        curl -v -X DELETE -u admin:admin -H "Content-Type: application/json" http://localhost:8000/api/v2/resources/<id>/permissions

        - Changes the owner of a Resource:
        curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'owner=afabiani' http://localhost:8000/api/v2/resources/<id>/permissions

        - Assigns View permissions to some users:
        curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'permissions={"users": {"admin": ["view_resourcebase"]}, "groups": {}}'
            http://localhost:8000/api/v2/resources/<id>/permissions

        curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'owner=afabiani' -d 'permissions={"users": {"admin": ["view_resourcebase"]}, "groups": {}}'
            http://localhost:8000/api/v2/resources/<id>/permissions

        - Assigns View permissions to anyone:
        curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'permissions={"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": []}'
            http://localhost:8000/api/v2/resources/<id>/permissions

        - Assigns View permissions to anyone and edit (style and data) permissions to a Group on a Dataset:
        curl -v -X PUT -u admin:admin -H "Content-Type: application/json"
            -d 'permissions={"users": {"AnonymousUser": ["view_resourcebase"]},
            "groups": {"registered-members": ["view_resourcebase", "download_resourcebase", "change_dataset_style", "change_dataset_data"]}}'
            http://localhost:8000/api/v2/resources/<id>/permissions

        - Assigns View permissions to anyone and edit permissions to a Group on a Document:
        curl -v -X PUT -u admin:admin -H "Content-Type: application/json"
            -d 'permissions={"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": {"registered-members": ["view_resourcebase", "download_resourcebase", "change_resourcebase"]}}'
            http://localhost:8000/api/v2/resources/<id>/permissions
        """
        config = Configuration.load()
        resource = self.get_object()
        _user_can_manage = request.user.has_perm('change_resourcebase', resource.get_self_resource()) or request.user.has_perm('change_resourcebase_permissions', resource.get_self_resource())
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
                resource is None or not _user_can_manage:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            perms_spec = PermSpec(resource.get_all_level_info(), resource)
            request_body = request.body
            request_params = QueryDict(request_body, mutable=True, encoding="UTF-8")
            if request.method == 'GET':
                return Response(perms_spec.compact)
            elif request.method == 'DELETE':
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='remove_permissions',
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid)
                    }
                )
            elif request.method == 'PUT':
                perms_spec_compact = PermSpecCompact(
                    json.loads(request_params.get('permissions', '{}')), resource)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='set_permissions',
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid),
                        "owner": request_params.get('owner', resource.owner.username),
                        "permissions": perms_spec_compact.extended,
                        "created": request_params.get('created', False)
                    }
                )
            elif request.method == 'PATCH':
                perms_spec_compact_patch = PermSpecCompact(
                    json.loads(request_params.get('permissions', '{}')), resource)
                perms_spec_compact_resource = PermSpecCompact(perms_spec.compact, resource)
                perms_spec_compact_resource.merge(perms_spec_compact_patch)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name='set_permissions',
                    input_params={
                        "uuid": request_params.get('uuid', resource.uuid),
                        "owner": request_params.get('owner', resource.owner.username),
                        "permissions": perms_spec_compact_resource.extended,
                        "created": request_params.get('created', False)
                    }
                )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["post"], responses={200}, description="API endpoint allowing to set the thumbnail url for an existing dataset."
    )
    @action(
        detail=False,
        url_path="(?P<resource_id>\d+)/set_thumbnail_from_bbox",  # noqa
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

            if not isinstance(resource.get_real_instance(), (Dataset, Map)):
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
        methods=["post"], responses={200}, description="Instructs the Async dispatcher to execute a 'INGEST' operation."
    )
    @action(
        detail=False,
        url_path="ingest/(?P<resource_type>\w+)",  # noqa
        url_name="resource-service-ingest",
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
        ])
    def resource_service_ingest(self, request, resource_type: str = None):
        """Instructs the Async dispatcher to execute a 'INGEST' operation

        - POST input_params: {
            uuid: "<str: UUID>",
            files: "<list(str) path>",
            defaults: "{\"owner\":\"<str: username>\",<list: str>}",  # WARNING: 'owner' is mandatory
            resource_type: "<enum: ['dataset', 'document', 'map', '<GeoApp: name>']>"
        }

        - output_params: {
            output: <int: number of resources deleted / 0 if none>
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Request:

        1. curl -v -X POST -u admin:admin -H "Content-Type: application/json" -d 'defaults={"owner":"admin","title":"pippo"}' -d 'files=["/mnt/c/Data/flowers.jpg"]'
            http://localhost:8000/api/v2/resources/ingest/document
            OUTPUT: {
                "status": "ready",
                "execution_id": "90ca670d-df60-44b6-b358-d792c6aecc58",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58"
            }

        2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58
            OUTPUT: {
                "user": "admin",
                "status": "finished",
                "func_name": "create",
                "created": "2021-07-22T15:32:09.096075Z",
                "finished": "2021-07-22T15:32:26.936683Z",
                "last_updated": "2021-07-22T15:32:09.096129Z",
                "input_params": {
                    "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb",
                    "files": "[\"/mnt/c/Data/flowers.jpg\"]",
                    "defaults": "{\"owner\":\"admin\",\"title\":\"pippo\"}",
                    "resource_type": "dataset"
                },
                "output_params": {
                    "output": {
                        "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb"
                    }
                }
            }
        """
        config = Configuration.load()
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated \
                or not request.user.has_perm('base.add_resourcebase'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = QueryDict(request.body, mutable=True)
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name='ingest',
                input_params={
                    "uuid": request_params.get('uuid', str(uuid1())),
                    "files": request_params.get('files', '[]'),
                    "resource_type": resource_type,
                    "defaults": request_params.get('defaults', f"{{\"owner\":\"{request.user.username}\"}}")
                }
            )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["post"], responses={200}, description="Instructs the Async dispatcher to execute a 'CREATE' operation."
    )
    @action(
        detail=False,
        url_path="create/(?P<resource_type>\w+)",  # noqa
        url_name="resource-service-create",
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
        ])
    def resource_service_create(self, request, resource_type: str = None):
        """Instructs the Async dispatcher to execute a 'CREATE' operation
        **WARNING**: This will create an empty dataset; if you need to upload a resource to GeoNode, consider using the endpoint "ingest" instead

        - POST input_params: {
            uuid: "<str: UUID>",
            defaults: "{\"owner\":\"<str: username>\",<list: str>}",  # WARNING: 'owner' is mandatory
            resource_type: "<enum: ['dataset', 'document', 'map', '<GeoApp: name>']>"
        }

        - output_params: {
            output: <int: number of resources deleted / 0 if none>
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Request:

        1. curl -v -X POST -u admin:admin -H "Content-Type: application/json" -d 'defaults={"owner":"admin","title":"pippo"}'
            http://localhost:8000/api/v2/resources/create/dataset
            OUTPUT: {
                "status": "ready",
                "execution_id": "90ca670d-df60-44b6-b358-d792c6aecc58",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58"
            }

        2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58
            OUTPUT: {
                "user": "admin",
                "status": "finished",
                "func_name": "create",
                "created": "2021-07-22T15:32:09.096075Z",
                "finished": "2021-07-22T15:32:26.936683Z",
                "last_updated": "2021-07-22T15:32:09.096129Z",
                "input_params": {
                    "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb",
                    "defaults": "{\"owner\":\"admin\",\"title\":\"pippo\"}",
                    "resource_type": "dataset"
                },
                "output_params": {
                    "output": {
                        "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb"
                    }
                }
            }
        """
        config = Configuration.load()
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated \
                or not request.user.has_perm('base.add_resourcebase'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = QueryDict(request.body, mutable=True)
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name='create',
                input_params={
                    "uuid": request_params.get('uuid', str(uuid1())),
                    "resource_type": resource_type,
                    "defaults": request_params.get('defaults', f"{{\"owner\":\"{request.user.username}\"}}")
                }
            )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["delete"], responses={200}, description="Instructs the Async dispatcher to execute a 'DELETE' operation over a valid 'uuid'."
    )
    @action(
        detail=True,
        url_path="delete",  # noqa
        url_name="resource-service-delete",
        methods=["delete"],
        permission_classes=[
            IsAuthenticated,
        ])
    def resource_service_delete(self, request, pk=None):
        """Instructs the Async dispatcher to execute a 'DELETE' operation over a valid 'uuid'

        - DELETE input_params: {
            id: "<str: ID>"
        }

        - output_params: {
            output: <int: number of resources deleted / 0 if none>
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample request:

        1. curl -v -X DELETE -u admin:admin http://localhost:8000/api/v2/resources/<id>/delete
            OUTPUT: {
                "status":"ready",
                "execution_id":"7ed0b141-cf85-434f-bbfb-c02447a5221b",
                "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/7ed0b141-cf85-434f-bbfb-c02447a5221b"
            }

        2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/7ed0b141-cf85-434f-bbfb-c02447a5221b
            OUTPUT: {
                "user":"admin",
                "status":"finished",
                "func_name":"delete",
                "created":"2021-07-19T14:09:59.930619Z",
                "finished":"2021-07-19T14:10:00.054915Z",
                "last_updated":"2021-07-19T14:09:59.930647Z",
                "input_params":{"uuid":"1234"},
                "output_params":{"output":0}
            }
        """
        config = Configuration.load()
        resource = self.get_object()
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
                resource is None or not request.user.has_perm('delete_resourcebase', resource.get_self_resource()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name='delete',
                input_params={
                    "uuid": resource.uuid
                }
            )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["put"], responses={200}, description="Instructs the Async dispatcher to execute a 'UPDATE' operation over a valid 'uuid'."
    )
    @action(
        detail=True,
        url_path="update",  # noqa
        url_name="resource-service-update",
        methods=["put"],
        permission_classes=[
            IsAuthenticated,
        ])
    def resource_service_update(self, request, pk=None):
        """Instructs the Async dispatcher to execute a 'UPDATE' operation over a valid 'uuid'

        - PUT input_params: {
            id: "<str: ID>"
            xml_file: str = None
            metadata_uploaded: bool = False
            vals: dict = {}
            regions: list = []
            keywords: list = []
            custom: dict = {}
            notify: bool = True
        }

        - output_params: {
            output: {
                uuid: "<str: UUID>"
            }
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Request:

        1. curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'vals={"title":"pippo"}' http://localhost:8000/api/v2/resources/<id>/update
            OUTPUT: {
                "status":"ready",
                "execution_id":"08846e84-eae4-11eb-84be-00155d41f2fb",
                "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb"
            }

        2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb
            OUTPUT: {
                "user": "admin",
                "status": "finished",
                "func_name": "update",
                "created": "2021-07-22T14:42:56.284740Z",
                "finished": "2021-07-22T14:43:01.813971Z",
                "last_updated": "2021-07-22T14:42:56.284797Z",
                "input_params": {
                    "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb",
                    "vals": "{\"title\":\"pippo\"}",
                    "custom": {},
                    "notify": true,
                    "regions": [],
                    "keywords": [],
                    "xml_file": null,
                    "metadata_uploaded": false
                },
                "output_params": {
                    "output": {
                        "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb"
                    }
                }
            }

        Sample Request with more parameters:

        1. curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'vals={"title":"pippo"}' -d 'metadata_uploaded=true' -d 'keywords=["k1", "k2", "k3"]'
            http://localhost:8000/api/v2/resources/<id>/update
        """
        config = Configuration.load()
        resource = self.get_object()
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
                resource is None or not request.user.has_perm('change_resourcebase', resource.get_self_resource()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = QueryDict(request.body, mutable=True)
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name='update',
                input_params={
                    "uuid": request_params.get('uuid', resource.uuid),
                    "xml_file": request_params.get('xml_file', None),
                    "metadata_uploaded": request_params.get('metadata_uploaded', False),
                    "vals": request_params.get('vals', '{}'),
                    "regions": request_params.get('regions', '[]'),
                    "keywords": request_params.get('keywords', '[]'),
                    "custom": request_params.get('custom', '{}'),
                    "notify": request_params.get('notify', True)
                }
            )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["put"], responses={200}, description="Instructs the Async dispatcher to execute a 'COPY' operation over a valid 'uuid'."
    )
    @action(
        detail=True,
        url_path="copy",  # noqa
        url_name="resource-service-copy",
        methods=["put"],
        permission_classes=[
            IsAuthenticated,
        ])
    def resource_service_copy(self, request, pk=None):
        """Instructs the Async dispatcher to execute a 'COPY' operation over a valid 'pk'

        - PUT input_params: {
            instance: "<str: ID>"
            owner: "<str: username = <current_user>>"
            defaults: dict = {}
        }

        - output_params: {
            output: {
                uuid: "<str: UUID>"
            }
        }

        - output: {
                "status": "ready",
                "execution_id": "<str: execution ID>",
                "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
            }

        Sample Request:

        1. curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'defaults={"title":"pippo"}' http://localhost:8000/api/v2/resources/<id>/copy
            OUTPUT: {
                "status":"ready",
                "execution_id":"08846e84-eae4-11eb-84be-00155d41f2fb",
                "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb"
            }

        2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb
            OUTPUT: {
                "user": "admin",
                "status": "finished",
                "func_name": "update",
                "created": "2021-07-22T14:42:56.284740Z",
                "finished": "2021-07-22T14:43:01.813971Z",
                "last_updated": "2021-07-22T14:42:56.284797Z",
                "input_params": {
                    "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb",
                    "defaults": "{\"title\":\"pippo\"}"
                },
                "output_params": {
                    "output": {
                        "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb"
                    }
                }
            }
        """
        config = Configuration.load()
        resource = self.get_object()
        if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
                resource is None or not request.user.has_perm('view_resourcebase', resource.get_self_resource()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = QueryDict(request.body, mutable=True)
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name='copy',
                input_params={
                    "instance": resource.id,
                    "owner": request_params.get('owner', request.user.username),
                    "defaults": request_params.get('defaults', '{}')
                }
            )
            resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
            return Response(
                {
                    'status': _exec_request.status,
                    'execution_id': _exec_request.exec_id,
                    'status_url':
                        urljoin(
                            settings.SITEURL,
                            reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                        )
                },
                status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=['post', 'get'],
        responses={200},
        description="API endpoint allowing to rate and get overall rating of the Resource.")
    @action(
        detail=True,
        url_path="ratings",
        url_name="ratings",
        methods=['post', 'get'],
        permission_classes=[
            IsAuthenticatedOrReadOnly,
        ])
    def ratings(self, request, pk=None):
        resource = self.get_object()
        resource = resource.get_real_instance()
        ct = ContentType.objects.get_for_model(resource)
        if request.method == 'POST':
            rating_input = int(request.data.get("rating"))
            category = resource._meta.object_name.lower()
            # check if category is configured in settings.PINAX_RATINGS_CATEGORY_CHOICES
            cat_choice = category_value(resource, category)

            # Check for errors and bail early
            if category and cat_choice is None:
                return HttpResponseForbidden(
                    "Invalid category. It must match a preconfigured setting"
                )
            if rating_input not in range(NUM_OF_RATINGS + 1):
                return HttpResponseForbidden(
                    "Invalid rating. It must be a value between 0 and {}".format(NUM_OF_RATINGS)
                )
            Rating.update(
                rating_object=resource,
                user=request.user,
                category=cat_choice,
                rating=rating_input
            )
        user_rating = None
        if request.user.is_authenticated:
            user_rating = Rating.objects.filter(
                object_id=resource.pk,
                content_type=ct,
                user=request.user
            ).first()
        overall_rating = OverallRating.objects.filter(
            object_id=resource.pk,
            content_type=ct
        ).aggregate(r=models.Avg("rating"))["r"]
        overall_rating = Decimal(str(overall_rating or "0"))

        return Response(
            {
                "rating": user_rating.rating if user_rating else 0,
                "overall_rating": overall_rating
            }
        )

    @extend_schema(
        methods=['put'],
        responses={200},
        description="API endpoint allowing to set thumbnail of the Resource.")
    @action(
        detail=True,
        url_path="set_thumbnail",
        url_name="set_thumbnail",
        methods=['put'],
        permission_classes=[
            IsAuthenticated,
        ],
        parser_classes=[JSONParser, MultiPartParser]
    )
    def set_thumbnail(self, request, pk=None):
        resource = get_object_or_404(ResourceBase, pk=pk)

        if not request.data.get('file'):
            raise ValidationError("Field file is required")

        file_data = request.data['file']

        if isinstance(file_data, str):
            if re.match(BASE64_PATTERN, file_data):
                try:
                    thumbnail, _thumbnail_format = _decode_base64(file_data)
                except Exception:
                    return Response(
                        'The request body is not a valid base64 string or the image format is not PNG or JPEG',
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                try:
                    # Check if file_data is a valid url and set it as thumbail_url
                    validate = URLValidator()
                    validate(file_data)
                    if urlparse(file_data).path.rsplit('.')[-1] not in ['png', 'jpeg', 'jpg']:
                        return Response(
                            'The url must be of an image with format (png, jpeg or jpg)',
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    resource.thumbnail_url = file_data
                    resource.save()
                    return Response({"thumbnail_url": resource.thumbnail_url})
                except Exception:
                    raise ValidationError('file is either a file upload, ASCII byte string or a valid image url string')
        else:
            # Validate size
            if file_data.size > 1000000:
                raise ValidationError('File must not exceed 1MB')

            thumbnail = file_data.read()
            try:
                file_data.seek(0)
                Image.open(file_data)
            except Exception:
                raise ValidationError('Invalid data provided')
        if thumbnail:
            resource_manager.set_thumbnail(resource.uuid, instance=resource, thumbnail=thumbnail)
            return Response({"thumbnail_url": resource.thumbnail_url})
        return Response(
            'Unable to set thumbnail',
            status=status.HTTP_400_BAD_REQUEST
        )
