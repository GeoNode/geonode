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
import logging
from typing import Optional
from uuid import UUID
import zipfile

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.module_loading import import_string
from geonode.base.models import ResourceBase
from geonode.layers.models import Dataset
from geonode.resource.models import ExecutionRequest
from rest_framework import serializers

from geonode.storage.utils import organize_files_by_ext
from geonode.upload.api.exceptions import ImportException
from geonode.upload.api.serializer import ImporterSerializer, OverwriteImporterSerializer, UpsertImporterSerializer
from geonode.upload.celery_app import importer_app
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.utils import create_layer_key
from geonode.upload.utils import error_handler
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")


class ImportOrchestrator:
    """'
    Main import object. Is responsible to handle all the execution steps
    Using the ExecutionRequest object, will extrapolate the information and
    it call the next step of the import pipeline
    Params:

    """

    def get_handler_registry(self):
        return BaseHandler.get_registry()

    def get_handler(self, _data) -> Optional[BaseHandler]:
        """
        If is part of the supported format, return the handler which can handle the import
        otherwise return None
        """
        file_list = {}
        if "zip_file" in _data or "kmz_file" in _data:
            with zipfile.ZipFile(_data["base_file"], "r") as zip_ref:
                # Get a list of all files inside the zip
                file_list = organize_files_by_ext(zip_ref.namelist())
        _data = _data | file_list

        for handler in self.get_handler_registry():
            can_handle = handler.can_handle(_data)
            match can_handle:
                case True:
                    return handler()
                case False:
                    logger.info(
                        f"The handler {str(handler)} cannot manage the requested action: {_data.get('action', None)}"
                    )

        logger.error("No handlers found for this dataset type/action")
        return None

    def get_serializer(self, _data) -> serializers.Serializer:
        for handler in self.get_handler_registry():
            _serializer = handler.has_serializer(_data)
            if _serializer:
                return _serializer
        logger.info("specific serializer not found, fallback on the default one")
        is_overwrite_flow = _data.get("overwrite_existing_layer", False)
        if _data.get("action") == ira.UPSERT.value:
            return UpsertImporterSerializer
        if isinstance(is_overwrite_flow, str):
            is_overwrite_flow = ast.literal_eval(is_overwrite_flow.title())
        return OverwriteImporterSerializer if is_overwrite_flow else ImporterSerializer

    def load_handler(self, module_path):
        try:
            return import_string(module_path)
        except Exception:
            raise ImportException(detail=f"The handler is not available: {module_path}")

    def load_handler_by_id(self, handler_id):
        for handler in self.get_handler_registry():
            if handler().id == handler_id:
                return handler
        logger.error("Handler not found")
        return None

    def get_execution_object(self, exec_id):
        """
        Returns the ExecutionRequest object with the detail about the
        current execution
        """
        req = ExecutionRequest.objects.filter(exec_id=exec_id)
        if not req.exists():
            raise ImportException("The selected UUID does not exists")
        return req.first()

    def perform_next_step(
        self,
        execution_id: str,
        action: str,
        handler_module_path: str,
        step: str = None,
        layer_name: str = None,
        alternate: str = None,
        **kwargs,
    ) -> None:
        """
        It takes the executionRequest detail to extract which was the last step
        and take from the task_lists provided by the ResourceType handler
        which will be the following step. if empty a None is returned, otherwise
        in async the next step is called
        """
        try:
            _exec_obj = self.get_execution_object(str(execution_id))
            if step is None:
                step = _exec_obj.step

            # retrieve the task list for the resource_type
            tasks = self.load_handler(handler_module_path).get_task_list(action=action)
            # getting the index
            if not tasks:
                raise StopIteration("Task lists is completed")
            _index = tasks.index(step) + 1
            if _index == 1:
                """
                Means that the first task is available and we set the executions state as running
                So is updated only at the beginning keeping it in a consistent state
                """
                self.update_execution_request_status(
                    execution_id=str(_exec_obj.exec_id),
                    status=ExecutionRequest.STATUS_RUNNING,
                )
            # finding in the task_list the last step done
            remaining_tasks = tasks[_index:] if not _index >= len(tasks) else []
            if not remaining_tasks:
                # The list of task is empty, it means that the process is finished
                self.evaluate_execution_progress(execution_id, handler_module_path=handler_module_path)
                return
            # getting the next step to perform
            next_step = next(iter(remaining_tasks))
            # calling the next step for the resource

            # defining the tasks parameter for the step
            task_params = (str(execution_id), handler_module_path, action)
            logger.info(f"STARTING NEXT STEP {next_step}")

            if layer_name and alternate:
                # if the layer and alternate is provided, means that we are executing the step specifically for a layer
                # so we add this information to the task_parameters to be sent to the next step
                logger.info(f"STARTING NEXT STEP {next_step} for resource: {layer_name}, alternate {alternate}")

                """
                If layer name and alternate are provided, are sent as an argument
                for the next task step
                """
                task_params = (
                    str(execution_id),
                    next_step,
                    layer_name,
                    alternate,
                    handler_module_path,
                    action,
                )

                # We create the layer key through which the layer is stored in the tasks schema
                kwargs["layer_key"] = create_layer_key(layer_name, str(execution_id))

            # continuing to the next step
            importer_app.tasks.get(next_step).apply_async(task_params, kwargs)
            return execution_id

        except StopIteration:
            # means that the expected list of steps is completed
            logger.info("The whole list of tasks has been processed")
            self.set_as_completed(execution_id)
            return
        except Exception as e:
            self.set_as_failed(execution_id, reason=error_handler(e, execution_id))
            raise e

    def set_as_failed(self, execution_id, reason=None, delete_file=True):
        """
        Utility method to set the ExecutionRequest object to fail
        """
        self.update_execution_request_status(
            execution_id=str(execution_id),
            status=ExecutionRequest.STATUS_FAILED,
            finished=timezone.now(),
            last_updated=timezone.now(),
            log=reason,
        )
        # delete
        if delete_file:
            exec_obj = self.get_execution_object(execution_id)
            # cleanup asset in case of fail
            if exec_obj.input_params.get("asset_module_path", None):
                asset_handler = import_string(exec_obj.input_params["asset_module_path"])
                asset = asset_handler.objects.filter(pk=exec_obj.input_params["asset_id"])
                if asset.exists():
                    asset.first().delete()

    def set_as_partially_failed(self, execution_id, reason=None):
        """
        Utility method to set the ExecutionRequest object to partially failed
        """
        self.update_execution_request_status(
            execution_id=str(execution_id),
            status=ExecutionRequest.STATUS_FAILED,
            finished=timezone.now(),
            last_updated=timezone.now(),
            log=f"The execution is completed, but the following layers are not imported: \n {', '.join(reason)}. Check the logs for additional infos",
        )

    def set_as_completed(self, execution_id):
        """
        Utility method to set the ExecutionRequest object to fail
        """
        self.update_execution_request_status(
            execution_id=str(execution_id),
            status=ExecutionRequest.STATUS_FINISHED,
            finished=timezone.now(),
            last_updated=timezone.now(),
        )

    def evaluate_execution_progress(self, execution_id, _log=None, handler_module_path=None):

        from geonode.upload.models import ResourceHandlerInfo

        """
        Evaluate the progress of an execution request.
        Uses _exec.tasks to track the status of all alternates/tasks while it sets
        the execution request as failed, partially failed, or calls _evaluate_last_dataset.
        """

        _exec = self.get_execution_object(execution_id)
        tasks_status = _exec.tasks or {}

        expected_dataset = _exec.input_params.get("total_layers", 0)
        actual_dataset = ResourceHandlerInfo.objects.filter(execution_request=_exec).count()
        is_last_dataset = actual_dataset >= expected_dataset

        # Check if any data exists (ResourceHandlerInfo) for this execution
        _has_data = ResourceHandlerInfo.objects.filter(execution_request__exec_id=execution_id).exists()

        # Flatten all statuses across alternates
        all_statuses = [status for alt_dict in tasks_status.values() for status in alt_dict.values()]

        if any(status in {"RUNNING", "PENDING"} for status in all_statuses):
            # Some tasks still in progress
            self._evaluate_last_dataset(is_last_dataset, _log, execution_id, handler_module_path)

        elif "FAILED" in all_statuses:
            # At least one task failed
            failed_alternates = [alt for alt, status_dict in tasks_status.items() if "FAILED" in status_dict.values()]

            if _has_data and failed_alternates:
                # Partial import: some layers imported, some failed
                logger.error(f"Partial failure for execution {execution_id}: {failed_alternates}")
                self.set_as_partially_failed(execution_id=execution_id, reason=failed_alternates)
                self._last_step(execution_id, handler_module_path)
            else:
                # Nothing imported or only a single layer expected
                logger.error(f"Execution {execution_id} failed completely.")
                self.set_as_failed(execution_id=execution_id, reason=_log)

        else:
            # All tasks succeeded
            self._evaluate_last_dataset(is_last_dataset, _log, execution_id, handler_module_path)

    def _evaluate_last_dataset(self, is_last_dataset, _log, execution_id, handler_module_path):
        if is_last_dataset:
            if _log and "ErrorDetail" in _log:
                self.set_as_failed(execution_id=execution_id, reason=_log)
            else:
                logger.info(f"Execution with ID {execution_id} is completed. All tasks are done")
                self._last_step(execution_id, handler_module_path)
                self.set_as_completed(execution_id)
        else:
            logger.info(f"Execution progress with id {execution_id} is not finished yet, continuing")
            return

    def create_execution_request(
        self,
        user: get_user_model,
        func_name: str,
        step: str,
        input_params: dict = {},
        resource=None,
        action=None,
        name=None,
        source=None,
        asset_module_path=None,
    ) -> UUID:
        """
        Create an execution request for the user. Return the UUID of the request
        """
        execution = ExecutionRequest.objects.create(
            user=user,
            geonode_resource=ResourceBase.objects.filter(pk=resource).first().get_real_instance() if resource else None,
            func_name=func_name,
            step=step,
            input_params=input_params,
            action=action,
            name=name,
        )
        return execution.exec_id

    def update_execution_request_status(
        self,
        execution_id,
        status=None,
        celery_task_request=None,
        **kwargs,
    ):
        """
        Update the execution request status and also the legacy upload status if the
        feature toggle is enabled
        """
        if status is not None:
            kwargs["status"] = status

        ExecutionRequest.objects.filter(exec_id=execution_id).update(**kwargs)

    def update_execution_request_obj(self, _exec_obj, payload):
        ExecutionRequest.objects.filter(pk=_exec_obj.pk).update(**payload)
        _exec_obj.refresh_from_db()
        return _exec_obj

    def _last_step(self, execution_id, handler_module_path):
        """
        Last hookable step for each handler before mark the execution as completed
        To overwrite this, please hook the method perform_last_step from the Handler
        """
        if not handler_module_path:
            return
        return self.load_handler(handler_module_path).perform_last_step(execution_id)

    def register_task_status(
        self, exec_id: str, layer_refs: str | Dataset | list[str], step: str, status: str = "PENDING", persist=True
    ) -> None:
        """
        Register or update task status for one or more layers in an ExecutionRequest.
        """
        # Normalize input to a list
        if isinstance(layer_refs, (str, Dataset)):
            layer_refs = [layer_refs]

        _exec = self.get_execution_object(exec_id)

        for layer in layer_refs:
            # Extract the name if it's a Dataset
            layer = layer.name if isinstance(layer, Dataset) else str(layer)

            layer_key = create_layer_key(layer, str(_exec.exec_id))
            if layer_key not in _exec.tasks:
                _exec.tasks[layer_key] = {}
            _exec.tasks[layer_key][step] = status

        if persist:
            self.update_execution_request_status(execution_id=exec_id, tasks=_exec.tasks)

        return _exec.tasks


orchestrator = ImportOrchestrator()
