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

from pathlib import Path
import magic

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from geonode.documents.enumerations import DOCUMENT_MAGIC_MIMETYPE_MAP
from geonode.upload.api.exceptions import FileUploadLimitException
from geonode.upload.models import UploadSizeLimit


DOCUMENT_UPLOAD_SIZE_SLUG = "document_upload_size"
DEFAULT_SAMPLE_SIZE = 4096


class FileValidator:
    def __init__(self, file, context="document"):
        self.file = file
        self.context = context
        self.extension = None
        self.detected_mime = None

    def validate(self):
        self.validate_extension()
        self.validate_size()
        self.validate_magic_mime()
        return True

    def validate_extension(self):
        extension = self._get_extension()
        if self.context == "document" and extension not in settings.ALLOWED_DOCUMENT_TYPES:
            raise ValidationError(_("The file provided is not in the supported extensions list"))
        self.extension = extension

    def validate_size(self):
        file_size = self._get_file_size()
        if file_size is None:
            return

        max_size = self._get_max_size()
        if file_size > max_size:
            raise FileUploadLimitException(
                _(f"File size size exceeds {filesizeformat(max_size)}. Please try again with a smaller file.")
            )

    def validate_magic_mime(self):
        sample = self._read_sample()
        if not sample:
            raise ValidationError(_("The uploaded file is empty or could not be read."))

        detected_mime = self._detect_mime(sample)
        self.detected_mime = detected_mime
        if not detected_mime:
            raise ValidationError(_("The uploaded file type could not be detected."))

        expected_mimes = DOCUMENT_MAGIC_MIMETYPE_MAP.get(self.extension, set())

        if not expected_mimes:
            raise ValidationError(_(f"File type .{self.extension} cannot be verified by MIME detection."))

        if detected_mime not in expected_mimes:
            raise ValidationError(
                _("The uploaded file content does not match the expected file type " f"for .{self.extension} files.")
            )

    def _get_extension(self):
        filename = self.file if isinstance(self.file, str) else getattr(self.file, "name", "")
        extension = Path(filename).suffix.replace(".", "").lower()
        if not extension:
            raise ValidationError(_("The uploaded file has no extension."))
        return extension

    def _get_file_size(self):
        if isinstance(self.file, str):
            try:
                return Path(self.file).stat().st_size
            except OSError:
                return None
        return getattr(self.file, "size", None)

    def _get_max_size(self):
        slug = DOCUMENT_UPLOAD_SIZE_SLUG if self.context == "document" else f"{self.context}_upload_size"
        try:
            return UploadSizeLimit.objects.get(slug=slug).max_size
        except UploadSizeLimit.DoesNotExist:
            return settings.DEFAULT_MAX_UPLOAD_SIZE

    def _read_sample(self):
        if isinstance(self.file, str):
            try:
                with open(self.file, "rb") as file_pointer:
                    return file_pointer.read(DEFAULT_SAMPLE_SIZE)
            except OSError:
                raise ValidationError(_("The uploaded file could not be read."))

        position = None
        try:
            position = self.file.tell()
        except (AttributeError, OSError):
            pass

        sample = self.file.read(DEFAULT_SAMPLE_SIZE)

        if position is not None:
            try:
                self.file.seek(position)
            except (AttributeError, OSError):
                pass

        return sample

    def _detect_mime(self, sample):
        try:
            return magic.from_buffer(sample, mime=True)
        except Exception:
            raise ValidationError(_("File type validation could not inspect the uploaded file."))
