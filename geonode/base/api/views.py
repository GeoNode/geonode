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
import functools
import json
import re

from uuid import uuid4
from urllib.parse import urljoin, urlparse
from PIL import Image

from django.apps import apps
from django.core.validators import URLValidator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.db.models import Subquery, QuerySet
from django.http.request import QueryDict
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet, WithDynamicViewSetMixin
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.favorite.models import Favorite
from geonode.base.models import Configuration, ExtraMetadata, LinkedResource
from geonode.thumbs.exceptions import ThumbnailError
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.thumbs.utils import _decode_base64, BASE64_PATTERN
from geonode.groups.conf import settings as groups_settings
from geonode.base.models import HierarchicalKeyword, Region, ResourceBase, TopicCategory, ThesaurusKeyword
from geonode.base.api.filters import (
    DynamicSearchFilter,
    ExtentFilter,
    FacetVisibleResourceFilter,
    FavoriteFilter,
    TKeywordsFilter,
)
from geonode.groups.models import GroupProfile
from geonode.security.permissions import get_compact_perms_list, PermSpec, PermSpecCompact
from geonode.security.utils import (
    get_visible_resources,
    get_resources_with_perms,
    get_user_visible_groups,
)

from geonode.resource.models import ExecutionRequest
from geonode.resource.api.tasks import resouce_service_dispatcher
from geonode.resource.manager import resource_manager


from geonode.base.api.mixins import AdvertisedListMixin
from .permissions import (
    IsOwnerOrAdmin,
    IsManagerEditOrAdmin,
    ResourceBasePermissionsFilter,
    UserHasPerms,
)

from .serializers import (
    FavoriteSerializer,
    PermSpecSerialiazer,
    GroupProfileSerializer,
    ResourceBaseSerializer,
    ResourceBaseTypesSerializer,
    OwnerSerializer,
    HierarchicalKeywordSerializer,
    TopicCategorySerializer,
    RegionSerializer,
    ThesaurusKeywordSerializer,
    ExtraMetadataSerializer,
    LinkedResourceSerializer,
)
from geonode.people.api.serializers import UserSerializer
from .pagination import GeoNodeApiPagination
from geonode.base.utils import validate_extra_metadata

import logging

logger = logging.getLogger(__name__)


class GroupViewSet(DynamicModelViewSet):
    """
    API endpoint that allows gropus to be viewed or edited.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsManagerEditOrAdmin,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    serializer_class = GroupProfileSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filters the public groups and private ones the current user is member of.
        """
        metadata_author_groups = get_user_visible_groups(self.request.user, include_public_invite=True)
        if not isinstance(metadata_author_groups, list):
            metadata_author_groups = list(metadata_author_groups.all())
        queryset = GroupProfile.objects.filter(id__in=[_g.id for _g in metadata_author_groups])
        return queryset.order_by("title")

    @extend_schema(
        methods=["get"],
        responses={200: UserSerializer(many=True)},
        description="API endpoint allowing to retrieve the Group members.",
    )
    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        group = self.get_object()
        members = get_user_model().objects.filter(id__in=group.member_queryset().values_list("user", flat=True))
        return Response(UserSerializer(embed=True, many=True).to_representation(members))

    @extend_schema(
        methods=["get"],
        responses={200: UserSerializer(many=True)},
        description="API endpoint allowing to retrieve the Group managers.",
    )
    @action(detail=True, methods=["get"])
    def managers(self, request, pk=None):
        group = self.get_object()
        managers = group.get_managers()
        return Response(UserSerializer(embed=True, many=True).to_representation(managers))

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the Group specific resources.",
    )
    @action(detail=True, methods=["get"])
    def resources(self, request, pk=None):
        group = self.get_object()
        resources = group.resources()
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        result_page = paginator.paginate_queryset(list(resources), request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True, context={"request": request})
        return paginator.get_paginated_response({"resources": serializer.data})


class RegionViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists regions.
    """

    permission_classes = [
        AllowAny,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter, FacetVisibleResourceFilter]
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
                if obj.get("tags", []):
                    slugs.append(obj.get("href"))
                _get_kw_hrefs(obj.get("nodes", []), slugs)
            return slugs

        slugs = _get_kw_hrefs(resource_keywords)
        return HierarchicalKeyword.objects.filter(slug__in=slugs)

    permission_classes = [
        AllowAny,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    serializer_class = HierarchicalKeywordSerializer
    pagination_class = GeoNodeApiPagination


class ThesaurusKeywordViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists Thesaurus keywords.
    """

    permission_classes = [
        AllowAny,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    queryset = ThesaurusKeyword.objects.all()
    serializer_class = ThesaurusKeywordSerializer
    pagination_class = GeoNodeApiPagination


class TopicCategoryViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists categories.
    """

    permission_classes = [
        AllowAny,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter, FacetVisibleResourceFilter]
    queryset = TopicCategory.objects.all()
    serializer_class = TopicCategorySerializer
    pagination_class = GeoNodeApiPagination


class OwnerViewSet(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that lists all possible owners.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        AllowAny,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
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
                "type_filter": self.request.query_params.get("type"),
                "title_filter": self.request.query_params.get("title__icontains"),
            }
        queryset = queryset.filter(
            id__in=Subquery(get_resources_with_perms(self.request.user, filter_options).values("owner"))
        )
        return queryset.order_by("username")


class ApiPresetsInitializer(APIView):
    """
    Replaces the `api_preset` query params with the configured params
    """

    def initialize_request(self, request, *args, **kwargs):
        self.replace_presets(request)
        return super().initialize_request(request, *args, **kwargs)

    def replace_presets(self, request):
        # we must make the GET mutable since in the filters, some queryparams are popped
        request.GET._mutable = True
        try:
            for preset_name in request.GET.pop("api_preset", []):
                presets = settings.REST_API_PRESETS.get(preset_name, None)
                if not presets:
                    logger.info(f'Preset "{preset_name}" is not defined')  # maybe return 404?
                    return
                for param_name in presets.keys():
                    for param_value in presets.get(param_name):
                        if param_value not in request.GET.get(param_name, []):
                            request.GET.appendlist(param_name, param_value)
        finally:
            request.GET._mutable = False


class ResourceBaseViewSet(ApiPresetsInitializer, DynamicModelViewSet, AdvertisedListMixin):
    """
    API endpoint that allows base resources to be viewed or edited.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]
    filter_backends = [
        TKeywordsFilter,
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        ResourceBasePermissionsFilter,
        FavoriteFilter,
    ]
    queryset = ResourceBase.objects.all().order_by("-created")
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination

    def _filtered(self, request, filter):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        resources = get_resources_with_perms(request.user).filter(**filter)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the approved Resources.",
    )
    @action(detail=False, methods=["get"])
    def approved(self, request, *args, **kwargs):
        return self._filtered(request, {"is_approved": True})

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the published Resources.",
    )
    @action(detail=False, methods=["get"])
    def published(self, request, *args, **kwargs):
        return self._filtered(request, {"is_published": True})

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the featured Resources.",
    )
    @action(detail=False, methods=["get"])
    def featured(self, request, *args, **kwargs):
        return self._filtered(request, {"featured": True})

    @extend_schema(
        methods=["get"],
        responses={200: FavoriteSerializer(many=True)},
        description="API endpoint allowing to retrieve the favorite Resources.",
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorites(self, request, pk=None, *args, **kwargs):
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        favorites = Favorite.objects.favorites_for_user(user=request.user)
        result_page = paginator.paginate_queryset(favorites, request)
        serializer = FavoriteSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"favorites": serializer.data})

    @extend_schema(
        methods=["post", "delete"],
        responses={200: FavoriteSerializer(many=True)},
        description="API endpoint allowing to retrieve the favorite Resources.",
    )
    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None, *args, **kwargs):
        resource = self.get_object()
        user = request.user

        if request.method == "POST":
            try:
                Favorite.objects.get(user=user, object_id=resource.pk)
                return Response({"message": "Resource is already in favorites"}, status=400)
            except Favorite.DoesNotExist:
                Favorite.objects.create_favorite(resource, user)
                return Response({"message": "Successfuly added resource to favorites"}, status=201)

        if request.method == "DELETE":
            try:
                Favorite.objects.get(user=user, object_id=resource.pk).delete()
                return Response({"message": "Successfuly removed resource from favorites"}, status=200)
            except Favorite.DoesNotExist:
                return Response({"message": "Resource not in favorites"}, status=404)

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseTypesSerializer()},
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
        """,
    )
    @action(detail=False, methods=["get"])
    def resource_types(self, request, *args, **kwargs):
        def _to_compact_perms_list(
            allowed_perms: dict, resource_type: str, resource_subtype: str, compact_perms_labels: dict = {}
        ) -> list:
            _compact_perms_list = {}
            for _k, _v in allowed_perms.items():
                _is_owner = _k not in ["anonymous", groups_settings.REGISTERED_MEMBERS_GROUP_NAME]
                _is_none_allowed = not _is_owner
                _compact_perms_list[_k] = get_compact_perms_list(
                    _v, resource_type, resource_subtype, _is_owner, _is_none_allowed, compact_perms_labels
                )
            return _compact_perms_list

        resource_types = []
        _types = []
        _allowed_perms = {}
        for _model in apps.get_models():
            if _model.__name__ == "ResourceBase":
                for _m in _model.__subclasses__():
                    if _m.__name__.lower() not in ["service"]:
                        _types.append(_m.__name__.lower())
                        _allowed_perms[_m.__name__.lower()] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(
                                _m.allowed_permissions,
                                _m.__name__.lower(),
                                _m.__name__.lower(),
                                _m.compact_permission_labels,
                            ),
                        }

        if settings.GEONODE_APPS_ENABLE and "geoapp" in _types:
            _types.remove("geoapp")
            if hasattr(settings, "CLIENT_APP_LIST") and settings.CLIENT_APP_LIST:
                _types += settings.CLIENT_APP_LIST
            else:
                from geonode.geoapps.models import GeoApp

                geoapp_types = [x for x in GeoApp.objects.values_list("resource_type", flat=True).all().distinct()]
                _types += geoapp_types

            if hasattr(settings, "CLIENT_APP_ALLOWED_PERMS_LIST") and settings.CLIENT_APP_ALLOWED_PERMS_LIST:
                for _type in settings.CLIENT_APP_ALLOWED_PERMS_LIST:
                    for _type_name, _type_perms in _type.items():
                        _compact_permission_labels = {}
                        if hasattr(settings, "CLIENT_APP_COMPACT_PERM_LABELS"):
                            _compact_permission_labels = settings.CLIENT_APP_COMPACT_PERM_LABELS.get(_type_name, {})
                        _allowed_perms[_type_name] = {
                            "perms": _type_perms,
                            "compact": _to_compact_perms_list(
                                _type_perms, _type_name, _type_name, _compact_permission_labels
                            ),
                        }
            else:
                from geonode.geoapps.models import GeoApp

                for _m in GeoApp.objects.filter(resource_type__in=_types).iterator():
                    if hasattr(_m, "resource_type") and _m.resource_type and _m.resource_type not in _allowed_perms:
                        _allowed_perms[_m.resource_type] = {
                            "perms": _m.allowed_permissions,
                            "compact": _to_compact_perms_list(
                                _m.allowed_permissions, _m.resource_type, _m.subtype, _m.compact_permission_labels
                            ),
                        }

        for _type in _types:
            resource_types.append(
                {
                    "name": _type,
                    "count": get_resources_with_perms(request.user).filter(resource_type=_type).count(),
                    "allowed_perms": _allowed_perms[_type] if _type in _allowed_perms else [],
                }
            )
        return Response({"resource_types": resource_types})

    @extend_schema(
        methods=["get", "put", "patch", "delete"],
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
        """,
    )
    @action(
        detail=True,
        url_path="permissions",  # noqa
        url_name="perms-spec",
        methods=["get", "put", "patch", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def resource_service_permissions(self, request, pk, *args, **kwargs):
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
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": 1001,"permissions": "owner"}]}'

        - Assigns View permissions to some users:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": 1000,"permissions": "view"}]}'

        - Assigns View permissions to anyone:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [],"organizations": [],"users": [{"id": -1,"permissions": "view"}]}'

        - Assigns View permissions to anyone and edit permissions to a Group on a Dataset:
            curl -u admin:admin --location --request PUT 'http://localhost:8000/api/v2/resources/<id>/permissions' \
                --header 'Content-Type: application/json' \
                --data-raw '{"groups": [{"id": 1,"permissions": "manage"}],"organizations": [],"users": [{"id": -1,"permissions": "view"}]}'

        """
        config = Configuration.load()
        resource = get_object_or_404(ResourceBase, pk=pk)
        _user_can_manage = request.user.has_perm("change_resourcebase_permissions", resource.get_self_resource())
        if (
            config.read_only
            or config.maintenance
            or request.user.is_anonymous
            or not request.user.is_authenticated
            or resource is None
            or not _user_can_manage
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            perms_spec = PermSpec(resource.get_all_level_info(), resource)
            request_params = request.data
            if request.method == "GET":
                return Response(perms_spec.compact)
            elif request.method == "DELETE":
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name="remove_permissions",
                    geonode_resource=resource,
                    action="permissions",
                    input_params={"uuid": request_params.get("uuid", resource.uuid)},
                )
            elif request.method == "PUT":
                perms_spec_compact = PermSpecCompact(request.data, resource)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name="set_permissions",
                    geonode_resource=resource,
                    action="permissions",
                    input_params={
                        "uuid": request_params.get("uuid", resource.uuid),
                        "owner": request_params.get("owner", resource.owner.username),
                        "permissions": perms_spec_compact.extended,
                        "created": request_params.get("created", False),
                    },
                )
            elif request.method == "PATCH":
                perms_spec_compact_patch = PermSpecCompact(request.data, resource)
                perms_spec_compact_resource = PermSpecCompact(perms_spec.compact, resource)
                perms_spec_compact_resource.merge(perms_spec_compact_patch)
                _exec_request = ExecutionRequest.objects.create(
                    user=request.user,
                    func_name="set_permissions",
                    geonode_resource=resource,
                    action="permissions",
                    input_params={
                        "uuid": request_params.get("uuid", resource.uuid),
                        "owner": request_params.get("owner", resource.owner.username),
                        "permissions": perms_spec_compact_resource.extended,
                        "created": request_params.get("created", False),
                    },
                )
            resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
            return Response(
                {
                    "status": _exec_request.status,
                    "execution_id": _exec_request.exec_id,
                    "status_url": urljoin(
                        settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": _exec_request.exec_id})
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["post"],
        responses={200},
        description="API endpoint allowing to set the thumbnail url for an existing dataset.",
    )
    @action(
        detail=False,
        url_path="(?P<resource_id>\d+)/set_thumbnail_from_bbox",  # noqa
        url_name="set-thumb-from-bbox",
        methods=["post"],
        permission_classes=[IsAuthenticated, UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}})],
    )
    def set_thumbnail_from_bbox(self, request, resource_id, *args, **kwargs):
        import traceback
        from django.utils.datastructures import MultiValueDictKeyError

        try:
            resource = ResourceBase.objects.get(id=ast.literal_eval(resource_id))

            map_thumb_from_bbox = False
            if isinstance(resource.get_real_instance(), Map):
                map_thumb_from_bbox = True

            if not isinstance(resource.get_real_instance(), (Dataset, Map)):
                raise NotImplementedError("Not implemented: Endpoint available only for Dataset and Maps")

            request_body = request.data if request.data else json.loads(request.body)
            try:
                # bbox format: (xmin, xmax, ymin, ymax)
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)
            except MultiValueDictKeyError:
                for _k, _v in request_body.items():
                    request_body = json.loads(_k)
                    break
                bbox = request_body["bbox"] + [request_body["srid"]]
                zoom = request_body.get("zoom", None)

            thumbnail_url = create_thumbnail(
                resource.get_real_instance(),
                bbox=bbox,
                background_zoom=zoom,
                overwrite=True,
                map_thumb_from_bbox=map_thumb_from_bbox,
            )
            return Response(
                {"message": "Thumbnail correctly created.", "success": True, "thumbnail_url": thumbnail_url}, status=200
            )
        except ResourceBase.DoesNotExist:
            traceback.print_exc()
            logger.error(f"Resource selected with id {resource_id} does not exists")
            return Response(
                data={"message": f"Resource selected with id {resource_id} does not exists", "success": False},
                status=404,
                exception=True,
            )
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
        methods=["post"], responses={200}, description="Instructs the Async dispatcher to execute a 'CREATE' operation."
    )
    @action(
        detail=False,
        url_path="create/(?P<resource_type>\w+)",  # noqa
        url_name="resource-service-create",
        methods=["post"],
        permission_classes=[IsAuthenticated, UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}})],
    )
    def resource_service_create(self, request, resource_type: str = None, *args, **kwargs):
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
        if (
            config.read_only
            or config.maintenance
            or request.user.is_anonymous
            or not request.user.is_authenticated
            or not request.user.has_perm("base.add_resourcebase")
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = self._get_request_params(request)
            uuid = request_params.get("uuid", str(uuid4()))
            resource_filter = ResourceBase.objects.filter(uuid=uuid)

            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name="create",
                geonode_resource=resource_filter.get() if resource_filter.exists() else None,
                action="create",
                input_params={
                    "uuid": uuid,
                    "resource_type": resource_type,
                    "defaults": request_params.get("defaults", f'{{"owner":"{request.user.username}"}}'),
                },
            )
            resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
            return Response(
                {
                    "status": _exec_request.status,
                    "execution_id": _exec_request.exec_id,
                    "status_url": urljoin(
                        settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": _exec_request.exec_id})
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["delete"],
        responses={200},
        description="Instructs the Async dispatcher to execute a 'DELETE' operation over a valid 'uuid'.",
    )
    @action(
        detail=True,
        url_path="delete",  # noqa
        url_name="resource-service-delete",
        methods=["delete"],
        permission_classes=[IsAuthenticated, UserHasPerms],
    )
    def resource_service_delete(self, request, pk, *args, **kwargs):
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
        resource = get_object_or_404(ResourceBase, pk=pk)
        if (
            config.read_only
            or config.maintenance
            or request.user.is_anonymous
            or not request.user.is_authenticated
            or resource is None
            or not request.user.has_perm("delete_resourcebase", resource.get_self_resource())
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name="delete",
                action="delete",
                geonode_resource=resource,
                input_params={"uuid": resource.uuid},
            )
            resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
            return Response(
                {
                    "status": _exec_request.status,
                    "execution_id": _exec_request.exec_id,
                    "status_url": urljoin(
                        settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": _exec_request.exec_id})
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["put"],
        responses={200},
        description="Instructs the Async dispatcher to execute a 'UPDATE' operation over a valid 'uuid'.",
    )
    @action(
        detail=True,
        url_path="update",  # noqa
        url_name="resource-service-update",
        methods=["put"],
        permission_classes=[IsAuthenticated, UserHasPerms],
    )
    def resource_service_update(self, request, pk, *args, **kwargs):
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
        resource = get_object_or_404(ResourceBase, pk=pk)
        if (
            config.read_only
            or config.maintenance
            or request.user.is_anonymous
            or not request.user.is_authenticated
            or resource is None
            or not request.user.has_perm("change_resourcebase", resource.get_self_resource())
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            request_params = self._get_request_params(request=request)
            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name="update",
                geonode_resource=resource,
                action="update",
                input_params={
                    "uuid": request_params.get("uuid", resource.uuid),
                    "xml_file": request_params.get("xml_file", None),
                    "metadata_uploaded": request_params.get("metadata_uploaded", False),
                    "vals": request_params.get("vals", "{}"),
                    "regions": request_params.get("regions", "[]"),
                    "keywords": request_params.get("keywords", "[]"),
                    "custom": request_params.get("custom", "{}"),
                    "notify": request_params.get("notify", True),
                },
            )
            resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
            return Response(
                {
                    "status": _exec_request.status,
                    "execution_id": _exec_request.exec_id,
                    "status_url": urljoin(
                        settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": _exec_request.exec_id})
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["put"],
        responses={200},
        description="Instructs the Async dispatcher to execute a 'COPY' operation over a valid 'uuid'.",
    )
    @action(
        detail=True,
        url_path="copy",  # noqa
        url_name="resource-service-copy",
        methods=["put"],
        permission_classes=[
            IsAuthenticated,
            UserHasPerms(
                perms_dict={
                    "dataset": {"PUT": ["base.add_resourcebase", "base.download_resourcebase"], "rule": all},
                    "document": {"PUT": ["base.add_resourcebase", "base.download_resourcebase"], "rule": all},
                    "default": {"PUT": ["base.add_resourcebase"]},
                }
            ),
        ],
    )
    def resource_service_copy(self, request, pk, *args, **kwargs):
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
        resource = get_object_or_404(ResourceBase, pk=pk)
        if (
            config.read_only
            or config.maintenance
            or request.user.is_anonymous
            or not request.user.is_authenticated
            or resource is None
            or not request.user.has_perm("view_resourcebase", resource.get_self_resource())
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if not resource.is_copyable:
            return Response({"message": "Resource can not be cloned."}, status=400)
        try:
            request_params = self._get_request_params(request)

            _exec_request = ExecutionRequest.objects.create(
                user=request.user,
                func_name="copy",
                geonode_resource=resource,
                action="copy",
                input_params={
                    "instance": resource.id,
                    "owner": request_params.get("owner", request.user.username),
                    "defaults": request_params.get("defaults", "{}"),
                },
            )
            resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
            return Response(
                {
                    "status": _exec_request.status,
                    "execution_id": _exec_request.exec_id,
                    "status_url": urljoin(
                        settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": _exec_request.exec_id})
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    @extend_schema(
        methods=["put"], responses={200}, description="API endpoint allowing to set thumbnail of the Resource."
    )
    @action(
        detail=True,
        url_path="set_thumbnail",
        url_name="set_thumbnail",
        methods=["put"],
        permission_classes=[IsAuthenticated, UserHasPerms],
        parser_classes=[JSONParser, MultiPartParser],
    )
    def set_thumbnail(self, request, pk, *args, **kwargs):
        resource = get_object_or_404(ResourceBase, pk=pk)

        if not request.data.get("file"):
            raise ValidationError("Field file is required")

        file_data = request.data["file"]

        if isinstance(file_data, str):
            if re.match(BASE64_PATTERN, file_data):
                try:
                    thumbnail, _thumbnail_format = _decode_base64(file_data)
                except Exception:
                    return Response(
                        "The request body is not a valid base64 string or the image format is not PNG or JPEG",
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                try:
                    # Check if file_data is a valid url and set it as thumbail_url
                    validate = URLValidator()
                    validate(file_data)
                    if urlparse(file_data).path.rsplit(".")[-1] not in ["png", "jpeg", "jpg"]:
                        return Response(
                            "The url must be of an image with format (png, jpeg or jpg)",
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    resource.thumbnail_url = file_data
                    resource.save()
                    return Response({"thumbnail_url": resource.thumbnail_url})
                except Exception:
                    raise ValidationError(
                        detail="file is either a file upload, ASCII byte string or a valid image url string"
                    )
        else:
            # Validate size
            if file_data.size > 1000000:
                raise ValidationError(detail="File must not exceed 1MB")

            thumbnail = file_data.read()
            try:
                file_data.seek(0)
                Image.open(file_data)
            except Exception:
                raise ValidationError(detail="Invalid data provided")
        if thumbnail:
            resource_manager.set_thumbnail(resource.uuid, instance=resource, thumbnail=thumbnail)
            return Response({"thumbnail_url": resource.thumbnail_url})
        return Response("Unable to set thumbnail", status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=["get", "put", "delete", "post"], description="Get/Update/Delete/Add extra metadata for resource"
    )
    @action(
        detail=True,
        methods=["get", "put", "delete", "post"],
        permission_classes=[IsOwnerOrAdmin, UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}})],
        url_path=r"extra_metadata",  # noqa
        url_name="extra-metadata",
    )
    def extra_metadata(self, request, pk, *args, **kwargs):
        _obj = get_object_or_404(ResourceBase, pk=pk)

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
            """
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
            """
            for _m in extra_metadata:
                _id = _m.pop("id")
                ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id=_id).update(metadata=_m)
            logger.info("metadata updated for the selected resource")
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "DELETE":
            # delete single metadata
            """
            Expect a payload with the IDs of the metadata that should be deleted. Payload be like:
            [4, 3]
            """
            ResourceBase.objects.filter(id=_obj.id).first().metadata.filter(id__in=request.data).delete()
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()))
        elif request.method == "POST":
            # add new metadata
            """
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
            """
            for _m in extra_metadata:
                new_m = ExtraMetadata.objects.create(resource=_obj, metadata=_m)
                new_m.save()
                _obj.metadata.add(new_m)
            _obj.refresh_from_db()
            return Response(ExtraMetadataSerializer().to_representation(_obj.metadata.all()), status=201)

    def _get_request_params(self, request, encode=False):
        try:
            return (
                QueryDict(request.body, mutable=True, encoding="UTF-8")
                if encode
                else QueryDict(request.body, mutable=True)
            )
        except Exception as e:
            """
            The request with the barer token access to the request.data during the token verification
            so in this case if the request.body cannot not access, we just re-access to the
            request.data to get the params needed
            """
            logger.debug(e)
            return request.data

    @extend_schema(methods=["get", "post", "delete"], description="Get Linked Resources")
    @action(
        detail=True,
        methods=["get", "post", "delete"],
        permission_classes=[UserHasPerms(perms_dict={"default": {"GET": ["base.view_resourcebase"]}})],
        url_path=r"linked_resources",  # noqa
        url_name="linked_resources",
    )
    def linked_resources(self, request, pk, *args, **kwargs):
        resource = self.get_object()
        if request.method in ("POST", "DELETE"):
            success_var = []
            error_var = []
            payload = {"success": success_var, "error": error_var, "message": "Resources updated successfully"}

            target_ids = request.data.get("target")
            if not isinstance(target_ids, list):
                raise ValidationError("Payload is not valid")

            # remove duplicates and self ref
            target_ids = set(target_ids)
            if resource.id in target_ids:
                error_var.append(resource.id)

            valid_ids = target_ids - {resource.id}

            for t_id in valid_ids:
                try:
                    target = get_object_or_404(ResourceBase, pk=t_id)

                    if request.method == "POST":
                        _, created = LinkedResource.objects.get_or_create(source=resource, target=target)
                        if created:
                            success_var.append(t_id)
                            continue
                        error_var.append(t_id)
                    if request.method == "DELETE":
                        link = LinkedResource.objects.filter(source=resource.id, target=t_id).first()
                        if not link:
                            logger.error(f"Resource selected with id {t_id} does not exist")
                            error_var.append(t_id)
                            continue
                        link.delete()
                        success_var.append(t_id)
                except Exception:
                    error_var.append(t_id)
                    logger.error(f"Resource with id {t_id} not found")

            if len(error_var):
                payload["message"] = "Some error has occurred during the saving"
                return Response(payload, status=400)

            return Response(payload, status=200)

        return base_linked_resources(self.get_object().get_real_instance(), request.user, request.GET)


def base_linked_resources(instance, user, params):
    try:
        return Response(base_linked_resources_payload(instance, user, params))
    except Exception as e:
        logger.exception(e)
        return Response(data={"message": e.args[0], "success": False}, status=500, exception=True)


def base_linked_resources_payload(instance, user, params={}):
    resource_type = params.get("resource_type", None)
    link_type = params.get("link_type", None)
    type_list = resource_type.split(",") if resource_type else []

    warnings = {}

    if "page_size" in params or "page" in params:
        warnings["PAGINATION"] = "Pagination is not supported on this call"

    ret = {"WARNINGS": warnings}

    get_visible_resources_p = functools.partial(
        get_visible_resources,
        user=user,
        admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
        unpublished_not_visible=settings.RESOURCE_PUBLISHING,
        private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
    )

    if not link_type or link_type == "linked_to":
        # list of linked resources, probably extended by ResourceBase's child class - may be loopable only once
        linked_to_over = instance.get_linked_resources()

        # resolve the ids of linked resources - using either e QuerySet (preferred) or a list
        if isinstance(linked_to_over, QuerySet):
            linked_to_over_loopable = linked_to_over
            linked_to_id_values = linked_to_over.values("target_id")
        else:
            linked_to_over_loopable = [lr for lr in linked_to_over]
            linked_to_id_values = [lr.target_id for lr in linked_to_over_loopable]

        # filter resources by visibility / permissions
        linked_to_visib = get_visible_resources_p(ResourceBase.objects.filter(id__in=linked_to_id_values)).order_by(
            "-pk"
        )
        # optionally filter by resource type
        linked_to_visib = linked_to_visib.filter(resource_type__in=type_list) if type_list else linked_to_visib
        linked_to_visib_ids = linked_to_visib.values_list("id", flat=True)
        linked_to = [lres for lres in linked_to_over_loopable if lres.target.id in linked_to_visib_ids]

        ret["linked_to"] = LinkedResourceSerializer(linked_to, embed=True, many=True).data

    if not link_type or link_type == "linked_by":
        linked_by_over = instance.get_linked_resources(as_target=True)
        if isinstance(linked_by_over, QuerySet):
            linked_by_over_loopable = linked_by_over
            linked_by_id_values = linked_by_over.values("source_id")
        else:
            linked_by_over_loopable = [lr for lr in linked_by_over]
            linked_by_id_values = [lr.source_id for lr in linked_by_over_loopable]

        linked_by_visib = get_visible_resources_p(ResourceBase.objects.filter(id__in=linked_by_id_values)).order_by(
            "-pk"
        )

        linked_by_visib = linked_by_visib.filter(resource_type__in=type_list) if type_list else linked_by_visib
        linked_by_visib_ids = linked_by_visib.values_list("id", flat=True)
        linked_by = [lres for lres in linked_by_over_loopable if lres.source.id in linked_by_visib_ids]

        ret["linked_by"] = LinkedResourceSerializer(
            instance=linked_by, serialize_source=True, embed=True, many=True
        ).data

    if not ret["WARNINGS"]:
        ret.pop("WARNINGS")

    return ret
