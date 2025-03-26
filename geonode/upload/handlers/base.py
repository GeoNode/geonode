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
from abc import ABC
import logging
from typing import List

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.layers.models import Dataset
from geonode.upload.api.exceptions import ImportException
from geonode.upload.utils import ImporterRequestAction as ira, find_key_recursively
from django_celery_results.models import TaskResult
from django.db.models import Q
from geonode.resource.models import ExecutionRequest
from geonode.base.models import ResourceBase


logger = logging.getLogger("importer")


class BaseHandler(ABC):
    """
    Base abstract handler object
    define the required method needed to define an upload handler
    it must be:
    - provide the tasks list to complete the import
    - validation function
    - method to import the resource
    - create_error_log
    """

    REGISTRY = []

    TASKS = {
        exa.UPLOAD.value: (),
        exa.COPY.value: (),
        exa.DELETE.value: (),
        exa.UPDATE.value: (),
        ira.ROLLBACK.value: (),
    }

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def register(cls):
        BaseHandler.REGISTRY.append(cls)

    @classmethod
    def get_registry(cls):
        return BaseHandler.REGISTRY

    @classmethod
    def get_task_list(cls, action) -> tuple:
        if action not in cls.TASKS:
            raise Exception("The requested action is not implemented yet")
        return cls.TASKS.get(action)

    @property
    def default_geometry_column_name(self):
        return "geometry"

    @property
    def id(self):
        pk = self.supported_file_extension_config.get("id", None)
        if pk is None:
            raise ImportException(
                "PK must be defined, check that supported_file_extension_config had been correctly defined, it cannot be empty"
            )
        return pk

    @property
    def supported_file_extension_config(self):
        return {}

    @property
    def can_handle_xml_file(self) -> bool:
        """
        True or false if the handler is able to handle XML file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return True

    @property
    def can_handle_sld_file(self) -> bool:
        """
        True or false if the handler is able to handle SLD file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return True

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps
        """
        return NotImplementedError

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return False

    @staticmethod
    def has_serializer(_data) -> bool:
        """
        This endpoint should return (if set) the custom serializer used in the API
        to validate the input resource
        """
        return None

    @staticmethod
    def can_do(action) -> bool:
        """
        Evaluate if the handler can take care of a specific action.
        Each action (import/copy/etc...) can define different step so
        the Handler must be ready to handle them. If is not in the actual
        flow the already in place flow is followd
        """
        return action in BaseHandler.TASKS

    @staticmethod
    def extract_params_from_data(_data):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        return []

    @staticmethod
    def perform_last_step(execution_id):
        """
        Override this method if there is some extra step to perform
        before considering the execution as completed.
        For example can be used to trigger an email-send to notify
        that the execution is completed
        """
        from geonode.upload.orchestrator import orchestrator
        from geonode.upload.models import ResourceHandlerInfo

        # as last step, we delete the celery task to keep the number of rows under control
        lower_exec_id = execution_id.replace("-", "_").lower()
        TaskResult.objects.filter(
            Q(task_args__icontains=lower_exec_id)
            | Q(task_kwargs__icontains=lower_exec_id)
            | Q(result__icontains=lower_exec_id)
            | Q(task_args__icontains=execution_id)
            | Q(task_kwargs__icontains=execution_id)
            | Q(result__icontains=execution_id)
        ).delete()

        _exec = orchestrator.get_execution_object(execution_id)

        resource_output_params = [
            {"detail_url": x.resource.detail_url, "id": x.resource.pk}
            for x in ResourceHandlerInfo.objects.filter(execution_request=_exec)
        ]
        _exec.output_params.update({"resources": resource_output_params})
        _exec.save()

        return _exec

    def fixup_name(self, name):
        """
        Emulate the LAUNDER option in ogr2ogr which will normalize the string.
        This is enriched with additional transformation for parentesis.
        The basic normalized function can be found here
        https://github.com/OSGeo/gdal/blob/0fc262675051b63f96c91ca920d27503655dfb7b/ogr/ogrsf_frmts/pgdump/ogrpgdumpdatasource.cpp#L130  # noqa

        We use replace because it looks to be one of the fasted options:
        https://stackoverflow.com/questions/3411771/best-way-to-replace-multiple-characters-in-a-string
        """
        prefix = name[0]
        if prefix.isnumeric():
            name = name.replace(name[0], "_")
        return (
            name.lower()
            .replace("-", "_")
            .replace(" ", "_")
            .replace("#", "_")
            .replace("\\", "_")
            .replace(".", "")
            .replace(")", "")
            .replace("(", "")
            .replace(",", "")
            .replace("&", "")[:62]
        )

    def extract_resource_to_publish(self, files, layer_name, alternate, **kwargs):
        """
        Function to extract the layer name and the CRS from needed in the
        publishing phase
        [
            {'name': 'alternate or layer_name', 'crs': 'EPSG:25832'}
        ]
        """
        return NotImplementedError

    def overwrite_geoserver_resource(self, resource, catalog, store, workspace):
        """
        Base method for override the geoserver resource. For vector file usually
        is not needed since the value are replaced by ogr2ogr
        """
        pass

    @staticmethod
    def create_error_log(exc, task_name, *args):
        """
        This function will handle the creation of the log error for each message.
        This is helpful and needed, so each handler can specify the log as needed
        """
        return f"Task: {task_name} raised an error during actions for layer: {args[-1]}: {exc}"

    def prepare_import(self, files, execution_id, **kwargs):
        """
        Optional preparation step to before the actual import begins.
        By default this does nothing.
        """
        pass

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        """
        Define the step to perform the import of the data
        into the datastore db
        """
        return NotImplementedError

    @staticmethod
    def publish_resources(resources: List[str], catalog, store, workspace):
        """
        Given a list of strings (which rappresent the table on geoserver)
        Will publish the resorces on geoserver
        """
        return NotImplementedError

    def create_geonode_resource(self, layer_name, alternate, execution_id, resource_type: Dataset = Dataset):
        """
        Base function to create the resource into geonode. Each handler can specify
        and handle the resource in a different way
        """
        return NotImplementedError

    def create_resourcehandlerinfo(self, handler_module_path, resource, **kwargs):
        return NotImplementedError

    def get_ogr2ogr_task_group(self, execution_id, files, layer, should_be_overwritten, alternate):
        """
        implement custom ogr2ogr task group
        """
        return NotImplementedError

    @staticmethod
    def delete_resource(instance):
        """
        Base function to delete the resource with all the dependencies (example: dynamic model)
        """
        return

    def _get_execution_request_object(self, execution_id: str):
        return ExecutionRequest.objects.filter(exec_id=execution_id).first()

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

    def rollback(self, exec_id, rollback_from_step, action_to_rollback, *args, **kwargs):
        steps = self.TASKS.get(action_to_rollback)

        if rollback_from_step not in steps:
            logger.info(f"Step not found {rollback_from_step}, skipping")
            return
        step_index = steps.index(rollback_from_step)
        # the start_import, start_copy etc.. dont do anything as step, is just the start
        # so there is nothing to rollback
        steps_to_rollback = steps[1 : step_index + 1]  # noqa
        if not steps_to_rollback:
            return
        # reversing the tuple to going backwards with the rollback
        reversed_steps = steps_to_rollback[::-1]
        instance_name = None
        try:
            instance_name = find_key_recursively(kwargs, "new_dataset_alternate") or args[3]
        except Exception:
            pass

        logger.warning(f"Starting rollback for execid: {exec_id} resource published was: {instance_name}")

        for step in reversed_steps:
            normalized_step_name = step.split(".")[-1]
            if getattr(self, f"_{normalized_step_name}_rollback", None):
                function = getattr(self, f"_{normalized_step_name}_rollback")
                function(exec_id, instance_name, *args, **kwargs)

        logger.warning(f"Rollback for execid: {exec_id} resource published was: {instance_name} completed")

    def _create_geonode_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        from geonode.upload.orchestrator import orchestrator

        """
        The handler will remove the resource from geonode
        """
        logger.info(f"Rollback geonode step in progress for execid: {exec_id} resource created was: {istance_name}")
        _exec_obj = orchestrator.get_execution_object(exec_id)
        resource = ResourceBase.objects.filter(alternate__icontains=istance_name, owner=_exec_obj.user)
        if resource.exists():
            resource.delete()

    def _copy_dynamic_model_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        self._import_resource_rollback(exec_id, istance_name=istance_name)

    def _copy_geonode_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        self._create_geonode_resource_rollback(exec_id, istance_name=istance_name)
