#########################################################################
#
# Copyright (C) 2026 OSGeo
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

import copy
import typing
import logging

from geonode.base.models import ResourceBase
from geonode.resource.manager import BaseResourceManager
from geonode.documents.models import Document


logger = logging.getLogger(__name__)


class DocumentResourceManager(BaseResourceManager):
    handled_model = Document

    def create(
        self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs
    ) -> ResourceBase:
        from geonode.storage.manager import StorageManager

        file = kwargs.pop("file", None)
        request_user = kwargs.get("user")
        storage = None
        resource_type = resource_type or Document
        defaults = copy.deepcopy(defaults or {})
        extent = defaults.pop("extent", None)
        try:
            if file:
                if isinstance(file, str):
                    defaults["files"] = [file]
                else:
                    storage = StorageManager(remote_files={"base_file": file})
                    storage.clone_remote_files()
                    defaults["files"] = [storage.get_retrieved_paths().get("base_file")]
            resource = super().create(uuid, resource_type=resource_type, defaults=defaults)
            if extent or request_user:
                # Mirrors ResourceBaseSerializer.save() (extent + role defaults); could be moved to the API,
                # but it’s kept here to centralize manager behavior.
                self._apply_extent_and_role_defaults(resource, extent=extent, user=request_user)
            resource.handle_moderated_uploads()
            # Only trigger thumbnailing for local documents, not for remote URLs
            if resource.is_local:
                self.set_thumbnail(resource.uuid, instance=resource, overwrite=False)
            else:
                logger.info(f"Skipping thumbnail generation for remote document: {resource.doc_url}")
            return resource
        finally:
            if storage:
                storage.delete_retrieved_paths(force=True)
