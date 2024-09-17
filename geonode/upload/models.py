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
import logging

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase
from django.utils.translation import gettext_lazy as _
from geonode.resource.models import ExecutionRequest
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.template.defaultfilters import filesizeformat


logger = logging.getLogger("importer")


class UploadSizeLimitManager(models.Manager):
    def create_default_limit(self):
        max_size_db_obj = self.create(
            slug="dataset_upload_size",
            description="The sum of sizes for the files of a dataset upload.",
            max_size=settings.DEFAULT_MAX_UPLOAD_SIZE,
        )
        return max_size_db_obj

    def create_default_limit_with_slug(self, slug):
        max_size_db_obj = self.create(
            slug=slug,
            description="Size limit.",
            max_size=settings.DEFAULT_MAX_UPLOAD_SIZE,
        )
        return max_size_db_obj


class UploadParallelismLimitManager(models.Manager):
    def create_default_limit(self):
        default_limit = self.create(
            slug="default_max_parallel_uploads",
            description="The default maximum parallel uploads per user.",
            max_number=settings.DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER,
        )
        return default_limit


class UploadSizeLimit(models.Model):
    objects = UploadSizeLimitManager()

    slug = models.SlugField(
        primary_key=True,
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        validators=[MinLengthValidator(limit_value=3)],
    )
    description = models.TextField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
    )
    max_size = models.PositiveBigIntegerField(
        help_text=_("The maximum file size allowed for upload (bytes)."),
        default=settings.DEFAULT_MAX_UPLOAD_SIZE,
    )

    @property
    def max_size_label(self):
        return filesizeformat(self.max_size)

    def __str__(self):
        return f'UploadSizeLimit for "{self.slug}" (max_size: {self.max_size_label})'

    class Meta:
        ordering = ("slug",)


class UploadParallelismLimit(models.Model):
    objects = UploadParallelismLimitManager()

    slug = models.SlugField(
        primary_key=True,
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        validators=[MinLengthValidator(limit_value=3)],
    )
    description = models.TextField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
    )
    max_number = models.PositiveSmallIntegerField(
        help_text=_("The maximum number of parallel uploads (0 to 32767)."),
        default=settings.DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER,
    )

    def __str__(self):
        return f'UploadParallelismLimit for "{self.slug}" (max_number: {self.max_number})'

    class Meta:
        ordering = ("slug",)


@receiver(pre_delete, sender=Dataset)
def delete_dynamic_model(instance, sender, **kwargs):
    """
    Delete the dynamic relation and the geoserver layer
    """
    from geonode.upload.orchestrator import orchestrator

    try:
        if instance.resourcehandlerinfo_set.exists():
            handler_module_path = instance.resourcehandlerinfo_set.first().handler_module_path
            handler = orchestrator.load_handler(handler_module_path)
            handler.delete_resource(instance)
        # Removing Field Schema
    except Exception as e:
        logger.error(f"Error during deletion instance deletion: {e}")


class ResourceHandlerInfo(models.Model):
    """
    Here we save the relation between the geonode resource created and the handler that created that resource
    """

    resource = models.ForeignKey(ResourceBase, blank=False, null=False, on_delete=models.CASCADE)
    handler_module_path = models.CharField(max_length=250, blank=False, null=False)
    execution_request = models.ForeignKey(ExecutionRequest, null=True, default=None, on_delete=models.SET_NULL)
    kwargs = models.JSONField(verbose_name="Storing strictly related information of the handler", default=dict)
