#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import pyproj
from geonode.upload.publisher import DataPublisher
import json
import logging
from pathlib import Path
from subprocess import PIPE, Popen
from typing import List

from django.conf import settings
from django.db.models import Q
from geonode.base.models import ResourceBase
from geonode.layers.models import Dataset
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.resource.manager import resource_manager
from geonode.resource.models import ExecutionRequest
from geonode.upload.api.exceptions import ImportException
from geonode.upload.celery_tasks import ErrorBaseTaskClass, import_orchestrator
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.geotiff.exceptions import InvalidGeoTiffException
from geonode.upload.handlers.utils import create_alternate, should_be_imported
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.orchestrator import orchestrator
from osgeo import gdal
from geonode.upload.celery_app import importer_app
from geonode.storage.manager import storage_manager

logger = logging.getLogger("importer")


gdal.UseExceptions()


class BaseRasterFileHandler(BaseHandler):
    """
    Handler to import Raster files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    @property
    def default_geometry_column_name(self):
        return "geometry"

    @property
    def supported_file_extension_config(self):
        return NotImplementedError

    @staticmethod
    def get_geoserver_store_name(default=None):
        """
        Method that return the base store name where to save the data in geoserver
        and a boolean to know if the store should be created.
        For raster, the store is created during the geoserver publishing
        so we dont want to created it upfront
        """
        return default, False

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps
        """
        result = Popen("gdal_translate --version", stdout=PIPE, stderr=PIPE, shell=True)
        _, stderr = result.communicate()
        if stderr:
            raise ImportException(stderr)
        return True

    @staticmethod
    def has_serializer(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return False

    @staticmethod
    def can_do(action) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return action in BaseHandler.TASKS

    @staticmethod
    def create_error_log(exc, task_name, *args):
        """
        This function will handle the creation of the log error for each message.
        This is helpful and needed, so each handler can specify the log as needed
        """
        return f"Task: {task_name} raised an error during actions for layer: {args[-1]}: {exc}"

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        if action == exa.COPY.value:
            title = json.loads(_data.get("defaults"))
            return {"title": title.pop("title"), "store_spatial_file": True}, _data

        return {
            "skip_existing_layers": _data.pop("skip_existing_layers", "False"),
            "overwrite_existing_layer": _data.pop("overwrite_existing_layer", False),
            "resource_pk": _data.pop("resource_pk", None),
            "store_spatial_file": _data.pop("store_spatial_files", "True"),
            "action": _data.pop("action", "upload"),
        }, _data

    @staticmethod
    def publish_resources(resources: List[str], catalog, store, workspace):
        """
        Given a list of strings (which rappresent the table on geoserver)
        Will publish the resorces on geoserver
        """
        for _resource in resources:
            try:
                catalog.create_coveragestore(
                    _resource.get("name"),
                    path=_resource.get("raster_path"),
                    layer_name=_resource.get("name"),
                    workspace=workspace,
                    overwrite=True,
                    upload_data=False,
                )
            except Exception as e:
                if f"Resource named {_resource.get('name')} already exists in store:" in str(e):
                    continue
                raise e
        return True

    def pre_validation(self, files, execution_id, **kwargs):
        """
        Hook for let the handler prepare the data before the validation.
        Maybe a file rename, assign the resource to the execution_id
        """

    def overwrite_geoserver_resource(self, resource: List[str], catalog, store, workspace):
        # we need to delete the resource before recreating it
        self._delete_resource(resource, catalog, workspace)
        self._delete_store(resource, catalog, workspace)
        return self.publish_resources([resource], catalog, store, workspace)

    def _delete_store(self, resource, catalog, workspace):
        store = None
        possible_layer_name = [
            resource.get("name"),
            resource.get("name").split(":")[-1],
            f"{workspace.name}:{resource.get('name')}",
        ]
        for el in possible_layer_name:
            store = catalog.get_store(el, workspace=workspace)
            if store:
                break
        if store:
            catalog.delete(store, purge="all", recurse=True)
        return store

    def _delete_resource(self, resource, catalog, workspace):
        res = None
        possible_layer_name = [
            resource.get("name"),
            resource.get("name").split(":")[-1],
            f"{workspace.name}:{resource.get('name')}",
        ]
        for el in possible_layer_name:
            res = catalog.get_resource(el, workspace=workspace)
            if res:
                break
        if res:
            catalog.delete(res, purge="all", recurse=True)

    @staticmethod
    def delete_resource(instance):
        # it should delete the image from the geoserver data dir
        # for now we can rely on the geonode delete behaviour
        # since the file is stored on local
        pass

    @staticmethod
    def perform_last_step(execution_id):
        BaseHandler.perform_last_step(execution_id=execution_id)

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs):
        if action == exa.COPY.value:
            return [
                {
                    "name": alternate,
                    "crs": ResourceBase.objects.filter(
                        Q(alternate__icontains=layer_name) | Q(title__icontains=layer_name)
                    )
                    .first()
                    .srid,
                    "raster_path": kwargs["kwargs"].get("new_file_location").get("files")[0],
                }
            ]

        layers = gdal.Open(files.get("base_file"))
        if not layers:
            return []
        return [
            {
                "name": alternate or layer_name,
                "crs": (self.identify_authority(layers) if layers.GetSpatialRef() else None),
                "raster_path": files.get("base_file"),
            }
        ]

    def identify_authority(self, layer):
        try:
            layer_wkt = layer.GetSpatialRef().ExportToWkt()
            _name = "EPSG"
            _code = pyproj.CRS(layer_wkt).to_epsg(min_confidence=20)
            if _code is None:
                layer_proj4 = layer.GetSpatialRef().ExportToProj4()
                _code = pyproj.CRS(layer_proj4).to_epsg(min_confidence=20)
                if _code is None:
                    raise Exception("CRS authority code not found, fallback to default behaviour")
        except Exception:
            spatial_ref = layer.GetSpatialRef()
            spatial_ref.AutoIdentifyEPSG()
            _name = spatial_ref.GetAuthorityName(None) or spatial_ref.GetAttrValue("AUTHORITY", 0)
            _code = (
                spatial_ref.GetAuthorityCode("PROJCS")
                or spatial_ref.GetAuthorityCode("GEOGCS")
                or spatial_ref.GetAttrValue("AUTHORITY", 1)
            )
        return f"{_name}:{_code}"

    def import_resource(self, files: dict, execution_id: str, **kwargs) -> str:
        """
        Main function to import the resource.
        Internally will call the steps required to import the
        data inside the geonode_data database
        """
        # for the moment we skip the dyanamic model creation
        logger.info("Total number of layers available: 1")
        _exec = self._get_execution_request_object(execution_id)
        _input = {**_exec.input_params, **{"total_layers": 1}}
        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)

        try:
            filename = Path(files.get("base_file")).stem
            # start looping on the layers available
            layer_name = self.fixup_name(filename)

            should_be_overwritten = _exec.input_params.get("overwrite_existing_layer")
            # should_be_imported check if the user+layername already exists or not
            if should_be_imported(
                layer_name,
                _exec.user,
                skip_existing_layer=_exec.input_params.get("skip_existing_layer"),
                overwrite_existing_layer=should_be_overwritten,
            ):
                workspace = DataPublisher(None).workspace
                if _exec.input_params.get("resource_pk"):
                    dataset = Dataset.objects.filter(pk=_exec.input_params.get("resource_pk")).first()
                    if not dataset:
                        raise ImportException("The dataset selected for the ovewrite does not exists")
                    if dataset.is_vector():
                        raise Exception("cannot override a vector dataset with a raster one")
                    alternate = dataset.alternate.split(":")[-1]
                    orchestrator.update_execution_request_obj(_exec, {"geonode_resource": dataset})
                else:
                    user_datasets = Dataset.objects.filter(owner=_exec.user, alternate=f"{workspace.name}:{layer_name}")

                    dataset_exists = user_datasets.exists()

                    if dataset_exists and should_be_overwritten:
                        if user_datasets.is_vector():
                            raise Exception("cannot override a vector dataset with a raster one")
                        layer_name, alternate = (
                            layer_name,
                            user_datasets.first().alternate.split(":")[-1],
                        )
                    elif not dataset_exists:
                        alternate = layer_name
                    else:
                        alternate = create_alternate(layer_name, execution_id)

                import_orchestrator.apply_async(
                    (
                        files,
                        execution_id,
                        str(self),
                        "geonode.upload.import_resource",
                        layer_name,
                        alternate,
                        exa.UPLOAD.value,
                    )
                )
                return layer_name, alternate, execution_id

        except Exception as e:
            logger.error(e)
            raise e
        return

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = Dataset,
        asset=None,
    ):
        """
        Base function to create the resource into geonode. Each handler can specify
        and handle the resource in a different way
        """
        saved_dataset = resource_type.objects.filter(alternate__icontains=alternate)

        _exec = self._get_execution_request_object(execution_id)

        workspace = getattr(
            settings,
            "DEFAULT_WORKSPACE",
            getattr(settings, "CASCADE_WORKSPACE", "geonode"),
        )

        _overwrite = _exec.input_params.get("overwrite_existing_layer", False)
        # if the layer exists, we just update the information of the dataset by
        # let it recreate the catalogue
        if not saved_dataset.exists() and _overwrite:
            logger.warning(
                f"The dataset required {alternate} does not exists, but an overwrite is required, the resource will be created"
            )

        saved_dataset = resource_manager.create(
            None,
            resource_type=resource_type,
            defaults=dict(
                name=alternate,
                workspace=workspace,
                subtype="raster",
                alternate=f"{workspace}:{alternate}",
                dirty_state=True,
                title=layer_name,
                owner=_exec.user,
                asset=asset,
            ),
        )

        saved_dataset.refresh_from_db()

        self.handle_xml_file(saved_dataset, _exec)
        self.handle_sld_file(saved_dataset, _exec)

        resource_manager.set_thumbnail(None, instance=saved_dataset)

        ResourceBase.objects.filter(alternate=alternate).update(dirty_state=False)

        saved_dataset.refresh_from_db()
        return saved_dataset

    def overwrite_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = Dataset,
        asset=None,
    ):

        _exec = self._get_execution_request_object(execution_id)

        dataset = resource_type.objects.filter(alternate__icontains=alternate, owner=_exec.user)

        _overwrite = _exec.input_params.get("overwrite_existing_layer", False)
        # if the layer exists, we just update the information of the dataset by
        # let it recreate the catalogue

        if dataset.exists() and _overwrite:
            dataset = dataset.first()

            dataset = resource_manager.update(dataset.uuid, instance=dataset)

            self.handle_xml_file(dataset, _exec)
            self.handle_sld_file(dataset, _exec)

            resource_manager.set_thumbnail(dataset.uuid, instance=dataset, overwrite=True)
            dataset.refresh_from_db()
            return dataset
        elif not dataset.exists() and _overwrite:
            logger.warning(
                f"The dataset required {alternate} does not exists, but an overwrite is required, the resource will be created"
            )
            return self.create_geonode_resource(layer_name, alternate, execution_id, resource_type, asset)
        elif not dataset.exists() and not _overwrite:
            logger.warning("The resource does not exists, please use 'create_geonode_resource' to create one")
        return

    def handle_xml_file(self, saved_dataset: Dataset, _exec: ExecutionRequest):
        _path = _exec.input_params.get("files", {}).get("xml_file", "")
        resource_manager.update(
            None,
            instance=saved_dataset,
            xml_file=_path,
            metadata_uploaded=True if _path else False,
            vals={"dirty_state": True},
        )

    def handle_sld_file(self, saved_dataset: Dataset, _exec: ExecutionRequest):
        _path = _exec.input_params.get("files", {}).get("sld_file", "")
        resource_manager.exec(
            "set_style",
            None,
            instance=saved_dataset,
            sld_file=_exec.input_params.get("files", {}).get("sld_file", ""),
            sld_uploaded=True if _path else False,
            vals={"dirty_state": True},
        )

    def create_resourcehandlerinfo(
        self,
        handler_module_path: str,
        resource: Dataset,
        execution_id: ExecutionRequest,
        **kwargs,
    ):
        """
        Create relation between the GeonodeResource and the handler used
        to create/copy it
        """
        ResourceHandlerInfo.objects.create(
            handler_module_path=str(handler_module_path),
            resource=resource,
            execution_request=execution_id,
            kwargs=kwargs.get("kwargs", {}),
        )

    def overwrite_resourcehandlerinfo(
        self,
        handler_module_path: str,
        resource: Dataset,
        execution_id: ExecutionRequest,
        **kwargs,
    ):
        """
        Overwrite the ResourceHandlerInfo
        """
        if resource.resourcehandlerinfo_set.exists():
            resource.resourcehandlerinfo_set.update(
                handler_module_path=handler_module_path,
                resource=resource,
                execution_request=execution_id,
                kwargs=kwargs.get("kwargs", {}) or kwargs,
            )
            return
        return self.create_resourcehandlerinfo(handler_module_path, resource, execution_id, **kwargs)

    def copy_geonode_resource(
        self,
        alternate: str,
        resource: Dataset,
        _exec: ExecutionRequest,
        data_to_update: dict,
        new_alternate: str,
        **kwargs,
    ):
        resource = self.create_geonode_resource(
            layer_name=data_to_update.get("title"),
            alternate=new_alternate,
            execution_id=str(_exec.exec_id),
            asset=kwargs.get("kwargs", {}).get("new_file_location", {}).get("asset", []),
        )
        resource.refresh_from_db()
        return resource

    def _get_execution_request_object(self, execution_id: str):
        return ExecutionRequest.objects.filter(exec_id=execution_id).first()

    @staticmethod
    def copy_original_file(dataset):
        """
        Copy the original file into a new location
        """
        return storage_manager.copy(dataset)

    def _import_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        """
        In the raster, this step just generate the alternate, no real action
        are done on the database
        """
        pass

    def _publish_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        """
        We delete the resource from geoserver
        """
        logger.info(
            f"Rollback publishing step in progress for execid: {exec_id} resource published was: {istance_name}"
        )
        exec_object = orchestrator.get_execution_object(exec_id)
        handler_module_path = exec_object.input_params.get("handler_module_path")
        publisher = DataPublisher(handler_module_path=handler_module_path)
        publisher.delete_resource(istance_name)


@importer_app.task(
    base=ErrorBaseTaskClass,
    name="geonode.upload.copy_raster_file",
    queue="geonode.upload.copy_raster_file",
    max_retries=1,
    acks_late=False,
    ignore_result=False,
    task_track_started=True,
)
def copy_raster_file(exec_id, actual_step, layer_name, alternate, handler_module_path, action, **kwargs):
    """
    Perform a copy of the original raster file"""

    original_dataset = ResourceBase.objects.filter(alternate=alternate)
    if not original_dataset.exists():
        raise InvalidGeoTiffException("Dataset required does not exists")

    original_dataset = original_dataset.first()

    if not original_dataset.files:
        raise InvalidGeoTiffException(
            "The original file of the dataset is not available, Is not possible to copy the dataset"
        )

    new_file_location = orchestrator.load_handler(handler_module_path).copy_original_file(original_dataset)

    new_dataset_alternate = create_alternate(original_dataset.title, exec_id)

    additional_kwargs = {
        "original_dataset_alternate": original_dataset.alternate,
        "new_dataset_alternate": new_dataset_alternate,
        "new_file_location": new_file_location,
    }

    task_params = (
        {},
        exec_id,
        handler_module_path,
        actual_step,
        layer_name,
        new_dataset_alternate,
        action,
    )

    import_orchestrator.apply_async(task_params, additional_kwargs)

    return "copy_raster", layer_name, alternate, exec_id
