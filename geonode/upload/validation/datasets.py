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

from geonode.upload.handlers.base import BaseHandler
from geonode.upload.validation.base import ValidationConfigProvider, merge_handler_configs


class DatasetFileValidationConfigProvider(ValidationConfigProvider):
    """
    File validation config for the dataset importer endpoint (URL name
    "importer_upload" / permission base.add_resourcebase).

    The merged config is computed by walking ``BaseHandler.REGISTRY``: every
    handler that exposes ``upload_validation_config`` contributes its
    extensions, libmagic MIME set, and libmagic description substrings. A
    handler that does not declare the property contributes nothing, which
    means disabling a handler (e.g. via a feature flag) automatically
    removes its file types from the allowed set.
    """

    def url_names(self):
        return ("importer_upload",)

    def build_config(self):
        return merge_handler_configs(BaseHandler.REGISTRY)
