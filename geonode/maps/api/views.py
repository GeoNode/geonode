#########################################################################
#
# Copyright (C) 2021 OSGeo
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
from uuid import uuid4

from django.db import transaction
from drf_spectacular.utils import extend_schema
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from geonode.base import register_event
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, AdvertisedFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.base.api.views import ApiPresetsInitializer
from geonode.base.enumerations import EventType
from geonode.layers.api.serializers import DatasetSerializer
from geonode.maps.api.exception import GeneralMapsException
from geonode.maps.api.permissions import MapPermissionsFilter
from geonode.maps.api.serializers import MapLayerSerializer, MapSerializer
from geonode.maps.contants import _PERMISSION_MSG_SAVE
from geonode.maps.models import Map
from geonode.metadata.multilang.views import MultiLangViewMixin
from geonode.resource.registry import resource_manager_registry
from geonode.utils import resolve_object

logger = logging.getLogger(__name__)


class MapViewSet(ApiPresetsInitializer, MultiLangViewMixin, DynamicModelViewSet):
    """
    API endpoint that allows maps to be viewed or edited.
    """

    http_method_names = ["get", "patch", "post", "put"]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        AdvertisedFilter,
        ExtentFilter,
        MapPermissionsFilter,
    ]
    queryset = Map.objects.all().order_by("-created")
    serializer_class = MapSerializer
    pagination_class = GeoNodeApiPagination

    def list(self, request, *args, **kwargs):
        # Avoid overfetching removing mapslayer of the list.
        request.query_params.add("exclude[]", "maplayers")
        return super(MapViewSet, self).list(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Changes in the m2m `maplayers` are committed before object changes.
        To protect the db, this action is done within an atomic tansation.
        """
        return super(MapViewSet, self).update(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Changes in the m2m `maplayers` are committed before object changes.
        To protect the db, this action is done within an atomic tansation.
        """
        return super(MapViewSet, self).create(request, *args, **kwargs)

    @extend_schema(
        methods=["get"],
        responses={200: MapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def maplayers(self, request, pk=None, *args, **kwargs):
        map = self.get_object()
        resources = map.maplayers
        return Response(MapLayerSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: DatasetSerializer(many=True)},
        description="API endpoint allowing to retrieve the local MapLayers.",
    )
    @action(detail=True, methods=["get"])
    def datasets(self, request, pk=None, *args, **kwargs):
        map = self.get_object()
        resources = map.datasets
        return Response(DatasetSerializer(embed=True, many=True).to_representation(resources))

    def perform_create(self, serializer):
        payload = serializer.validated_data.copy()
        request_user = self.request.user
        payload["owner"] = request_user
        payload["resource_type"] = "map"
        payload["uuid"] = str(uuid4())
        instance = resource_manager_registry.get_for_model(Map).create(
            payload["uuid"],
            resource_type=Map,
            defaults=payload,
            user=request_user,
        )
        serializer.instance = instance
        register_event(self.request, EventType.EVENT_CREATE, instance)

    def perform_update(self, serializer):
        mapid = serializer.instance.id
        key = "urlsuffix" if Map.objects.filter(urlsuffix=mapid).exists() else "pk"
        map_obj = resolve_object(
            self.request, Map, {key: mapid}, permission="base.change_resourcebase", permission_msg=_PERMISSION_MSG_SAVE
        )
        instance = serializer.instance
        if instance != map_obj:
            raise GeneralMapsException(detail="serializer instance and object are different")

        dataset_names_before_changes = [lyr.alternate for lyr in instance.datasets]
        # Preserve serializer-side validation and group/role logic before manager hooks.
        instance = serializer.save()
        instance = resource_manager_registry.get_for_instance(instance).update(
            instance.uuid,
            instance=instance,
            dataset_names_before_changes=dataset_names_before_changes,
            notify=True,
        )
        serializer.instance = instance
        register_event(self.request, EventType.EVENT_CHANGE, instance)
