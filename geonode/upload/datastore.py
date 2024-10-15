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
        if self.files:
            return self.handler.is_valid(self.files, self.user, execution_id=self.execution_id)
        url = orchestrator.get_execution_object(exec_id=self.execution_id).input_params.get("url")
        if url:
            return self.handler.is_valid_url(url)
        return False

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

    def start_import(self, execution_id, **kwargs):
        """
        call the resource handler object to perform the import phase
        """
        return self.handler().import_resource(self.files, execution_id, **kwargs)
