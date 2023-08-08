#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.conf import settings

from django.utils.translation import ugettext as _
from django.template.defaultfilters import filesizeformat

from geonode.upload.api.exceptions import (
    FileUploadLimitException,
    UploadParallelismLimitException,
)
from geonode.upload.models import UploadSizeLimit, UploadParallelismLimit
from django.core.exceptions import ObjectDoesNotExist
from geonode.resource.models import ExecutionRequest


logger = logging.getLogger(__name__)


class UploadLimitValidator:
    def __init__(self, user) -> None:
        self.user = user

    def validate_parallelism_limit_per_user(self):
        max_parallel_uploads = self._get_max_parallel_uploads()
        parallel_uploads_count = self._get_parallel_uploads_count()
        if parallel_uploads_count >= max_parallel_uploads:
            raise UploadParallelismLimitException(
                _(
                    f"The number of active parallel uploads exceeds {max_parallel_uploads}. Wait for the pending ones to finish."
                )
            )

    def validate_files_sum_of_sizes(self, file_dict):
        max_size = self._get_uploads_max_size()
        total_size = self._get_uploaded_files_total_size(file_dict)
        if total_size > max_size:
            raise FileUploadLimitException(
                _(f"Total upload size exceeds {filesizeformat(max_size)}. Please try again with smaller files.")
            )

    def _get_uploads_max_size(self):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug="dataset_upload_size")
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit()
        return max_size_db_obj.max_size

    def _get_uploaded_files(self):
        """Return a list with all of the uploaded files"""
        return [django_file for field_name, django_file in self.files.items() if field_name != "base_file"]

    def _get_uploaded_files_total_size(self, file_dict):
        """Return a list with all of the uploaded files"""
        excluded_files = (
            "zip_file",
            "shp_file",
        )
        _iterate_files = file_dict.data_items if hasattr(file_dict, "data_items") else file_dict
        uploaded_files_sizes = [
            file_obj.size for field_name, file_obj in _iterate_files.items() if field_name not in excluded_files
        ]
        total_size = sum(uploaded_files_sizes)
        return total_size

    def _get_max_parallel_uploads(self):
        try:
            parallelism_limit = UploadParallelismLimit.objects.get(slug="default_max_parallel_uploads")
        except UploadParallelismLimit.DoesNotExist:
            parallelism_limit = UploadParallelismLimit.objects.create_default_limit()
        return parallelism_limit.max_number

    def _get_parallel_uploads_count(self):
        return (
            ExecutionRequest.objects.filter(user=self.user)
            .exclude(status=ExecutionRequest.STATUS_FINISHED)
            .exclude(status=ExecutionRequest.STATUS_FAILED)
            .count()
        )


def get_max_upload_size(slug):
    try:
        max_size = UploadSizeLimit.objects.get(slug=slug).max_size
    except ObjectDoesNotExist:
        max_size = getattr(settings, "DEFAULT_MAX_UPLOAD_SIZE", 104857600)
    return max_size


def get_max_upload_parallelism_limit(slug):
    try:
        max_number = UploadParallelismLimit.objects.get(slug=slug).max_number
    except ObjectDoesNotExist:
        max_number = getattr(settings, "DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER", 5)
    return max_number
