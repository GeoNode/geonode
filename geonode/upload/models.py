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

import os
import base64
import pickle
import logging

from gsimporter.api import NotFound
from django.utils.timezone import now

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from geonode import GeoNodeException
from geonode.base import enumerations
from geonode.base.models import ResourceBase
from geonode.storage.manager import storage_manager
from geonode.geoserver.helpers import gs_uploader, ogc_server_settings

logger = logging.getLogger(__name__)


class UploadManager(models.Manager):
    def __init__(self):
        models.Manager.__init__(self)

    def invalidate_from_session(self, upload_session):
        return self.filter(user=upload_session.user, import_id=upload_session.import_session.id).update(
            state=enumerations.STATE_INVALID
        )

    def update_from_session(self, upload_session, resource: ResourceBase = None):
        _upload = None
        if resource:
            try:
                _upload = self.get(resource=resource)
            except Upload.DoesNotExist:
                _upload = None
        if not _upload:
            _upload = self.filter(user=upload_session.user, name=upload_session.name).order_by("-date").first()
        if _upload:
            return _upload.update_from_session(upload_session, resource=resource)
        return None

    def get_incomplete_uploads(self, user):
        return (
            self.filter(user=user).exclude(state=enumerations.STATE_PROCESSED).exclude(state=enumerations.STATE_WAITING)
        )


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


class Upload(models.Model):
    objects = UploadManager()

    import_id = models.BigIntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=16)
    create_date = models.DateTimeField("create_date", default=now)
    date = models.DateTimeField("date", default=now)
    resource = models.ForeignKey(ResourceBase, null=True, on_delete=models.SET_NULL)
    upload_dir = models.TextField(null=True)
    store_spatial_files = models.BooleanField(default=True)
    name = models.CharField(max_length=64, null=False, blank=False)
    complete = models.BooleanField(default=False)
    # hold our serialized session object
    session = models.TextField(null=True, blank=True)
    # hold a dict of any intermediate Dataset metadata - not used for now
    metadata = models.TextField(null=True)

    mosaic = models.BooleanField(default=False)
    append_to_mosaic_opts = models.BooleanField(default=False)
    append_to_mosaic_name = models.CharField(max_length=128, null=True)

    mosaic_time_regex = models.CharField(max_length=128, null=True)
    mosaic_time_value = models.CharField(max_length=128, null=True)

    mosaic_elev_regex = models.CharField(max_length=128, null=True)
    mosaic_elev_value = models.CharField(max_length=128, null=True)

    resume_url = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ["-date"]

    @property
    def get_session(self):
        if self.session:
            return pickle.loads(base64.decodebytes(self.session.encode("UTF-8")))

    def update_from_session(self, upload_session, resource: ResourceBase = None):
        self.session = base64.encodebytes(pickle.dumps(upload_session)).decode("UTF-8")
        self.import_id = upload_session.import_session.id
        self.name = upload_session.name
        self.user = upload_session.user
        self.date = now()

        if not self.upload_dir:
            self.upload_dir = os.path.dirname(upload_session.base_file)

        if resource:
            if not self.resource:
                if not isinstance(resource, ResourceBase) and hasattr(resource, "resourcebase_ptr"):
                    self.resource = resource.resourcebase_ptr
                elif not isinstance(resource, ResourceBase):
                    raise GeoNodeException("Invalid resource uploaded, plase select one of the available")
                else:
                    self.resource = resource

            if upload_session.base_file and len(self.resource.files) == 0:
                uploaded_files = upload_session.base_file[0]
                aux_files = uploaded_files.auxillary_files
                sld_files = uploaded_files.sld_files
                xml_files = uploaded_files.xml_files

                if self.store_spatial_files and self.resource and not self.resource.files:
                    files_to_upload = aux_files + sld_files + xml_files + [uploaded_files.base_file]
                    if len(files_to_upload):
                        ResourceBase.objects.upload_files(resource_id=self.resource.id, files=files_to_upload)
                        self.resource.refresh_from_db()

        if self.resource:
            if self.resource.processed:
                self.state = enumerations.STATE_PROCESSED
            else:
                self.state = enumerations.STATE_RUNNING
        elif self.state in (enumerations.STATE_READY, enumerations.STATE_PENDING):
            self.state = upload_session.import_session.state
            if self.state == enumerations.STATE_COMPLETE:
                self.complete = True

        self.save()
        return self.get_session

    @property
    def progress(self):
        if self.state in (enumerations.STATE_READY, enumerations.STATE_INVALID, enumerations.STATE_INCOMPLETE):
            return 0.0
        elif self.state == enumerations.STATE_PENDING:
            return 33.0
        elif self.state == enumerations.STATE_WAITING:
            return 50.0
        elif self.state == enumerations.STATE_PROCESSED:
            if (self.resource and self.resource.processed) or self.complete:
                return 100.0
            return 80.0
        elif self.state in (enumerations.STATE_COMPLETE, enumerations.STATE_RUNNING):
            if self.resource and self.resource.state == enumerations.STATE_PROCESSED:
                self.state = enumerations.STATE_PROCESSED
                self.save()
                return 90.0
            return 80.0

    def set_resume_url(self, resume_url):
        if self.resume_url != resume_url:
            self.resume_url = resume_url
            Upload.objects.filter(id=self.id).update(resume_url=resume_url)

    def get_resume_url(self):
        if self.state == enumerations.STATE_WAITING and self.import_id:
            return self.resume_url
        return None

    def get_delete_url(self):
        if self.state != enumerations.STATE_PROCESSED:
            return reverse("data_upload_delete", args=[self.id])
        return None

    def get_import_url(self):
        session = None
        try:
            if not self.import_id:
                raise NotFound
            session = self.get_session.import_session
            if not session or session.state != enumerations.STATE_COMPLETE:
                session = gs_uploader.get_session(self.import_id)
        except (NotFound, Exception):
            if not session and self.state not in (enumerations.STATE_COMPLETE, enumerations.STATE_PROCESSED):
                logger.warning(f"Import session was not found for upload with ID: {self.pk}")
        if session and self.state != enumerations.STATE_INVALID:
            return f"{ogc_server_settings.LOCATION}rest/imports/{session.id}"
        else:
            return None

    def get_detail_url(self):
        if self.resource and self.resource.processed:
            return getattr(self.resource, "detail_url", None)
        else:
            return None

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        storage_manager.rmtree(self.upload_dir, ignore_errors=True)

    def set_processing_state(self, state):
        if self.state != state:
            self.state = state
            Upload.objects.filter(id=self.id).update(state=state)
        if self.resource:
            self.resource.set_processing_state(state)

    def __str__(self):
        return f"Upload [{self.pk}] gs{self.import_id} - {self.name}, {self.user}"


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
