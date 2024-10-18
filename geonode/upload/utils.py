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
import enum
from geonode.resource.manager import ResourceManager
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.base.models import ResourceBase
from django.utils.translation import gettext_lazy as _
from geonode.upload.api.exceptions import (
    FileUploadLimitException,
    UploadParallelismLimitException,
)
from geonode.upload.models import UploadSizeLimit, UploadParallelismLimit
from django.template.defaultfilters import filesizeformat
from geonode.resource.models import ExecutionRequest
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings


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


class ImporterRequestAction(enum.Enum):
    ROLLBACK = _("rollback")
    RESOURCE_METADATA_UPLOAD = _("resource_metadata_upload")
    RESOURCE_STYLE_UPLOAD = _("resource_style_upload")
    REPLACE = _("replace")


def error_handler(exc, exec_id=None):
    return f'{str(exc.detail if hasattr(exc, "detail") else exc.args[0])}. Request: {exec_id}'


class ImporterConcreteManager(GeoServerResourceManager):
    """
    The default GeoNode concrete manager, handle the communication with geoserver
    For this implementation the interaction with geoserver is not needed
    so we are going to overwrite the concrete manager to avoid it
    """

    def copy(self, instance, uuid, defaults):
        return ResourceBase.objects.get(uuid=uuid)

    def update(self, uuid, **kwargs) -> ResourceBase:
        return ResourceBase.objects.get(uuid=uuid)


custom_resource_manager = ResourceManager(concrete_manager=ImporterConcreteManager())


def call_rollback_function(
    execution_id,
    handlers_module_path,
    prev_action,
    layer=None,
    alternate=None,
    error=None,
    **kwargs,
):
    from geonode.upload.celery_tasks import import_orchestrator

    task_params = (
        {},
        execution_id,
        handlers_module_path,
        "start_rollback",
        layer,
        alternate,
        ImporterRequestAction.ROLLBACK.value,
    )
    kwargs["previous_action"] = prev_action
    kwargs["error"] = error_handler(error, exec_id=execution_id)
    import_orchestrator.apply_async(task_params, kwargs)


def find_key_recursively(obj, key):
    """
    Celery (unluckly) append the kwargs for each task
    under a new kwargs key, so sometimes is faster
    to look into the key recursively instead of
    parsing the dict
    """
    if key in obj:
        return obj.get(key, None)
    for _unsed, v in obj.items():
        if isinstance(v, dict):
            return find_key_recursively(v, key)


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
        """
        Count the total layers that are part of the running import
        """
        return sum(
            filter(
                None,
                ExecutionRequest.objects.filter(
                    user=self.user, status__in=[ExecutionRequest.STATUS_RUNNING, ExecutionRequest.STATUS_READY]
                ).values_list("input_params__total_layers", flat=True),
            )
        )
