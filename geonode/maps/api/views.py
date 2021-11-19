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

from drf_spectacular.utils import extend_schema
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from geonode.base import register_event
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.layers.api.serializers import DatasetSerializer
from geonode.maps.api.permissions import MapPermissionsFilter
from geonode.maps.api.serializers import MapLayerSerializer, MapSerializer
from geonode.maps.contants import _PERMISSION_MSG_SAVE
from geonode.maps.models import Map
from geonode.maps.signals import map_changed_signal
from geonode.maps.utils.thumbnail import handle_map_thumbnail
from geonode.monitoring.models import EventType
from geonode.resource.manager import resource_manager
from geonode.utils import resolve_object

logger = logging.getLogger(__name__)


class MapViewSet(DynamicModelViewSet):
    """
    API endpoint that allows maps to be viewed or edited.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        MapPermissionsFilter,
    ]
    queryset = Map.objects.all().order_by("-date")
    serializer_class = MapSerializer
    pagination_class = GeoNodeApiPagination

    def list(self, request, *args, **kwargs):
        # Avoid overfetching removing mapslayer of the list.
        request.query_params.add("exclude[]", "maplayers")
        return super(MapViewSet, self).list(request, *args, **kwargs)

    @extend_schema(
        methods=["get"],
        responses={200: MapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def maplayers(self, request, pk=None):
        map = self.get_object()
        resources = map.datasets
        return Response(MapLayerSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: DatasetSerializer(many=True)},
        description="API endpoint allowing to retrieve the local MapLayers.",
    )
    @action(detail=True, methods=["get"])
    def local_datasets(self, request, pk=None):
        map = self.get_object()
        resources = map.local_datasets
        return Response(DatasetSerializer(embed=True, many=True).to_representation(resources))

    def perform_create(self, serializer):
        self._get_data_from_blob(serializer)
        # Thumbnail will be handled later
        post_creation_data = {"thumbnail": serializer.validated_data.pop("thumbnail_url", "")}
        # M2M maplayers
        serializer.validated_data["maplayers"] = self._create_m2m_maplayers(serializer)

        instance = serializer.save(
            owner=self.request.user,
            resource_type="map",
            uuid=str(uuid4()),
        )

        # thumbnail, events and resouce routines
        self._post_change_routines(
            instance=instance,
            create_action_perfomed=True,
            additional_data=post_creation_data,
        )

    def perform_update(self, serializer):
        # Check instance permissions with resolve_object
        mapid = serializer.validated_data["id"]
        key = "urlsuffix" if Map.objects.filter(urlsuffix=mapid).exists() else "pk"
        map_obj = resolve_object(self.request, Map, {key: mapid}, permission="base.change_resourcebase", permission_msg=_PERMISSION_MSG_SAVE)
        instance = serializer.instance
        assert instance == map_obj
        # Thumbnail will be handled later
        post_change_data = {
            "thumbnail": serializer.validated_data.pop("thumbnail_url", ""),
            "dataset_names_before_changes": [lyr.alternate for lyr in instance.local_datasets],
        }
        # M2M maplayers
        serializer.validated_data["maplayers"] = self._create_m2m_maplayers(serializer)

        instance = serializer.save()

        # thumbnail, events and resouce routines
        self._post_change_routines(
            instance=instance,
            create_action_perfomed=False,
            additional_data=post_change_data,
        )

    def _create_m2m_maplayers(self, serializer):
        if "maplayers" not in serializer.validated_data:
            # Do nothing, partial update, without changes to maplayers
            return []

        if serializer.instance:
            # Delete all existing maplayers
            serializer.instance.maplayers.all().delete()

        # Initialize maplayers serializer
        maplayers_data = serializer.validated_data.pop("maplayers")
        maplayers_serializer = MapLayerSerializer(data=maplayers_data, many=True)
        maplayers_serializer.is_valid(raise_exception=True)

        # Create new maplayers, map relation will be added by serializer.save()
        maplayers = maplayers_serializer.save()
        return maplayers

    def _get_maplayers_data_from_blob(self, blob_map_data: dict):
        maplayer_data = []
        datasets = blob_map_data.get("layers", [])
        for ordering, dataset in enumerate(datasets):
            maplayer = {
                "extra_params": {
                    "msId": dataset["id"]
                },
                "name": dataset.get("name", None),
                "current_style": "",
                "styles": [],
            }
            maplayer_data.append(maplayer)
        return maplayer_data

    def _get_data_from_blob(self, serializer):
        """
        TODO: To be removed, the blob data will not be read by geonode
        This will be changed after the mapstore updates by the issue here below
        Issue: https://github.com/GeoNode/geonode-mapstore-client/issues/574
        """
        blob_map_data = serializer.validated_data["blob"]["map"]
        serializer.validated_data["center_x"] = blob_map_data["center"]["x"]
        serializer.validated_data["center_y"] = blob_map_data["center"]["y"]
        serializer.validated_data["projection"] = blob_map_data["projection"]
        serializer.validated_data["zoom"] = blob_map_data["zoom"]
        serializer.validated_data["srid"] = blob_map_data["projection"]

        # Get MapLayer data
        if "maplayers" not in serializer.validated_data:
            serializer.validated_data["maplayers"] = self._get_maplayers_data_from_blob(blob_map_data)

    def _post_change_routines(self, instance: Map, create_action_perfomed: bool, additional_data: dict):
        # Step 1: Handle Maplayers signals if this is and update action
        if not create_action_perfomed:
            dataset_names_before_changes = additional_data.pop("dataset_names_before_changes", [])
            dataset_names_after_changes = [lyr.alternate for lyr in instance.local_datasets]
            if dataset_names_before_changes != dataset_names_after_changes:
                map_changed_signal.send_robust(sender=instance, what_changed="datasets")
        # Step 2: Register Event
        event_type = EventType.EVENT_CREATE if create_action_perfomed else EventType.EVENT_CHANGE
        register_event(self.request, event_type, instance)
        # Step 3: Resource Manager
        resource_manager.update(instance.uuid, instance=instance, notify=True)
        resource_manager.set_thumbnail(instance.uuid, instance=instance, overwrite=False)
        # Step 4: Handle Thumbnail
        handle_map_thumbnail(thumbnail=additional_data["thumbnail"], map_obj=instance)
