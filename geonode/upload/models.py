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

from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


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
