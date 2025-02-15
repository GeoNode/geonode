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
from urllib.parse import urljoin, urlsplit
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
from pathlib import Path
from geonode.resource.enumerator import ExecutionRequestAction
from django.utils.translation import gettext_lazy as _
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, FavoriteFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import (
    IsSelfOrAdminOrReadOnly,
    ResourceBasePermissionsFilter,
    UserHasPerms,
)
from rest_framework.exceptions import ValidationError
from rest_framework import status
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.base.api.views import ResourceBaseViewSet
from geonode.base.models import ResourceBase
from geonode.storage.manager import StorageManager
from geonode.upload.api.permissions import UploadPermissionsFilter
from geonode.upload.models import UploadParallelismLimit, UploadSizeLimit
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.api.exceptions import HandlerException, ImportException
from geonode.upload.api.serializer import ImporterSerializer
from geonode.upload.celery_tasks import import_orchestrator
from geonode.upload.orchestrator import orchestrator
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from geonode.assets.handlers import asset_handler_registry
from geonode.assets.local import LocalAssetHandler
from geonode.proxy.utils import proxy_urls_registry

from geonode.upload.api.serializer import (
    UploadParallelismLimitSerializer,
    UploadSizeLimitSerializer,
)

logger = logging.getLogger("importer")


class UploadSizeLimitViewSet(DynamicModelViewSet):
    http_method_names = ["get", "post"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadSizeLimit.objects.all()
    serializer_class = UploadSizeLimitSerializer
    pagination_class = GeoNodeApiPagination

    def destroy(self, request, *args, **kwargs):
        protected_objects = [
            "dataset_upload_size",
            "document_upload_size",
            "file_upload_handler",
        ]
        instance = self.get_object()
        if instance.slug in protected_objects:
            detail = _(f"The limit `{instance.slug}` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadParallelismLimitViewSet(DynamicModelViewSet):
    http_method_names = ["get", "post"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadParallelismLimit.objects.all()
    serializer_class = UploadParallelismLimitSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer(self, *args, **kwargs):
        serializer = super(UploadParallelismLimitViewSet, self).get_serializer(*args, **kwargs)
        if self.action == "create":
            serializer.fields["slug"].read_only = False
        return serializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.slug == "default_max_parallel_uploads":
            detail = _("The limit `default_max_parallel_uploads` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ImporterViewSet(DynamicModelViewSet):
    """
    API endpoint that allows uploads to be viewed or edited.
    """

    parser_class = [JSONParser, FileUploadParser, MultiPartParser]

    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        OAuth2Authentication,
    ]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        UploadPermissionsFilter,
    ]
    queryset = ResourceBase.objects.all().order_by("-last_updated")
    serializer_class = ImporterSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ["get", "post"]

    def get_serializer_class(self):
        specific_serializer = orchestrator.get_serializer(self.request.data)
        return specific_serializer or ImporterSerializer

    def create(self, request, *args, **kwargs):
        """
        Main function called by the new import flow.
        It received the file via the front end
        if is a gpkg (in future it will support all the vector file)
        the new import flow is follow, else the normal upload api is used.
        It clone on the local repo the file that the user want to upload
        """
        _file = request.FILES.get("base_file") or request.data.get("base_file")
        execution_id = None
        asset_handler = LocalAssetHandler()
        asset_dir = asset_handler._create_asset_dir()

        serializer = self.get_serializer_class()
        data = serializer(data=request.data)
        storage_manager = None
        # serializer data validation
        data.is_valid(raise_exception=True)
        _data = {
            **data.data.copy(),
            **{key: value[0] if isinstance(value, list) else value for key, value in request.FILES.items()},
        }

        if "zip_file" in _data or "kmz_file" in _data:
            # if a zipfile is provided, we need to unzip it before searching for an handler
            zipname = Path(_data["base_file"].name).stem
            storage_manager = StorageManager(remote_files={"base_file": _data.get("zip_file", _data.get("kmz_file"))})
            # cloning and unzip the base_file
            storage_manager.clone_remote_files(cloning_directory=asset_dir, create_tempdir=False)
            # update the payload with the unziped paths
            _data.update(
                {
                    **{"original_zip_name": zipname},
                    **storage_manager.get_retrieved_paths(),
                }
            )

        handler = orchestrator.get_handler(_data)
        # not file but handler means that is a remote resource
        if handler:
            asset = None
            files = []
            try:
                # cloning data into a local folder
                extracted_params, _data = handler.extract_params_from_data(_data)
                if _file:
                    storage_manager, asset, files = self._handle_asset(
                        request, asset_dir, storage_manager, _data, handler
                    )

                    self.validate_upload(request, storage_manager)

                if "url" in extracted_params:
                    # we should register the hosts for the proxy
                    proxy_urls_registry.register_host(urlsplit(extracted_params["url"]).hostname)

                input_params = {
                    **{"files": files, "handler_module_path": str(handler)},
                    **extracted_params,
                }

                if asset:
                    input_params.update(
                        {
                            "asset_id": asset.id,
                            "asset_module_path": f"{asset.__module__}.{asset.__class__.__name__}",
                        }
                    )
                action = input_params.get("action")
                execution_id = orchestrator.create_execution_request(
                    user=request.user,
                    func_name=next(iter(handler.get_task_list(action=action))),
                    step=_(next(iter(handler.get_task_list(action=action)))),
                    input_params=input_params,
                    action=action,
                    name=_file.name if _file else extracted_params.get("title", None),
                )

                sig = import_orchestrator.s(files, str(execution_id), handler=str(handler), action=action)
                sig.apply_async()
                return Response(data={"execution_id": execution_id}, status=201)
            except Exception as e:
                # in case of any exception, is better to delete the
                # cloned files to keep the storage under control
                if asset:
                    try:
                        asset.delete()
                    except Exception as _exc:
                        logger.warning(_exc)
                elif storage_manager is not None:
                    storage_manager.delete_retrieved_paths(force=True)
                if execution_id:
                    orchestrator.set_as_failed(execution_id=str(execution_id), reason=e)
                logger.exception(e)
                raise ImportException(detail=e.args[0] if len(e.args) > 0 else e)

        raise ImportException(detail="No handlers found for this dataset type/action")

    def _handle_asset(self, request, asset_dir, storage_manager, _data, handler):
        if storage_manager is None:
            # means that the storage manager is not initialized yet, so
            # the file is not a zip
            storage_manager = StorageManager(remote_files=_data)
            storage_manager.clone_remote_files(cloning_directory=asset_dir, create_tempdir=False)
            # get filepath
        asset, files = self.generate_asset_and_retrieve_paths(request, storage_manager, handler)
        return storage_manager, asset, files

    def validate_upload(self, request, storage_manager):
        upload_validator = UploadLimitValidator(request.user)
        upload_validator.validate_parallelism_limit_per_user()
        upload_validator.validate_files_sum_of_sizes(storage_manager.data_retriever)

    def generate_asset_and_retrieve_paths(self, request, storage_manager, handler):
        asset_handler = asset_handler_registry.get_default_handler()
        _files = storage_manager.get_retrieved_paths()
        asset = asset_handler.create(
            title="Original",
            owner=request.user,
            description=None,
            type=handler.id,
            files=list(set(_files.values())),
            clone_files=False,
        )

        return asset, _files


class ResourceImporter(DynamicModelViewSet):
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        OAuth2Authentication,
    ]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(
            perms_dict={
                "dataset": {
                    "PUT": ["base.add_resourcebase", "base.download_resourcebase"],
                    "rule": all,
                },
                "document": {
                    "PUT": ["base.add_resourcebase", "base.download_resourcebase"],
                    "rule": all,
                },
                "default": {"PUT": ["base.add_resourcebase"]},
            }
        ),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        ResourceBasePermissionsFilter,
        FavoriteFilter,
    ]
    queryset = ResourceBase.objects.all().order_by("-last_updated")
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination

    def copy(self, request, *args, **kwargs):
        try:
            resource = self.get_object()
            if resource.resourcehandlerinfo_set.exists():
                handler_module_path = resource.resourcehandlerinfo_set.first().handler_module_path

                action = ExecutionRequestAction.COPY.value

                handler = orchestrator.load_handler(handler_module_path)

                if not handler.can_do(action):
                    raise HandlerException(
                        detail=f"The handler {handler_module_path} cannot manage the action required: {action}"
                    )

                step = next(iter(handler.get_task_list(action=action)))

                extracted_params, _data = handler.extract_params_from_data(request.data, action=action)

                execution_id = orchestrator.create_execution_request(
                    user=request.user,
                    func_name=step,
                    step=step,
                    action=action,
                    input_params={
                        **{"handler_module_path": handler_module_path},
                        **extracted_params,
                    },
                )

                sig = import_orchestrator.s(
                    {},
                    str(execution_id),
                    step=step,
                    handler=str(handler_module_path),
                    action=action,
                    layer_name=resource.title,
                    alternate=resource.alternate,
                )
                sig.apply_async()

                # to reduce the work on the FE, the old payload is mantained
                return Response(
                    data={
                        "status": "ready",
                        "execution_id": execution_id,
                        "status_url": urljoin(
                            settings.SITEURL,
                            reverse("rs-execution-status", kwargs={"execution_id": execution_id}),
                        ),
                    },
                    status=200,
                )
        except (Exception, Http404) as e:
            logger.error(e)
            return HttpResponse(status=404, content=e)
        return ResourceBaseViewSet(request=request, format_kwarg=None, args=args, kwargs=kwargs).resource_service_copy(
            request, pk=kwargs.get("pk")
        )
