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
import ast
import csv
import re
from datetime import datetime
from itertools import islice
from pathlib import Path
import shutil
import tempfile
from django.db import connections
from geonode.security.permissions import _to_compact_perms
from geonode.storage.manager import StorageManager
from geonode.upload.publisher import DataPublisher
from geonode.upload.utils import DEFAULT_PK_COLUMN_NAME, call_rollback_function
import json
import logging
import os
from subprocess import PIPE, Popen
from typing import List, Optional, Tuple
from celery import chord, group
from django.db import transaction

from django.conf import settings
from dynamic_models.models import ModelSchema
from dynamic_models.schema import ModelSchemaEditor
from geonode.base.models import ResourceBase
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.layers.models import Dataset
from geonode.upload.celery_tasks import (
    ErrorBaseTaskClass,
    FieldSchema,
    create_dynamic_structure,
    UpdateDynamicTaskClass,
)
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.utils import (
    GEOM_TYPE_MAPPING,
    STANDARD_TYPE_MAPPING,
    drop_dynamic_model_schema,
    create_layer_key,
)
from geonode.resource.manager import resource_manager
from geonode.resource.models import ExecutionRequest
from osgeo import ogr
from geonode.upload.api.exceptions import ImportException, UpsertException
from geonode.upload.celery_app import importer_app
from geonode.assets.utils import copy_assets_and_links, get_default_asset

from geonode.upload.handlers.utils import create_alternate, should_be_imported
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.orchestrator import orchestrator
from django.db.models import Q

import pyproj
from geonode.geoserver.security import delete_dataset_cache, set_geowebcache_invalidate_cache
from geonode.geoserver.helpers import get_time_info
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.security.registry import permissions_registry
from geonode.storage.manager import FileSystemStorageManager
from geonode.upload.utils import create_vrt_file, has_incompatible_field_names
from geonode.upload.registry import feature_validators_registry
from django.core.exceptions import ValidationError


logger = logging.getLogger("importer")


class BaseVectorFileHandler(BaseHandler):
    """
    Handler to import Vector files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_dynamic_model",
            "geonode.upload.copy_geonode_data_table",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
        ira.REPLACE.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
        ira.UPSERT.value: ("start_import", "geonode.upload.upsert_data", "geonode.upload.refresh_geonode_resource"),
    }

    @property
    def have_table(self):
        return True

    @property
    def default_geometry_column_name(self):
        return "geom"

    @property
    def supported_file_extension_config(self):
        return NotImplementedError

    @staticmethod
    def get_geoserver_store_name(default=None):
        """
        Method that return the base store name where to save the data in geoserver
        and a boolean to know if the store should be created.
        For vector, the store must be created
        """
        return os.environ.get("GEONODE_GEODATABASE", "geonode_data"), True

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps
        """
        result = Popen("ogr2ogr --version", stdout=PIPE, stderr=PIPE, shell=True)
        _, stderr = result.communicate()
        if stderr:
            raise ImportException(stderr)
        return True

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if _data.get("action", None) not in BaseVectorFileHandler.TASKS:
            return False
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
        return action in BaseVectorFileHandler.TASKS

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
            "upsert_key": _data.pop("upsert_key", None),
        }, _data

    @staticmethod
    def publish_resources(resources: List[str], catalog, store, workspace):
        """
        Given a list of strings (which rappresent the table on geoserver)
        Will publish the resorces on geoserver
        """
        for _resource in resources:
            try:
                catalog.publish_featuretype(
                    name=_resource.get("name"),
                    store=store,
                    native_crs=_resource.get("crs"),
                    srs=_resource.get("crs"),
                    jdbc_virtual_table=_resource.get("name"),
                )
            except Exception as e:
                if f"Resource named {_resource} already exists in store:" in str(e):
                    logger.error(f"error during publishing: {e}")
                    continue
                logger.error(f"error during publishing: {e}")
                raise e
        return True

    def pre_validation(self, files, execution_id, **kwargs):
        """
        Hook for let the handler prepare the data before the validation.
        Maybe a file rename, assign the resource to the execution_id
        """

    def overwrite_geoserver_resource(self, resource, catalog, store, workspace):
        """
        We dont need to do anything for now.
        The data is replaced via ogr2ogr
        """
        self._delete_resource(resource, catalog, workspace)
        return self.publish_resources([resource], catalog, store, workspace)

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
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate, **kwargs):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """
        _datastore = settings.DATABASES["datastore"]
        layers = ogr.Open(files.get("base_file"))
        layer = layers.GetLayer(original_name)

        options = "--config PG_USE_COPY YES"
        copy_with_dump = ast.literal_eval(os.getenv("OGR2OGR_COPY_WITH_DUMP", "False"))

        if copy_with_dump:
            # use PGDump to load the dataset with ogr2ogr
            options += " -f PGDump /vsistdout/ "
        else:
            # default option with postgres copy
            options += " -f PostgreSQL PG:\" dbname='%s' host=%s port=%s user='%s' password='%s' \" " % (
                _datastore["NAME"],
                _datastore["HOST"],
                _datastore.get("PORT", 5432),
                _datastore["USER"],
                _datastore["PASSWORD"],
            )
        # vrt file is aready created in import_resource and vrt will be auto detected by ogr2ogr
        # and also the base_file will work so can be used as alternative for fallback which will also be autodeteced by ogr2ogr.
        input_file = files.get("temp_vrt_file") or files.get("base_file")
        options += f'"{input_file}"' + f" -lco FID={DEFAULT_PK_COLUMN_NAME} "

        options += f'-nln {alternate} "{original_name}"'

        if layer is not None and "Point" not in ogr.GeometryTypeToName(layer.GetGeomType()):
            options += " -nlt PROMOTE_TO_MULTI"

        if ovverwrite_layer:
            options += " -overwrite"

        return options

    @staticmethod
    def copy_table_with_ogr2ogr(original_table_name: str, new_table_name: str, db_name: Optional[str] = None):
        """
        Copies a old existing table to new table using ogr2ogr.
        """
        db_name = db_name or os.getenv("DEFAULT_BACKEND_DATASTORE", "datastore")
        _datastore = settings.DATABASES[db_name]
        db_connection_string = (
            f"PG:host={_datastore['HOST']} dbname={_datastore['NAME']} "
            f"user={_datastore['USER']} password={_datastore['PASSWORD']} "
            f"port={_datastore.get('PORT', 5432)}"
        )

        ogr_exe = shutil.which("ogr2ogr")
        if not ogr_exe:
            raise Exception("ogr2ogr executable not found.")

        command = [
            ogr_exe,
            "-f",
            "PostgreSQL",
            db_connection_string,
            db_connection_string,
            "-nln",
            new_table_name,
            original_table_name,
            "-overwrite",
        ]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if (
            stderr is not None
            and stderr != b""
            and b"ERROR" in stderr
            and b"error" in stderr
            or b"Syntax error" in stderr
        ):
            try:
                err = stderr.decode()
            except Exception:
                err = stderr.decode("latin1")
            logger.error(f"Original error returned: {err}")
            message = normalize_ogr2ogr_error(err, original_table_name)
            raise Exception(f"ogr2ogr command failed with error: {message}")

    @staticmethod
    def delete_resource(instance):
        """
        Base function to delete the resource with all the dependencies (dynamic model)
        """
        try:
            name = instance.alternate.split(":")[1]
            schema = None
            if settings.IMPORTER_ENABLE_DYN_MODELS:
                schema = ModelSchema.objects.filter(name=name).first()
            if schema:
                """
                We use the schema editor directly, because the model itself is not managed
                on creation, but for the delete since we are going to handle, we can use it
                """
                try:
                    _model_editor = ModelSchemaEditor(initial_model=name, db_name=schema.db_name)
                    _model_editor.drop_table(schema.as_model())
                except Exception as e:
                    logger.info(f"database table already deleted: {e}")
                    pass
                ModelSchema.objects.filter(name=name).delete()
        except Exception as e:
            logger.error(f"Error during deletion of Dynamic Model schema: {e.args[0]}")

    @staticmethod
    def perform_last_step(execution_id):
        """
        Override this method if there is some extra step to perform
        before considering the execution as completed.
        For example can be used to trigger an email-send to notify
        that the execution is completed
        """
        _exec = BaseHandler.perform_last_step(execution_id=execution_id)
        if _exec and not _exec.input_params.get("store_spatial_file", True):
            resources = ResourceHandlerInfo.objects.filter(execution_request=_exec)
            # getting all assets list
            assets = filter(None, [get_default_asset(x.resource) for x in resources])
            # we need to loop and cancel one by one to activate the signal
            # that delete the file from the filesystem
            for asset in assets:
                asset.delete()

        tmp_data = _exec.input_params.get("temporary_files")
        if tmp_data:
            # Delete at the end of the operations, the temporary files created at the beginning
            # to cleanup disk space
            storage_manager = StorageManager(
                remote_files={},
                concrete_storage_manager=FileSystemStorageManager(),
            )
            base_file_path = tmp_data.get("base_file")
            if base_file_path:
                directory = os.path.dirname(base_file_path)
                if settings.ASSETS_ROOT not in directory:
                    storage_manager.rmtree(directory, ignore_errors=True)

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
                }
            ]

        layers = self.get_ogr2ogr_driver().Open(files.get("base_file"))
        if not layers:
            return []
        return [
            {
                "name": alternate or layer_name,
                "crs": self.identify_authority(_l) if _l.GetSpatialRef() else None,
            }
            for _l in layers
            if self.fixup_name(_l.GetName()) == layer_name
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

    def get_ogr2ogr_driver(self):
        """
        Should return the Driver object that is used to open the layers via OGR2OGR
        """
        return None

    def import_resource(self, files: dict, execution_id: str, **kwargs) -> str:
        """
        Main function to import the resource.
        Internally will call the steps required to import the
        data inside the geonode_data database
        """
        all_layers = self.get_ogr2ogr_driver().Open(files.get("base_file"))
        layers = self._select_valid_layers(all_layers)
        # for the moment we skip the dyanamic model creation
        layer_count = len(layers)
        logger.info(f"Total number of layers available: {layer_count}")
        _exec = self._get_execution_request_object(execution_id)
        _input = {**_exec.input_params, **{"total_layers": layer_count}}
        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)
        dynamic_model = None
        celery_group = None
        # list to collect all the alternates:
        layer_names = []
        alternates = []
        task_name = "geonode.upload.import_resource"

        try:
            if len(layers) == 0:
                raise Exception("No valid layers found")

            # start looping on the layers available

            for index, layer in enumerate(layers, start=1):
                layer_name = self.fixup_name(layer.GetName())

                should_be_overwritten = _exec.input_params.get("overwrite_existing_layer")
                # should_be_imported check if the user+layername already exists or not
                if (
                    should_be_imported(
                        layer_name,
                        _exec.user,
                        skip_existing_layer=_exec.input_params.get("skip_existing_layer"),
                        overwrite_existing_layer=should_be_overwritten,
                    )
                    # and layer.GetGeometryColumn() is not None
                ):
                    _files = files.copy()
                    vrt_layer_name = None
                    if has_incompatible_field_names(layer):
                        vrt_filename, vrt_layer_name = create_vrt_file(layer, files.get("base_file"))
                        _files["temp_vrt_file"] = vrt_filename

                    # update the execution request object
                    # setup dynamic model and retrieve the group task needed for tun the async workflow
                    # create the async task for create the resource into geonode_data with ogr2ogr
                    if settings.IMPORTER_ENABLE_DYN_MODELS:
                        (
                            dynamic_model,
                            alternate,
                            celery_group,
                        ) = self.setup_dynamic_model(
                            layer,
                            execution_id,
                            should_be_overwritten,
                            username=_exec.user,
                        )
                    else:
                        alternate = self.find_alternate_by_dataset(_exec, layer_name, should_be_overwritten)

                    layer_names.append(layer_name)
                    alternates.append(alternate)

                    ogr_res = self.get_ogr2ogr_task_group(
                        execution_id,
                        _files,
                        vrt_layer_name or layer.GetName().lower(),
                        should_be_overwritten,
                        alternate,
                    )

                    if settings.IMPORTER_ENABLE_DYN_MODELS:
                        group_to_call = group(
                            celery_group.set(link_error=["dynamic_model_error_callback"]),
                            ogr_res.set(link_error=["dynamic_model_error_callback"]),
                        )
                    else:
                        group_to_call = group(
                            ogr_res.set(link_error=["dynamic_model_error_callback"]),
                        )

                    # prepare the async chord workflow with the on_success and on_fail methods
                    workflow = chord(group_to_call)(  # noqa
                        import_next_step.s(
                            execution_id,
                            str(self),  # passing the handler module path
                            task_name,
                            layer_name,
                            alternate,
                            **kwargs,
                        )
                    )

        except Exception as e:
            logger.error(e)
            if dynamic_model:
                """
                In case of fail, we want to delete the dynamic_model schema and his field
                to keep the DB in a consistent state
                """
                drop_dynamic_model_schema(dynamic_model)
            raise e
        return layer_names, alternates, execution_id

    def _select_valid_layers(self, all_layers):
        layers = []
        for layer in all_layers:
            try:
                self.identify_authority(layer)
                layers.append(layer)
            except Exception as e:
                logger.error(e)
                logger.error(
                    f"The following layer {layer.GetName()} does not have a Coordinate Reference System (CRS) and will be skipped."
                )
                pass
        return layers

    def find_alternate_by_dataset(self, _exec_obj, layer_name, should_be_overwritten):
        if _exec_obj.input_params.get("resource_pk"):
            dataset = Dataset.objects.filter(pk=_exec_obj.input_params.get("resource_pk")).first()
            if not dataset:
                raise ImportException("The dataset selected for the ovewrite does not exists")
            if should_be_overwritten:
                if not dataset.is_vector():
                    raise Exception("Cannot override a raster dataset with a vector one")
            alternate = dataset.alternate.split(":")
            return alternate[-1]

        workspace = DataPublisher(None).workspace
        dataset_available = Dataset.objects.filter(alternate__iexact=f"{workspace.name}:{layer_name}")

        dataset_exists = dataset_available.exists()
        if should_be_overwritten:
            if not dataset_available.is_vector():
                raise Exception("Cannot override a raster dataset with a vector one")

        if dataset_exists and should_be_overwritten:
            alternate = dataset_available.first().alternate.split(":")[-1]
        elif not dataset_exists:
            alternate = layer_name
        else:
            alternate = create_alternate(layer_name, str(_exec_obj.exec_id))

        return alternate

    def setup_dynamic_model(
        self,
        layer: ogr.Layer,
        execution_id: str,
        should_be_overwritten: bool,
        username: str,
    ):
        """
        Extract from the geopackage the layers name and their schema
        after the extraction define the dynamic model instances
        Returns:
            - dynamic_model as model, so the actual dynamic instance
            - alternate -> the alternate of the resource which contains (if needed) the uuid
            - celery_group -> the celery group of the field creation
        """

        layer_name = self.fixup_name(layer.GetName() if isinstance(layer, ogr.Layer) else layer)
        _exec_obj = orchestrator.get_execution_object(execution_id)

        is_dynamic_model_managed = _exec_obj.input_params.get("is_dynamic_model_managed", False)
        workspace = DataPublisher(None).workspace
        if resource_pk := _exec_obj.input_params.get("resource_pk", None):
            user_datasets = Dataset.objects.filter(owner=username, pk=resource_pk)
            user_dataset = user_datasets.first()
            if user_dataset:
                dynamic_schema = ModelSchema.objects.filter(name__iexact=user_dataset.name)
            else:
                dynamic_schema = ModelSchema.objects.none()
        else:
            user_datasets = Dataset.objects.filter(owner=username, alternate__iexact=f"{workspace.name}:{layer_name}")
            dynamic_schema = ModelSchema.objects.filter(name__iexact=layer_name)

        dynamic_schema_exists = dynamic_schema.exists()
        dataset_exists = user_datasets.exists()

        if dataset_exists and dynamic_schema_exists and should_be_overwritten:
            """
            If the user have a dataset, the dynamic model has already been created and is in overwrite mode,
            we just take the dynamic_model to overwrite the existing one
            """
            dynamic_schema = dynamic_schema.get()
            layer_name = user_datasets.first().alternate.split(":")[-1]
        elif not dataset_exists and not dynamic_schema_exists:
            """
            cames here when is a new brand upload or when (for any reasons) the dataset exists but the
            dynamic model has not been created before
            """
            #  layer_name = create_alternate(layer_name, execution_id)
            dynamic_schema = ModelSchema.objects.create(
                name=layer_name,
                db_name="datastore",
                managed=is_dynamic_model_managed,
                db_table_name=layer_name,
            )
        elif (
            (not dataset_exists and dynamic_schema_exists)
            or (dataset_exists and dynamic_schema_exists and not should_be_overwritten)
            or (dataset_exists and not dynamic_schema_exists)
        ):
            """
            it comes here when the layer should not be overrided so we append the UUID
            to the layer to let it proceed to the next steps
            """
            layer_name = create_alternate(layer_name, execution_id)
            dynamic_schema, _ = ModelSchema.objects.get_or_create(
                name=layer_name,
                db_name="datastore",
                managed=is_dynamic_model_managed,
                db_table_name=layer_name,
            )
        else:
            raise ImportException("Error during the upload of the gpkg file. The dataset does not exists")

        # define standard field mapping from ogr to django
        dynamic_model, celery_group = self.create_dynamic_model_fields(
            layer=layer,
            dynamic_model_schema=dynamic_schema,
            overwrite=should_be_overwritten,
            execution_id=execution_id,
            layer_name=layer_name,
        )
        return dynamic_model, layer_name, celery_group

    def create_dynamic_model_fields(
        self,
        layer: str,
        dynamic_model_schema: ModelSchema = None,
        overwrite: bool = None,
        execution_id: str = None,
        layer_name: str = None,
        return_celery_group: bool = True,
    ):
        # retrieving the field schema from ogr2ogr and converting the type to Django Types

        layer_schema = self._define_dynamic_layer_schema(layer, execution_id=execution_id)

        if not return_celery_group:
            return layer_schema

        # ones we have the schema, here we create a list of chunked value
        # so the async task will handle max of 30 field per task
        list_chunked = [layer_schema[i : i + 30] for i in range(0, len(layer_schema), 30)]  # noqa

        # definition of the celery group needed to run the async workflow.
        # in this way each task of the group will handle only 30 field
        layer_name = layer.GetName() if not isinstance(layer, str) else layer_name
        celery_group = group(
            create_dynamic_structure.s(
                execution_id,
                schema,
                dynamic_model_schema.id,
                overwrite,
                layer_name,
                layer_key=create_layer_key(layer_name, str(execution_id)),
            )
            for schema in list_chunked
        )

        return dynamic_model_schema, celery_group

    def _define_dynamic_layer_schema(self, layer, **kwargs):
        layer_schema = [
            {"name": self.fixup_name(x.name), "class_name": self._get_type(x), "null": True} for x in layer.schema
        ]
        if (
            layer.GetGeometryColumn()
            or self.default_geometry_column_name
            and ogr.GeometryTypeToName(layer.GetGeomType()) not in ["Geometry Collection", "Unknown (any)", "None"]
        ):
            # the geometry colum is not returned rom the layer.schema, so we need to extract it manually
            layer_schema += [
                {
                    "name": layer.GetGeometryColumn() or self.default_geometry_column_name,
                    "class_name": GEOM_TYPE_MAPPING.get(
                        self.promote_to_multi(ogr.GeometryTypeToName(layer.GetGeomType()))
                    ),
                    "dim": (2 if not ogr.GeometryTypeToName(layer.GetGeomType()).lower().startswith("3d") else 3),
                    "authority": self.identify_authority(layer),
                }
            ]

        return layer_schema

    def promote_to_multi(self, geometry_name):
        """
        If needed change the name of the geometry, by promoting it to Multi
        example if is Point -> MultiPoint
        Needed for the shapefiles
        Later this is used to map the geometry coming from ogr2ogr with a django class
        """
        if "Multi" not in geometry_name and "Point" not in geometry_name and "3D" not in geometry_name:
            return f"Multi {geometry_name.title()}"
        return geometry_name

    def promote_geom_to_multi(self, geom):
        """
        Convert the GetGeometryType object into Multi
        example if is Point -> MultiPoint
        Needed for the shapefiles
        """
        match geom.GetGeometryType():
            case ogr.wkbMultiLineString | ogr.wkbMultiPolygon:
                # if is already multi, we dont need to do anything
                return geom
            case ogr.wkbLineString:
                new_multi_geom = ogr.Geometry(ogr.wkbMultiLineString)
                new_multi_geom.AddGeometry(geom)
                return new_multi_geom
            case ogr.wkbPolygon:
                new_multi_geom = ogr.Geometry(ogr.wkbMultiPolygon)
                new_multi_geom.AddGeometry(geom)
                return new_multi_geom
            case _:
                # we dont convert points
                return geom

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
            defaults=self.generate_resource_payload(layer_name, alternate, asset, _exec, workspace),
        )

        saved_dataset.refresh_from_db()

        self.handle_xml_file(saved_dataset, _exec)
        self.handle_sld_file(saved_dataset, _exec)
        self.handle_thumbnail(saved_dataset, _exec)

        ResourceBase.objects.filter(alternate=alternate).update(dirty_state=False)

        saved_dataset.refresh_from_db()

        self.__fixup_primary_key(saved_dataset)

        return saved_dataset

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace):
        return dict(
            name=alternate,
            workspace=workspace,
            store=os.environ.get("GEONODE_GEODATABASE", "geonode_data"),
            subtype="vector",
            alternate=f"{workspace}:{alternate}",
            dirty_state=True,
            title=layer_name,
            owner=_exec.user,
            asset=asset,
        )

    def overwrite_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = Dataset,
        asset=None,
    ):
        _exec = self._get_execution_request_object(execution_id)

        dataset = resource_type.objects.filter(pk=_exec.input_params.get("resource_pk"), owner=_exec.user)

        _overwrite = _exec.input_params.get("overwrite_existing_layer", False)
        # if the layer exists, we just update the information of the dataset by
        # let it recreate the catalogue
        if dataset.exists() and _overwrite:
            dataset = dataset.first()

            dataset = self.refresh_geonode_resource(str(_exec.exec_id), asset, dataset, create_asset=False)
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

    def handle_thumbnail(self, saved_dataset: Dataset, _exec: ExecutionRequest):
        resource_manager.set_thumbnail(None, instance=saved_dataset)

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
            handler_module_path=handler_module_path,
            resource=resource,
            execution_request=execution_id,
            kwargs=kwargs.get("kwargs", {}) or kwargs,
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

        new_resource = self.create_geonode_resource(
            layer_name=data_to_update.get("title"),
            alternate=new_alternate,
            execution_id=str(_exec.exec_id),
        )

        copy_assets_and_links(resource, target=new_resource)

        if resource.dataset.has_time is True:

            new_resource.has_time = True
            new_resource.save()

            time_info = None
            try:
                time_info = get_time_info(resource.dataset)
            except ValueError as e:
                logger.info(f"Failed to retrieve time information: {e}")

            time_info["attribute"] = (
                resource.dataset.attributes.get(pk=time_info.get("attribute")).attribute
                if time_info.get("attribute")
                else None
            )
            time_info["end_attribute"] = (
                resource.dataset.attributes.get(pk=time_info.get("end_attribute")).attribute
                if time_info.get("end_attribute")
                else None
            )

            resource_manager.exec(
                "set_time_info",
                None,
                instance=new_resource,
                time_info=time_info,
            )

        new_resource.refresh_from_db()

        return new_resource

    def get_ogr2ogr_task_group(
        self,
        execution_id: str,
        files: dict,
        layer,
        should_be_overwritten: bool,
        alternate: str,
    ):
        """
        In case the OGR2OGR is different from the default one, is enough to ovverride this method
        and return the celery task object needed
        """
        handler_module_path = str(self)
        return import_with_ogr2ogr.s(
            execution_id,
            files,
            layer.lower(),
            handler_module_path,
            should_be_overwritten,
            alternate,
            layer_key=create_layer_key(layer.lower(), str(execution_id)),
        )

    def _get_execution_request_object(self, execution_id: str):
        return ExecutionRequest.objects.filter(exec_id=execution_id).first()

    def _get_type(self, _type: str):
        """
        Used to get the standard field type in the dynamic_model_field definition
        """
        return STANDARD_TYPE_MAPPING.get(ogr.FieldDefn.GetTypeName(_type))

    def _import_resource_rollback(self, exec_id, instance_name=None, *args, **kwargs):
        """
        We use the schema editor directly, because the model itself is not managed
        on creation, but for the delete since we are going to handle, we can use it
        """
        logger.info(
            f"Rollback dynamic model & ogr2ogr step in progress for execid: {exec_id} resource published was: {instance_name}"
        )
        schema = None
        if settings.IMPORTER_ENABLE_DYN_MODELS:
            schema = ModelSchema.objects.filter(name=instance_name).first()
        if schema is not None:
            _model_editor = ModelSchemaEditor(initial_model=instance_name, db_name=schema.db_name)
            _model_editor.drop_table(schema.as_model())
            ModelSchema.objects.filter(name=instance_name).delete()
        elif schema is None:
            try:
                logger.warning("Dynamic model does not exists, removing ogr2ogr table in progress")
                if instance_name is None:
                    logger.warning("No table created, skipping...")
                    return
                db_name = os.getenv("DEFAULT_BACKEND_DATASTORE", "datastore")
                with connections[db_name].cursor() as cursor:
                    cursor.execute(f"DROP TABLE {instance_name}")
            except Exception as e:
                logger.warning(e)
                pass

    def _publish_resource_rollback(self, exec_id, instance_name=None, *args, **kwargs):
        """
        We delete the resource from geoserver
        """
        logger.info(
            f"Rollback publishing step in progress for execid: {exec_id} resource published was: {instance_name}"
        )
        exec_object = orchestrator.get_execution_object(exec_id)
        handler_module_path = exec_object.input_params.get("handler_module_path")
        publisher = DataPublisher(handler_module_path=handler_module_path)
        publisher.delete_resource(instance_name)

    def upsert_validation(self, files, execution_id, **kwargs: dict) -> Tuple[bool, Optional[str]]:
        """
        Perform the validation step to ensure that the file provided is valid
        to perform an upsert on the selected dataset.
            - Load the dynamic model for the selected dataset
            - User ogr2ogr to read the schema of the uploaded file
            - will evaluate if the field are coherent (int -> int = valid, int -> date = invalid)
        return True/False, if false, also the reason why is not valid
        """
        # if the dynamic_models is not enabled or the target schema does not exists, we cannot perform the upser
        if not settings.IMPORTER_ENABLE_DYN_MODELS:
            raise UpsertException(
                "The Dynamic model generation must be enabled to perform the upsert IMPORTER_ENABLE_DYN_MODELS=True"
            )
        # evaluate if the user can perform the operation on the selected resource

        exec_obj = orchestrator.get_execution_object(exec_id=execution_id)

        perms = _to_compact_perms(
            permissions_registry.get_perms(
                instance=ResourceBase.objects.filter(pk=exec_obj.input_params.get("resource_pk")).first(),
                user=exec_obj.user,
            )
        )
        if "manage" in perms or "edit" in perms:
            errors = []
            # getting the saved schema and convert the newly uploaded file into the same object
            target_schema_fields, new_file_schema_fields = self.__get_new_and_original_schema(files, execution_id)
            # let's check that the field in the uploaded file are coherent with the one preset
            # loop on all the new field coming from the uploaded file
            target_schema_as_list = [x for x in target_schema_fields.values_list("name", flat=True)]
            new_file_schema_fields_as_list = [x["name"] for x in new_file_schema_fields]
            differeces = list(set(target_schema_as_list) - set(new_file_schema_fields_as_list))
            if any(differeces):
                raise UpsertException(
                    f"The columns in the source and target do not match they must be equal. The following are not expected or missing: {differeces}"
                )
            skip_geom_eval = False
            for field in new_file_schema_fields:
                # check if the field exists in the previous schema
                target_field = target_schema_fields.filter(name=field["name"]).first()
                if target_field:
                    # if is the primary key, we can skip the check
                    # If the field exists the class name should be the same
                    if "authority" in field and not skip_geom_eval:
                        if db_value := target_field.model_schema.as_model().objects.first():
                            skip_geom_eval = True
                            if not str(db_value.geom.srid) in field["authority"]:
                                message = f"The file provided have a different authority ({field['authority']}) compared to the one in the DB: {db_value}"
                                raise UpsertException(message)

                    if not target_field.class_name == field["class_name"] and not target_field.kwargs.get(
                        "primary_key"
                    ):
                        # if the class changes, is marked as error
                        message = f"The type of the following field is changed and is prohibited: field: {field['name']}| current: {target_field.class_name}| new: {field['class_name']}"
                        errors.append(message)
                        logger.error(message)

            return not errors, errors
        else:
            raise UpsertException(
                "User does not have enough permissions to perform this action on the selected resource"
            )

    def __get_new_and_original_schema(self, files, execution_id):
        # check if the execution_id is passed and if the geonode resource exists
        exec_id = orchestrator.get_execution_object(execution_id)
        target_resource = ResourceBase.objects.filter(pk=exec_id.input_params.get("resource_pk")).first()
        if not target_resource:
            raise UpsertException(
                "Target dynamic models does not exists. Please re-upload the resource with IMPORTER_ENABLE_DYN_MODELS=True to generate the schema"
            )
        # retrieve the current schema for the resource
        target_schema_fields = FieldSchema.objects.filter(model_schema__name=target_resource.alternate.split(":")[-1])

        # use ogr2ogr to read the uploaded files for the upsert
        all_layers = self.get_ogr2ogr_driver().Open(files.get("base_file"))
        layers = self._select_valid_layers(all_layers)
        if not layers:
            raise UpsertException("No valid layers found in the provided file for upsert.")

        layer = layers[0]
        # evaluate if some of the fid entry is null. if is null we stop the workflow
        # the user should provide the completed list with the fid set
        sql_query = f'SELECT * FROM "{layer.GetName()}" WHERE "{DEFAULT_PK_COLUMN_NAME}" IS NULL'

        # Execute the SQL query to the layer
        result = all_layers.ExecuteSQL(sql_query)
        if not result or (result and result.GetFeatureCount() > 0):
            raise UpsertException(
                f"All the feature in the file must have the fid field correctly populated. Number of None value: {result.GetFeatureCount() if result else 'all'}"
            )

        # Will generate the same schema as the target_resource_schema
        new_file_schema_fields = self.create_dynamic_model_fields(
            layer,
            return_celery_group=False,
        )

        return target_schema_fields, new_file_schema_fields

    def __fixup_primary_key(self, saved_dataset):

        # if dynamic model is enabled, we can save up with is the primary key of the table
        if settings.IMPORTER_ENABLE_DYN_MODELS and self.have_table:
            from django.db import connections

            # then we can check for the PK
            column = None
            connection = connections["datastore"]
            table_name = saved_dataset.alternate.split(":")[1]

            schema = ModelSchema.objects.filter(name=table_name).first()
            if schema:
                schema.managed = False
                schema.save()

            with connection.cursor() as cursor:
                column = connection.introspection.get_primary_key_columns(cursor, table_name)
            if column:
                # getting the relative model schema
                # better to always ensure that the schema is NOT managed
                field = FieldSchema.objects.filter(name=column[0], model_schema__name=table_name).first()
                if field:
                    field.kwargs.update({"primary_key": True})
                    field.save()
                else:
                    # creating the field needed as primary key
                    pk_field = FieldSchema(
                        name=column[0],
                        model_schema=schema,
                        class_name="django.db.models.BigAutoField",
                        kwargs={"null": False, "primary_key": True},
                    )
                    pk_field.save()

    def upsert_data(self, files, execution_id, **kwargs):
        """
        Function used to upsert the data for a vector resource.
        The function will:
            - loop on all the values in the new uploaded file
            - if the upsert key exists, is marked as 'to update'
            - if the upsert key does not exists, is maked as 'to insert'
        Before saving the resources, an update of the schema is mandatory
            - the new column are added as nullable to keep the retrocompatibility
            - The pre-existing columns are NOT deleted
        """

        # getting execution_id information
        exec_obj = orchestrator.get_execution_object(execution_id)

        # getting the related model schema for the resource
        original_resource, model = self.___get_dynamic_schema(exec_obj)
        if not model:
            raise UpsertException(
                "This dataset does't support updates. Please upload the dataset again to have the upsert operations enabled"
            )

        # get the rows that match the upsert key
        OriginalResource = model.as_model()

        # retrieve the upsert key.
        upsert_key = self.extract_upsert_key(exec_obj, dynamic_model_instance=model)
        if not upsert_key:
            # if for any reason the key is not present, better to raise an error
            raise UpsertException("Was not possible to find the upsert key, upsert is aborted")
        # use ogr2ogr to read the uploaded files values for the upsert
        all_layers = self.get_ogr2ogr_driver().Open(files.get("base_file"))
        valid_create = 0
        valid_update = 0
        layers = self._select_valid_layers(all_layers)
        if not layers:
            raise UpsertException("No valid layers were found in the file provided")
        # we can upsert just 1 layer at time

        self._validate_single_feature(exec_obj, OriginalResource, upsert_key, layers, iter(layers[0]))

        valid_create, valid_update = self._commit_upsert(model, OriginalResource, upsert_key, iter(layers[0]))

        self.create_resourcehandlerinfo(
            handler_module_path=str(self), resource=original_resource, execution_id=exec_obj
        )

        return {
            "success": True,
            "data": {
                "total": valid_update + valid_create,
                "update": valid_update,
                "create": valid_create,
            },
            "layer_name": original_resource.title,
        }

    def ___get_dynamic_schema(self, exec_obj):
        original_resource = ResourceBase.objects.filter(pk=exec_obj.input_params.get("resource_pk")).first()
        self.real_instance = original_resource.get_real_instance()
        model = ModelSchema.objects.filter(name=original_resource.alternate.split(":")[-1]).first()
        return original_resource, model

    def _commit_upsert(self, model_obj, OriginalResource, upsert_key, layer_iterator):
        valid_create = 0
        valid_update = 0
        with transaction.atomic():
            try:
                while True:
                    # Create an iterator for the next chunk
                    data_chunk = list(islice(layer_iterator, settings.UPSERT_CHUNK_SIZE))

                    # If the chunk is empty, we've reached the end of the layer
                    if not data_chunk:
                        break

                    valid_update, valid_create = self._save_feature(
                        data_chunk,
                        model_obj=model_obj,
                        model_instance=OriginalResource,
                        upsert_key=upsert_key,
                        valid_update=valid_update,
                        valid_create=valid_create,
                    )
            except Exception as e:
                logger.error("Exception during upsert save: %s", e, exc_info=True)
                raise UpsertException("An internal error occurred during upsert save. All features are rolled back.")
        return valid_create, valid_update

    def _validate_single_feature(self, exec_obj, OriginalResource, upsert_key, layers, layer_iterator):
        errors = []
        feature_validators_registry.init_handlers(self.real_instance)
        while True:
            # Create an iterator for the next chunk
            data_chunk = list(islice(layer_iterator, settings.UPSERT_CHUNK_SIZE))

            # If the chunk is empty, we've reached the end of the layer
            if not data_chunk:
                break

            errors = self._validate_feature(
                data_chunk, model_instance=OriginalResource, upsert_key=upsert_key, errors=errors
            )

        if errors:
            # if some error is found, is useless to keep the VALID feature in memeory, we can just ignore it and proceed:
            # cleaning up the feature from memory
            self._create_error_log(exec_obj, layers, errors)

    def __get_csv_headers(self):
        constrained_attributes = []
        for handler in feature_validators_registry.HANDLERS:
            if hasattr(handler, "restrictions"):
                constrained_attributes.extend(handler.restrictions.keys())
        return ["fid"] + constrained_attributes + ["error"]

    def _create_error_log(self, exec_obj, layers, errors):
        logger.error(
            "Error found during the upsert process, no update/create will be perfomed. The error log is going to be created..."
        )
        errors_to_print = errors[: settings.UPSERT_LIMIT_ERROR_LOG]

        fieldnames = self.__get_csv_headers()

        log_name = f'error_{layers[0].GetName()}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            subfolder_path = temp_dir / "upsert_logs"
            subfolder_path.mkdir(parents=True, exist_ok=True)
            csv_file_path = subfolder_path / log_name
            with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
                # Create a DictWriter object. It maps dictionaries to output rows.
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(errors_to_print)

            self.create_asset_and_link(
                exec_obj.geonode_resource,
                files={"base_file": str(csv_file_path)},
                action=exec_obj.action,
                asset_name=log_name,
            )

        raise UpsertException(
            "Some validations failed. Errors are reported inside a CSV file that can be found inside the assets panel."
        )

    def _validate_feature(self, data_chunk, model_instance, upsert_key, errors):
        # looping over the chunk data
        for feature in data_chunk:
            feature_as_dict = feature.items()
            # need to simulate the "promote to multi" used by the upload process.
            # here we cannot rely on ogr2ogr so we need to do it manually
            geom = feature.GetGeometryRef()
            if geom:
                wkt = self.promote_geom_to_multi(geom).ExportToWkt()
                if code := geom.GetSpatialReference().GetAuthorityCode(None):
                    wkt = f"SRID={code};{wkt}"
                feature_as_dict.update({self.default_geometry_column_name: wkt})

            feature_as_dict, is_valid = self.validate_feature(feature_as_dict)
            if not is_valid:
                errors.append(feature_as_dict)
                continue

        return errors

    def _save_feature(self, data_chunk, model_obj, model_instance, upsert_key, valid_update, valid_create):
        # getting all the upsert_key value from the data chunk
        # retrieving the data from the DB
        value_in_db = model_instance.objects.filter(
            **{f"{upsert_key}__in": (getattr(feature, upsert_key) for feature in data_chunk)}
        ).in_bulk(field_name=upsert_key)
        # looping over the chunk data
        to_process = []
        feature_to_save = []
        for feature in data_chunk:
            feature_as_dict = feature.items()
            # evaluate if there is any date in the schema of the feature
            schema = feature.DumpReadableAsString().split("\n")
            if any(date_fields := [f for f in schema if ("(Date)" in f or "(DateTime)" in f) and "(null)" not in f]):
                # if any field schema as date is found, we can normalize the date
                pattern = re.compile(r"^\s*(?P<label>.+?)\s*\(\s*(?P<type>.+?)\s*\)\s*=\s*(?P<date_value>.+)\s*$")
                for fields in date_fields:
                    match = pattern.search(fields)
                    label = match.group("label")
                    date_value = match.group("date_value")
                    feature_as_dict[label] = date_value.replace("/", "-")
            # need to simulate the "promote to multi" used by the upload process.
            # here we cannot rely on ogr2ogr so we need to do it manually
            geom = feature.GetGeometryRef()
            code = geom.GetSpatialReference().GetAuthorityCode(None)
            feature_as_dict.update(
                {self.default_geometry_column_name: f"SRID={code};{self.promote_geom_to_multi(geom).ExportToWkt()}"}
            )
            to_process.append(feature_as_dict)

        for feature_as_dict in to_process:
            if feature_as_dict.get(upsert_key) in value_in_db:
                # if the key is present, we need to update the object
                # the geometry must be treated manually
                obj = value_in_db[feature_as_dict.get(upsert_key)]
                for key, value in feature_as_dict.items():
                    setattr(obj, key, value)
                feature_to_save.append(obj)
                valid_update += 1
            else:
                # if the key is not present, we can create a new instance
                feature_to_save.append(model_instance(**feature_as_dict))
                valid_create += 1
        try:
            schema_fields = [f.name for f in model_obj.fields.filter(kwargs__primary_key__isnull=True)]
            model_instance.objects.bulk_create(
                feature_to_save, update_conflicts=True, update_fields=schema_fields, unique_fields=[upsert_key]
            )
        except Exception:
            logger.exception("Error occurred during bulk upsert in upsert_data.")
            raise UpsertException("An internal error occurred during upsert operation.")

        return valid_update, valid_create

    def validate_feature(self, feature):
        try:
            feature_validators_registry.validate(feature)
            return feature, True
        except ValidationError as e:
            errors = e.messages if hasattr(e, "messages") else [str(e)]
            feature["error"] = " | ".join(errors)
            return feature, False

    def extract_upsert_key(self, exec_obj, dynamic_model_instance):
        # first we check if the upsert key is passed by the call
        key = exec_obj.input_params.get("upsert_key", DEFAULT_PK_COLUMN_NAME)
        if not key:
            # if the upsert key is not passed, we use the primary key as upsert key
            # the primary key is defined in the Fields of the dynamic model
            # dynamic models raise error if we filter the json with ORM
            key = [x.name for x in dynamic_model_instance.fields.all() if x.kwargs.get("primary_key")]
            if key:
                return key[0]

        return key

    def refresh_geonode_resource(self, execution_id, asset=None, dataset=None, create_asset=True, **kwargs):
        # getting execution_id information
        exec_obj = orchestrator.get_execution_object(execution_id)
        # getting the geonode resource
        if not dataset:
            dataset = Dataset.objects.filter(pk=exec_obj.input_params.get("resource_pk")).first()

        # once the upsert is completed, the geonode resource must be update to
        # load the new data from the database
        if not asset and create_asset:
            # if the asset is not passed, we can create a new one
            asset = self.create_asset_and_link(
                resource=dataset, files=exec_obj.input_params["files"], action=exec_obj.action
            )
            # but we need to delete the previous one associated to the resource
        start = datetime.now()
        delete_dataset_cache(dataset.alternate)
        logging.debug(f"DATASET DELETE CACHE DONE {datetime.now() - start}")

        # recalculate featuretype info
        start = datetime.now()
        DataPublisher(str(self)).recalculate_geoserver_featuretype(dataset)
        logging.debug(f"recalculate_geoserver_featuretype DONE {datetime.now() - start}")

        start = datetime.now()
        set_geowebcache_invalidate_cache(dataset_alternate=dataset.alternate)
        logging.debug(f"set_geowebcache_invalidate_cache DONE {datetime.now() - start}")

        dataset = resource_manager.update(dataset.uuid, instance=dataset)

        self.handle_xml_file(dataset, exec_obj)
        self.handle_sld_file(dataset, exec_obj)

        resource_manager.set_thumbnail(dataset.uuid, instance=dataset, overwrite=True)
        dataset.refresh_from_db()

        orchestrator.update_execution_request_obj(exec_obj, {"geonode_resource": dataset})

        self.__fixup_primary_key(dataset)
        return dataset

    def fixup_dynamic_model_fields(self, _exec, files):
        """
        Utility needed during the replace workflow,
        it will sync all the FieldSchema along with the current resource uploaded.
        This is mandatory in order to have a reliable field structure in the DB
        """
        fields_schema, needed_field_schema = self.__get_new_and_original_schema(files, str(_exec.exec_id))
        fields_schema.filter(~Q(name__in=(x["name"] for x in needed_field_schema))).delete()


@importer_app.task(
    base=ErrorBaseTaskClass,
    name="geonode.upload.import_next_step",
    queue="geonode.upload.import_next_step",
    task_track_started=True,
)
def import_next_step(
    _,
    execution_id: str,
    handlers_module_path: str,
    actual_step: str,
    layer_name: str,
    alternate: str,
    **kwargs: dict,
):
    """
    If the ingestion of the resource is successfuly, the next step for the layer is called
    """
    from geonode.upload.celery_tasks import import_orchestrator

    try:
        _exec = orchestrator.get_execution_object(execution_id)

        _files = _exec.input_params.get("files")
        # at the end recall the import_orchestrator for the next step

        task_params = (
            _files,
            execution_id,
            handlers_module_path,
            actual_step,
            layer_name,
            alternate,
            _exec.input_params.get("action", exa.UPLOAD.value),
        )

        import_orchestrator.apply_async(task_params, kwargs)
    except Exception as e:
        call_rollback_function(
            execution_id,
            handlers_module_path=handlers_module_path,
            prev_action=_exec.input_params.get("action", exa.UPLOAD.value),
            layer=layer_name,
            alternate=alternate,
            error=e,
            **kwargs,
        )

    finally:
        return "import_next_step", alternate, execution_id


@importer_app.task(
    base=UpdateDynamicTaskClass,
    name="geonode.upload.import_with_ogr2ogr",
    queue="geonode.upload.import_with_ogr2ogr",
    max_retries=1,
    acks_late=False,
    ignore_result=False,
    task_track_started=True,
)
def import_with_ogr2ogr(
    execution_id: str,
    files: dict,
    original_name: str,
    handler_module_path: str,
    ovverwrite_layer=False,
    alternate=None,
    **kwargs,
):
    """
    Perform the ogr2ogr command to import he gpkg inside geonode_data
    If the layer should be overwritten, the option is appended dynamically
    """
    try:
        ogr_exe = shutil.which("ogr2ogr")

        options = orchestrator.load_handler(handler_module_path).create_ogr2ogr_command(
            files, original_name, ovverwrite_layer, alternate, execution_id=execution_id
        )
        _datastore = settings.DATABASES["datastore"]

        copy_with_dump = ast.literal_eval(os.getenv("OGR2OGR_COPY_WITH_DUMP", "False"))

        if copy_with_dump:
            options += f" | PGPASSWORD={_datastore['PASSWORD']} psql -d {_datastore['NAME']} -h {_datastore['HOST']} -p {_datastore.get('PORT', 5432)} -U {_datastore['USER']} -f -"

        commands = [ogr_exe] + options.split(" ")
        process = Popen(" ".join(commands), stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()

        if files.get("temp_vrt_file") and os.path.exists(files["temp_vrt_file"]):
            os.remove(files["temp_vrt_file"])

        if (
            stderr is not None
            and stderr != b""
            and b"ERROR" in stderr
            and b"error" in stderr
            or b"Syntax error" in stderr
        ):
            try:
                err = stderr.decode()
            except Exception:
                err = stderr.decode("latin1")
            logger.error(f"Original error returned: {err}")
            message = normalize_ogr2ogr_error(err, original_name)
            raise Exception(f"{message} for layer {alternate}")
        return "ogr2ogr", alternate, execution_id
    except Exception as e:
        if files.get("temp_vrt_file") and os.path.exists(files.get("temp_vrt_file")):
            os.remove(files["temp_vrt_file"])
        call_rollback_function(
            execution_id,
            handlers_module_path=handler_module_path,
            prev_action=exa.UPLOAD.value,
            layer=original_name,
            alternate=alternate,
            error=e,
            **{},
        )
        raise Exception(e)


def normalize_ogr2ogr_error(err, original_name):
    getting_errors = [y for y in err.split("\n") if "ERROR " in y]
    return ", ".join([x.split(original_name)[0] for x in getting_errors if "ERROR" in x])
