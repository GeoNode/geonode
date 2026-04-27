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

from django.conf import settings

from geonode.documents.enumerations import DOCUMENT_MAGIC_MIMETYPE_MAP
from geonode.upload.validation.base import ValidationConfigProvider


class DocumentFileValidationConfigProvider(ValidationConfigProvider):
    """
    File validation config for the legacy /documents/upload/ HTML form view
    (URL name "document_upload"). Sources its data from the static
    DOCUMENT_MAGIC_MIMETYPE_MAP and the operator-tunable
    ALLOWED_DOCUMENT_TYPES setting.
    """

    def url_names(self):
        return ("document_upload",)

    def build_config(self):
        return {
            "allowed_extensions": frozenset(settings.ALLOWED_DOCUMENT_TYPES),
            "magic_mimetype_map": {
                ext: frozenset(mimes) for ext, mimes in DOCUMENT_MAGIC_MIMETYPE_MAP.items()
            },
        }
