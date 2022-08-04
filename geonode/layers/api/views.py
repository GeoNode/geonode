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
from urllib.request import Request
from drf_spectacular.utils import extend_schema, OpenApiExample

from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.response import Response

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.layers.api.exceptions import GeneralDatasetException, InvalidDatasetException
from geonode.layers.models import Dataset
from geonode.layers.utils import validate_input_source
from geonode.maps.api.serializers import SimpleMapLayerSerializer, SimpleMapSerializer
from rest_framework.exceptions import NotFound

from geonode.storage.manager import StorageManager
from geonode.resource.manager import resource_manager

from .serializers import DatasetReplaceAppendSerializer, DatasetSerializer, DatasetListSerializer
from .permissions import DatasetPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class DatasetViewSet(DynamicModelViewSet):
    """
    API endpoint that allows layers to be viewed or edited.
    """
    http_method_names = ['get', 'patch', 'put']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        DatasetPermissionsFilter,
    ]
    queryset = Dataset.objects.all().order_by("-last_updated")
    serializer_class = DatasetSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer_class(self):
        if self.action == "list":
            return DatasetListSerializer
        return DatasetSerializer

    @extend_schema(
        methods=["get"],
        responses={200: SimpleMapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def maplayers(self, request, pk=None):
        dataset = self.get_object()
        resources = dataset.maplayers
        return Response(SimpleMapLayerSerializer(many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: SimpleMapSerializer(many=True)},
        description="API endpoint allowing to retrieve maps using the dataset.",
    )
    @action(detail=True, methods=["get"])
    def maps(self, request, pk=None):
        dataset = self.get_object()
        resources = dataset.maps
        return Response(SimpleMapSerializer(many=True).to_representation(resources))

    @extend_schema(
        methods=["patch"],
        responses={200},
        description="API endpoint allowing to replace a dataset.",
        examples=[
            OpenApiExample(
                "Example1",
                summary="expected payload",
                description="Example of the input payload",
                value='{\
                    "base_file": "/home/mattia/gis_data/single_point/single_point.shp",\
                    "dbf_file": "/home/mattia/gis_data/single_point/single_point.dbf",\
                    "shx_file": "/home/mattia/gis_data/single_point/single_point.shx",\
                    "prj_file": "/home/mattia/gis_data/single_point/single_point.prj",\
                    "xml_file": "/home/mattia/gis_data/single_point.xml",\
                    "store_spatial_files": False\
                }',
            )
        ],
    )
    @action(
        detail=False,
        url_path="(?P<dataset_id>\d+)/replace",  # noqa
        url_name="replace-dataset",
        methods=["patch"],
        serializer_class=DatasetReplaceAppendSerializer,
    )
    def replace(self, request, dataset_id=None):
        """
        Edpoint for replace data to an existing layer
        """
        return self._replace_or_append(request, dataset_id, action="replace")

    @extend_schema(
        methods=["patch"],
        responses={200, 500},
        description="API endpoint allowing to append data to dataset.",
        examples=[
            OpenApiExample(
                "Example1",
                summary="expected payload",
                description="Example of the input payload",
                value='{\
                    "base_file": "/home/mattia/gis_data/single_point/single_point.shp",\
                    "dbf_file": "/home/mattia/gis_data/single_point/single_point.dbf",\
                    "shx_file": "/home/mattia/gis_data/single_point/single_point.shx",\
                    "prj_file": "/home/mattia/gis_data/single_point/single_point.prj",\
                    "xml_file": "/home/mattia/gis_data/single_point.xml",\
                    "store_spatial_files": False\
                }',
            )
        ],
    )
    @action(
        detail=False,
        url_path="(?P<dataset_id>\d+)/append",  # noqa
        url_name="append-dataset",
        methods=["patch"],
        serializer_class=DatasetReplaceAppendSerializer,
    )
    def append(self, request, dataset_id=None):
        """
        Edpoint for replace data to an existing layer
        """
        return self._replace_or_append(request, dataset_id, action="append")

    def _replace_or_append(self, request: Request, dataset_id: int, action: str) -> Response:
        """
        Raise error if the datasets does not exists
        """
        if not self.queryset.filter(id=dataset_id).exists():
            raise NotFound(detail=f"Layer with ID {dataset_id} is not available")

        serializer = self.serializer_class(data=request.data)
        """
        Raise error if the serializer is invalid. Instead of the default exception
        We raise a custom one with the list of the erros from the serializer
        """
        if not serializer.is_valid(raise_exception=False):
            raise InvalidDatasetException(detail=serializer.errors)

        data = serializer.data.copy()

        dataset = self.queryset.get(id=dataset_id)

        """
        This validation will ensure that the new input file are fully compliant
        with the existing dataset. If not, an InvalidDatasetException is raised
        """
        store_spatial_files = data.pop("store_spatial_files")

        try:
            storage_manager = StorageManager(remote_files=data)

            storage_manager.clone_remote_files()

            files = storage_manager.get_retrieved_paths()

            validate_input_source(
                layer=dataset,
                filename=data.get("base_file"),
                files={_file.split(".")[1]: _file for _file in files.values()},
                gtype=dataset.gtype,
                action_type=action,
                storage_manager=storage_manager,
            )

            xml_file = files.pop('xml_file', None)
            sld_file = files.pop('sld_file', None)

            call_kwargs = {
                "instance": dataset,
                "vals": {'files': list(files.values()), 'user': request.user},
                "store_spatial_files": store_spatial_files,
                "xml_file": xml_file,
                "metadata_uploaded": True if xml_file is not None else False,
                "sld_file": sld_file,
                "sld_uploaded": True if sld_file is not None else False
            }

            getattr(resource_manager, action)(**call_kwargs)

        except Exception as e:
            raise GeneralDatasetException(e)
        finally:
            '''
            Always keep the temporary folder under control.
            '''
            if not store_spatial_files:
                storage_manager.delete_retrieved_paths()
        # For now, we will return the input dataset
        data = {
            "alternate": dataset.alternate,
            "state": "success",
            "action": action
        }
        return Response(data)
