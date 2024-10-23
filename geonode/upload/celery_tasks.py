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
import logging
import os
from typing import Optional

from celery import Task
from django.db import connections, transaction
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy
from dynamic_models.exceptions import DynamicModelError, InvalidFieldNameError
from dynamic_models.models import FieldSchema, ModelSchema
from geonode.base.models import ResourceBase
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.api.exceptions import (
    CopyResourceException,
    InvalidInputFileException,
    PublishResourceException,
    ResourceCreationException,
    StartImportException,
)
from geonode.upload.celery_app import importer_app
from geonode.upload.datastore import DataStoreManager
from geonode.upload.handlers.gpkg.tasks import SingleMessageErrorHandler
from geonode.upload.handlers.utils import (
    create_alternate,
    drop_dynamic_model_schema,
    evaluate_error,
    get_uuid,
)
from geonode.upload.orchestrator import orchestrator
from geonode.upload.publisher import DataPublisher
from geonode.upload.settings import (
    IMPORTER_GLOBAL_RATE_LIMIT,
    IMPORTER_PUBLISHING_RATE_LIMIT,
    IMPORTER_RESOURCE_CREATION_RATE_LIMIT,
)
from geonode.upload.utils import call_rollback_function, error_handler, find_key_recursively

logger = logging.getLogger("importer")


class ErrorBaseTaskClass(Task):
    """
    Basic Error task class. Is common to all the base tasks of the import pahse
    it defines a on_failure method which set the task as "failed" with some extra information
    """

    max_retries = 3
    track_started = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # exc (Exception) - The exception raised by the task.
        # args (Tuple) - Original arguments for the task that failed.
        # kwargs (Dict) - Original keyword arguments for the task that failed.
        evaluate_error(self, exc, task_id, args, kwargs, einfo)


@importer_app.task(
    bind=True,
    base=ErrorBaseTaskClass,
    name="geonode.upload.import_orchestrator",
    queue="geonode.upload.import_orchestrator",
    max_retries=1,
    rate_limit=IMPORTER_GLOBAL_RATE_LIMIT,
    task_track_started=True,
)
def import_orchestrator(
    self,
    files: dict,
    execution_id: str,
    handler=None,
    step="start_import",
    layer_name=None,
    alternate=None,
    action=exa.UPLOAD.value,
    **kwargs,
):
    """
    Base task. Is the task responsible to call the orchestrator and redirect the upload to the next step
    mainly is a wrapper for the Orchestrator object.

            Parameters:
                    user (UserModel): user that is performing the request
                    execution_id (UUID): unique ID used to keep track of the execution request
                    step (str): last step performed from the tasks
                    layer_name (str): layer name
                    alternate (str): alternate used to naming the layer
            Returns:
                    None
    """
    try:
        # extract the resource_type of the layer and retrieve the expected handler

        orchestrator.perform_next_step(
            execution_id=execution_id,
            step=step,
            layer_name=layer_name,
            alternate=alternate,
            handler_module_path=handler,
            action=action,
            kwargs=kwargs,
        )

    except Exception as e:
        raise StartImportException(detail=error_handler(e, execution_id))


@importer_app.task(
    bind=True,
    # base=ErrorBaseTaskClass,
    name="geonode.upload.import_resource",
    queue="geonode.upload.import_resource",
    max_retries=1,
    rate_limit=IMPORTER_GLOBAL_RATE_LIMIT,
    ignore_result=False,
    task_track_started=True,
)
def import_resource(self, execution_id, /, handler_module_path, action, **kwargs):
    """
    Task to import the resources.
    NOTE: A validation if done before acutally start the import

            Parameters:
                    execution_id (UUID): unique ID used to keep track of the execution request
                    resource_type (str): extension of the resource type that we want to import
                    The resource type is needed to retrieve the right handler for the resource
            Returns:
                    None
    """
    # Updating status to running
    try:
        orchestrator.update_execution_request_status(
            execution_id=execution_id,
            last_updated=timezone.now(),
            func_name="import_resource",
            step=gettext_lazy("geonode.upload.import_resource"),
            celery_task_request=self.request,
        )
        _exec = orchestrator.get_execution_object(execution_id)

        _files = _exec.input_params.get("files")

        # initiating the data store manager
        _datastore = DataStoreManager(_files, handler_module_path, _exec.user, execution_id)

        _datastore.pre_validation(**kwargs)
        # starting file validation
        if not _datastore.input_is_valid():
            raise Exception("dataset is invalid")

        _datastore.prepare_import(**kwargs)
        _datastore.start_import(execution_id, **kwargs)

        """
        since the call to the orchestrator can changed based on the handler
        called. See the GPKG handler gpkg_next_step task
        """
        return self.name, execution_id

    except Exception as e:
        call_rollback_function(
            execution_id,
            handlers_module_path=handler_module_path,
            prev_action=exa.UPLOAD.value,
            layer=None,
            alternate=None,
            error=e,
            **kwargs,
        )
        raise InvalidInputFileException(detail=error_handler(e, execution_id))


@importer_app.task(
    bind=True,
    base=ErrorBaseTaskClass,
    name="geonode.upload.publish_resource",
    queue="geonode.upload.publish_resource",
    max_retries=3,
    rate_limit=IMPORTER_PUBLISHING_RATE_LIMIT,
    ignore_result=False,
    task_track_started=True,
)
def publish_resource(
    self,
    execution_id: str,
    /,
    step_name: str,
    layer_name: Optional[str] = None,
    alternate: Optional[str] = None,
    handler_module_path: str = None,
    action: str = None,
    **kwargs,
):
    """
    Task to publish a single resource in geoserver.
    NOTE: If the layer should be overwritten, for now we are skipping this feature
        geoserver is not ready yet

            Parameters:
                    execution_id (UUID): unique ID used to keep track of the execution request
                    step_name (str): step name example: geonode.upload.publish_resource
                    layer_name (UUID): name of the resource example: layer
                    alternate (UUID): alternate of the resource example: layer_alternate
            Returns:
                    None
    """
    # Updating status to running
    try:
        kwargs = kwargs.get("kwargs") if "kwargs" in kwargs else kwargs

        orchestrator.update_execution_request_status(
            execution_id=execution_id,
            last_updated=timezone.now(),
            func_name="publish_resource",
            step=gettext_lazy("geonode.upload.publish_resource"),
            celery_task_request=self.request,
        )
        _exec = orchestrator.get_execution_object(execution_id)
        _files = _exec.input_params.get("files")
        _overwrite = _exec.input_params.get("overwrite_existing_layer")

        _publisher = DataPublisher(handler_module_path)

        # extracting the crs and the resource name, are needed for publish the resource
        data = _publisher.extract_resource_to_publish(_files, action, layer_name, alternate, **kwargs)
        if data:
            # we should not publish resource without a crs
            if not _overwrite or (_overwrite and not _publisher.get_resource(alternate)):
                _publisher.publish_resources(data)
            else:
                _publisher.overwrite_resources(data)

            # updating the execution request status
            orchestrator.update_execution_request_status(
                execution_id=execution_id,
                last_updated=timezone.now(),
                celery_task_request=self.request,
            )
        else:
            logger.error(
                f"Layer: {alternate} raised: Only resources with a CRS provided can be published for execution_id: {execution_id}"
            )
            raise PublishResourceException("Only resources with a CRS provided can be published")

        # at the end recall the import_orchestrator for the next step

        task_params = (
            {},
            execution_id,
            handler_module_path,
            step_name,
            layer_name,
            alternate,
            action,
        )
        # for some reason celery will always put the kwargs into a key kwargs
        # so we need to remove it

        import_orchestrator.apply_async(task_params, kwargs)

        return self.name, execution_id

    except Exception as e:
        call_rollback_function(
            execution_id,
            handlers_module_path=handler_module_path,
            prev_action=action,
            layer=layer_name,
            alternate=alternate,
            error=e,
            **kwargs,
        )
        raise PublishResourceException(detail=error_handler(e, execution_id))


@importer_app.task(
    bind=True,
    base=ErrorBaseTaskClass,
    name="geonode.upload.create_geonode_resource",
    queue="geonode.upload.create_geonode_resource",
    max_retries=1,
    rate_limit=IMPORTER_RESOURCE_CREATION_RATE_LIMIT,
    ignore_result=False,
    task_track_started=True,
)
def create_geonode_resource(
    self,
    execution_id: str,
    /,
    step_name: str,
    layer_name: Optional[str] = None,
    alternate: Optional[str] = None,
    handler_module_path: str = None,
    action: str = exa.UPLOAD.value,
    **kwargs,
):
    """
    Create the GeoNode resource and the relatives information associated
    NOTE: for gpkg we dont want to handle sld and XML files

            Parameters:
                    execution_id (UUID): unique ID used to keep track of the execution request
                    resource_type (str): extension of the resource type that we want to import
                        The resource type is needed to retrieve the right handler for the resource
                    step_name (str): step name example: geonode.upload.publish_resource
                    layer_name (UUID): name of the resource example: layer
                    alternate (UUID): alternate of the resource example: layer_alternate
            Returns:
                    None
    """
    # Updating status to running
    try:
        orchestrator.update_execution_request_status(
            execution_id=execution_id,
            last_updated=timezone.now(),
            func_name="create_geonode_resource",
            step=gettext_lazy("geonode.upload.create_geonode_resource"),
            celery_task_request=self.request,
        )
        _exec = orchestrator.get_execution_object(execution_id)

        _files = _exec.input_params.get("files")

        if not _files:
            _asset = None
        else:
            _asset = (
                import_string(_exec.input_params.get("asset_module_path"))
                .objects.filter(id=_exec.input_params.get("asset_id"))
                .first()
            )

        handler_module_path = handler_module_path or _exec.input_params.get("handler_module_path")

        handler = import_string(handler_module_path)()
        _overwrite = _exec.input_params.get("overwrite_existing_layer")

        if _overwrite:
            resource = handler.overwrite_geonode_resource(
                layer_name=layer_name,
                alternate=alternate,
                execution_id=execution_id,
                asset=_asset,
            )
        else:
            resource = handler.create_geonode_resource(
                layer_name=layer_name,
                alternate=alternate,
                execution_id=execution_id,
                asset=_asset,
            )

        # assign geonode resource to ExectionRequest
        orchestrator.update_execution_request_obj(_exec, {"geonode_resource": resource})

        if _overwrite:
            handler.overwrite_resourcehandlerinfo(handler_module_path, resource, _exec, **kwargs)
        else:
            handler.create_resourcehandlerinfo(handler_module_path, resource, _exec, **kwargs)

        # at the end recall the import_orchestrator for the next step
        import_orchestrator.apply_async(
            (
                _files,
                execution_id,
                handler_module_path,
                step_name,
                layer_name,
                alternate,
                action,
            )
        )
        return self.name, execution_id

    except Exception as e:
        call_rollback_function(
            execution_id,
            handlers_module_path=handler_module_path,
            prev_action=action,
            layer=layer_name,
            alternate=alternate,
            error=e,
            **kwargs,
        )
        raise ResourceCreationException(detail=error_handler(e))


@importer_app.task(
    base=ErrorBaseTaskClass,
    name="geonode.upload.copy_geonode_resource",
    queue="geonode.upload.copy_geonode_resource",
    max_retries=1,
    rate_limit=IMPORTER_RESOURCE_CREATION_RATE_LIMIT,
    ignore_result=False,
    task_track_started=True,
)
def copy_geonode_resource(exec_id, actual_step, layer_name, alternate, handler_module_path, action, **kwargs):
    """
    Copy the geonode resource and create a new one. an assert is performed to be sure that the new resource
    have the new generated alternate
    """
    orchestrator.update_execution_request_status(
        execution_id=exec_id,
        last_updated=timezone.now(),
        func_name="copy_geonode_resource",
        step=gettext_lazy("geonode.upload.copy_geonode_resource"),
    )
    original_dataset_alternate = kwargs.get("kwargs").get("original_dataset_alternate")
    new_alternate = kwargs.get("kwargs").get("new_dataset_alternate")
    from geonode.upload.celery_tasks import import_orchestrator

    try:
        resource = ResourceBase.objects.filter(alternate=original_dataset_alternate)
        if not resource.exists():
            raise Exception("The resource requested does not exists")
        resource = resource.first()

        _exec = orchestrator.get_execution_object(exec_id)

        workspace = resource.alternate.split(":")[0]

        data_to_update = {
            "alternate": f"{workspace}:{new_alternate}",
            "name": new_alternate,
        }

        if _exec.input_params.get("title"):
            data_to_update["title"] = _exec.input_params.get("title")

        handler = import_string(handler_module_path)()

        new_resource = handler.copy_geonode_resource(
            alternate=alternate,
            resource=resource,
            _exec=_exec,
            data_to_update=data_to_update,
            new_alternate=new_alternate,
            **kwargs,
        )

        handler.create_resourcehandlerinfo(
            resource=new_resource,
            handler_module_path=handler_module_path,
            execution_id=_exec,
        )

        assert f"{workspace}:{new_alternate}" == new_resource.alternate

        orchestrator.update_execution_request_status(
            execution_id=str(_exec.exec_id),
            input_params={**_exec.input_params, **{"instance": resource.pk}},
            output_params={"output": {"uuid": str(new_resource.uuid)}},
        )

        task_params = (
            {},
            exec_id,
            handler_module_path,
            actual_step,
            layer_name,
            new_alternate,
            action,
        )
        # for some reason celery will always put the kwargs into a key kwargs
        # so we need to remove it
        kwargs = kwargs.get("kwargs") if "kwargs" in kwargs else kwargs

        import_orchestrator.apply_async(task_params, kwargs)

    except Exception as e:
        call_rollback_function(
            exec_id,
            handlers_module_path=handler_module_path,
            prev_action=action,
            layer=layer_name,
            alternate=alternate,
            error=e,
            **kwargs,
        )
        raise CopyResourceException(detail=e)
    return exec_id, new_alternate


@importer_app.task(
    base=SingleMessageErrorHandler,
    name="geonode.upload.create_dynamic_structure",
    queue="geonode.upload.create_dynamic_structure",
    max_retries=1,
    acks_late=False,
    ignore_result=False,
    task_track_started=True,
)
def create_dynamic_structure(
    execution_id: str,
    fields: dict,
    dynamic_model_schema_id: int,
    overwrite: bool,
    layer_name: str,
):
    def _create_field(dynamic_model_schema, field, _kwargs):
        # common method to define the Field Schema object
        return FieldSchema(
            name=field["name"],
            class_name=field["class_name"],
            model_schema=dynamic_model_schema,
            kwargs=_kwargs,
        )

    """
    Create the single dynamic model field for each layer. Is made by a batch of 30 field
    """
    dynamic_model_schema = ModelSchema.objects.filter(id=dynamic_model_schema_id)
    if not dynamic_model_schema.exists():
        raise DynamicModelError(f"The model with id {dynamic_model_schema_id} does not exists.")

    dynamic_model_schema = dynamic_model_schema.first()

    row_to_insert = []
    for field in fields:
        # setup kwargs for the class provided
        if field["class_name"] is None or field["name"] is None:
            logger.error(
                f"Error during the field creation. The field or class_name is None {field} for {layer_name} for execution {execution_id}"
            )
            raise InvalidFieldNameError(
                f"Error during the field creation. The field or class_name is None {field} for {layer_name} for execution {execution_id}"
            )

        _kwargs = {"null": field.get("null", True)}
        if field["class_name"].endswith("CharField"):
            _kwargs = {**_kwargs, **{"max_length": 255}}

        if field.get("dim", None) is not None:
            # setting the dimension for the gemetry. So that we can handle also 3d geometries
            _kwargs = {**_kwargs, **{"dim": field.get("dim")}}

        # if is a new creation we generate the field model from scratch
        if not overwrite:
            row_to_insert.append(_create_field(dynamic_model_schema, field, _kwargs))
        else:
            # otherwise if is an overwrite, we update the existing one and create the one that does not exists
            _field_exists = FieldSchema.objects.filter(name=field["name"], model_schema=dynamic_model_schema)
            if _field_exists.exists():
                _field_exists.update(
                    class_name=field["class_name"],
                    model_schema=dynamic_model_schema,
                    kwargs=_kwargs,
                )
            else:
                row_to_insert.append(_create_field(dynamic_model_schema, field, _kwargs))

    if row_to_insert:
        # the build creation improves the overall permformance with the DB
        FieldSchema.objects.bulk_create(row_to_insert, 30)

    del row_to_insert
    return "dynamic_model", layer_name, execution_id


@importer_app.task(
    base=ErrorBaseTaskClass,
    name="geonode.upload.copy_dynamic_model",
    queue="geonode.upload.copy_dynamic_model",
    task_track_started=True,
)
def copy_dynamic_model(exec_id, actual_step, layer_name, alternate, handler_module_path, action, **kwargs):
    """
    Once the base resource is copied, is time to copy also the dynamic model
    """

    from geonode.upload.celery_tasks import import_orchestrator

    try:
        orchestrator.update_execution_request_status(
            execution_id=exec_id,
            last_updated=timezone.now(),
            func_name="copy_dynamic_model",
            step=gettext_lazy("geonode.upload.copy_dynamic_model"),
        )
        additional_kwargs = {}

        resource = ResourceBase.objects.filter(alternate=alternate)

        if not resource.exists():
            raise Exception("The resource requested does not exists")

        resource = resource.first()

        new_dataset_alternate = create_alternate(resource.title, exec_id).lower()

        if os.getenv("IMPORTER_ENABLE_DYN_MODELS", False):
            dynamic_schema = ModelSchema.objects.filter(name=alternate.split(":")[1])
            alternative_dynamic_schema = ModelSchema.objects.filter(name=new_dataset_alternate)

            if dynamic_schema.exists() and not alternative_dynamic_schema.exists():
                # Creating the dynamic schema object
                new_schema = dynamic_schema.first()
                new_schema.name = new_dataset_alternate
                new_schema.db_table_name = new_dataset_alternate
                new_schema.pk = None
                new_schema.save()
                # create the field_schema object
                fields = []
                for field in dynamic_schema.first().fields.all():
                    obj = field
                    obj.model_schema = new_schema
                    obj.pk = None
                    fields.append(obj)

                FieldSchema.objects.bulk_create(fields)

        additional_kwargs = {
            "original_dataset_alternate": resource.alternate,
            "new_dataset_alternate": new_dataset_alternate,
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

    except Exception as e:
        call_rollback_function(
            exec_id,
            handlers_module_path=handler_module_path,
            prev_action=action,
            layer=layer_name,
            alternate=alternate,
            error=e,
            **{**kwargs, **additional_kwargs},
        )
        raise CopyResourceException(detail=e)
    return exec_id, kwargs


@importer_app.task(
    base=ErrorBaseTaskClass,
    name="geonode.upload.copy_geonode_data_table",
    queue="geonode.upload.copy_geonode_data_table",
    task_track_started=True,
)
def copy_geonode_data_table(exec_id, actual_step, layer_name, alternate, handlers_module_path, action, **kwargs):
    """
    Once the base resource is copied, is time to copy also the dynamic model
    """
    try:
        orchestrator.update_execution_request_status(
            execution_id=exec_id,
            last_updated=timezone.now(),
            func_name="copy_geonode_data_table",
            step=gettext_lazy("geonode.upload.copy_geonode_data_table"),
        )

        original_dataset_alternate = kwargs.get("kwargs").get("original_dataset_alternate").split(":")[1]

        new_dataset_alternate = kwargs.get("kwargs").get("new_dataset_alternate")

        from geonode.upload.celery_tasks import import_orchestrator

        db_name = os.getenv("DEFAULT_BACKEND_DATASTORE", "datastore")
        if os.getenv("IMPORTER_ENABLE_DYN_MODELS", False):
            schema_exists = ModelSchema.objects.filter(name=new_dataset_alternate).first()
            if schema_exists:
                db_name = schema_exists.db_name

        with transaction.atomic():
            with connections[db_name].cursor() as cursor:
                cursor.execute(f'CREATE TABLE {new_dataset_alternate} AS TABLE "{original_dataset_alternate}";')

        task_params = (
            {},
            exec_id,
            handlers_module_path,
            actual_step,
            layer_name,
            alternate,
            action,
        )

        kwargs = kwargs.get("kwargs") if "kwargs" in kwargs else kwargs

        import_orchestrator.apply_async(task_params, kwargs)

    except Exception as e:
        call_rollback_function(
            exec_id,
            handlers_module_path=handlers_module_path,
            prev_action=action,
            layer=layer_name,
            alternate=alternate,
            error=e,
            **kwargs,
        )
        raise CopyResourceException(detail=e)
    return exec_id, kwargs


@importer_app.task(
    bind=True,
    base=ErrorBaseTaskClass,
    queue="geonode.upload.rollback",
    name="geonode.upload.rollback",
    task_track_started=True,
)
def rollback(self, *args, **kwargs):
    """
    Task used to rollback the partially imported resource
    The handler must implement the code to rollback each step that
    is declared
    """

    exec_id = get_uuid(args)

    logger.info(f"Calling rollback for execution_id {exec_id} in progress")

    exec_object = orchestrator.get_execution_object(exec_id)
    rollback_from_step = exec_object.step
    action_to_rollback = exec_object.action
    handler_module_path = exec_object.input_params.get("handler_module_path")

    orchestrator.update_execution_request_status(
        execution_id=exec_id,
        last_updated=timezone.now(),
        func_name="rollback",
        step=gettext_lazy("geonode.upload.rollback"),
        celery_task_request=self.request,
    )

    handler = import_string(handler_module_path)()
    if exec_object.input_params.get("overwrite_existing_layer"):
        logger.warning("Rollback is skipped for the overwrite")
    else:
        handler.rollback(exec_id, rollback_from_step, action_to_rollback, *args, **kwargs)
    error = find_key_recursively(kwargs, "error") or "Some issue has occured, please check the logs"
    logger.error(error)
    orchestrator.set_as_failed(exec_id, reason=error, delete_file=False)
    return exec_id, kwargs


@importer_app.task(name="dynamic_model_error_callback")
def dynamic_model_error_callback(*args, **kwargs):
    # revert eventually the import in ogr2ogr or the creation of the model in case of failing
    alternate = args[0].args[-1]
    schema_model = ModelSchema.objects.filter(name=alternate).first()
    if schema_model:
        drop_dynamic_model_schema(schema_model)

    return "error"
