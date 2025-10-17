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
from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model

from geonode.upload.orchestrator import orchestrator


class DataStoreManager:
    """
    Utility object to invoke the right handler used to save the
    resource in the datastore db
    """

    def __init__(
        self,
        files: list,
        handler_module_path: str,
        user: get_user_model(),  # type: ignore
        execution_id: str,
    ) -> None:
        self.files = files
        self.handler = import_string(handler_module_path)
        self.user = user
        self.execution_id = execution_id

    def input_is_valid(self):
        """
        Perform basic validation steps
        """
        url = orchestrator.get_execution_object(exec_id=self.execution_id).input_params.get("url")
        if url:
            return self.handler.is_valid_url(url)
        return self.handler.is_valid(self.files, self.user, execution_id=self.execution_id)

    def _import_and_register(self, execution_id, task_name, **kwargs):
        """
        Private method to handle resource import and register task status.
        """
        layer_names, _, _ = self.handler().import_resource(self.files, execution_id, **kwargs)
        orchestrator.register_task_status(execution_id, layer_names, task_name, status="RUNNING")

    def pre_processing(self, **kwargs):
        self.handler().pre_processing(self.files, self.execution_id, **kwargs)
        # always update the files after the pre-processing
        self.files = orchestrator.get_execution_object(exec_id=self.execution_id).input_params.get("files")

    def pre_validation(self, **kwargs):
        """
        Hook for let the handler prepare the data before the validation.
        Maybe a file rename, assign the resource to the execution_id
        """
        return self.handler().pre_validation(self.files, self.execution_id, **kwargs)

    def prepare_import(self, **kwargs):
        """
        prepares the data before the actual import
        """
        return self.handler().prepare_import(self.files, self.execution_id, **kwargs)

    def start_import(self, execution_id, task_name, **kwargs):
        """
        call the resource handler object to perform the import phase
        """
        self._import_and_register(execution_id, task_name, **kwargs)
        return

    def upsert_validation(self, execution_id, **kwargs):
        """
        Call the resource handler to validate files for an upsert operation.
        """
        return self.handler().upsert_validation(self.files, execution_id, **kwargs)

    def upsert_data(self, execution_id, task_name, **kwargs):
        """
        Call the resource handler to perform the upsert operation.
        """
        result = self.handler().upsert_data(self.files, execution_id, **kwargs)

        # register the task as RUNNING
        layer_name = result.get("layer_name", None)

        orchestrator.register_task_status(execution_id, layer_name, task_name, status="RUNNING")

        return result

    def refresh_geonode_resource(self, execution_id, **kwargs):
        """
        Call the resource handler to refresh the GeoNode resource after an update.
        """
        return self.handler().refresh_geonode_resource(execution_id, **kwargs)
