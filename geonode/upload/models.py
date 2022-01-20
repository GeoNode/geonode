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
import shutil
import logging

from gsimporter.api import NotFound
from django.utils.timezone import now

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

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
        return self.filter(
            user=upload_session.user,
            import_id=upload_session.import_session.id
        ).update(state=enumerations.STATE_INVALID)

    def update_from_session(self, upload_session, resource=None):
        self.get(
            user=upload_session.user,
            name=upload_session.name,
            import_id=upload_session.import_session.id).update_from_session(
            upload_session, resource=resource)

    def create_from_session(self, user, import_session):
        return self.create(
            user=user,
            name=import_session.name,
            import_id=import_session.id,
            state=import_session.state)

    def get_incomplete_uploads(self, user):
        return self.filter(user=user).exclude(
            state=enumerations.STATE_PROCESSED)


class UploadSizeLimitManager(models.Manager):

    def create_default_limit(self):
        max_size_db_obj = self.create(
            slug="total_upload_size_sum",
            description="The sum of sizes for the files of a dataset upload.",
            max_size=settings.DEFAULT_MAX_UPLOAD_SIZE,
        )
        return max_size_db_obj

    def create_default_limit_for_upload_handler(self):
        max_size_db_obj = UploadSizeLimit.objects.create(
            slug="file_upload_handler",
            description=(
                'Request total size, validated before the upload process. '
                'This should be greater than "total_upload_size_sum".'
            ),
            max_size=settings.DEFAULT_MAX_BEFORE_UPLOAD_SIZE,
        )
        return max_size_db_obj

    def create_default_limit_with_slug(self, slug):
        max_size_db_obj = self.create(
            slug=slug,
            description="Size limit.",
            max_size=settings.DEFAULT_MAX_UPLOAD_SIZE,
        )
        return max_size_db_obj


class Upload(models.Model):

    objects = UploadManager()

    import_id = models.BigIntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=16)
    create_date = models.DateTimeField('create_date', default=now)
    date = models.DateTimeField('date', default=now)
    resource = models.ForeignKey(ResourceBase, null=True, on_delete=models.SET_NULL)
    upload_dir = models.TextField(null=True)
    name = models.CharField(max_length=64, null=True)
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
        ordering = ['-date']

    @property
    def get_session(self):
        if self.session:
            return pickle.loads(
                base64.decodebytes(self.session.encode('UTF-8')))

    def update_from_session(self, upload_session, resource: ResourceBase = None):
        self.session = base64.encodebytes(pickle.dumps(upload_session)).decode('UTF-8')
        self.name = upload_session.name
        self.user = upload_session.user
        self.date = now()

        if not self.upload_dir:
            self.upload_dir = os.path.dirname(upload_session.base_file)

        if resource and not self.resource:
            if not isinstance(resource, ResourceBase) and hasattr(resource, 'resourcebase_ptr'):
                self.resource = resource.resourcebase_ptr
            elif not isinstance(resource, ResourceBase):
                raise GeoNodeException("Invalid resource uploaded, plase select one of the available")
            else:
                self.resource = resource

            if upload_session.base_file and self.resource and self.resource.title:
                uploaded_files = upload_session.base_file[0]
                aux_files = uploaded_files.auxillary_files
                sld_files = uploaded_files.sld_files
                xml_files = uploaded_files.xml_files

                if self.resource and not self.resource.files:
                    files_to_upload = aux_files + sld_files + xml_files + [uploaded_files.base_file]
                    if len(files_to_upload):
                        ResourceBase.objects.upload_files(resource_id=self.resource.id, files=files_to_upload)
                        self.resource.refresh_from_db()

                # Now we delete the files from local file system
                # only if it does not match with the default temporary path
                if os.path.exists(self.upload_dir):
                    if settings.STATIC_ROOT != os.path.dirname(os.path.abspath(self.upload_dir)):
                        shutil.rmtree(self.upload_dir, ignore_errors=True)

        if "COMPLETE" == self.state:
            self.complete = True
        if self.resource and self.resource.processed:
            self.state = enumerations.STATE_RUNNING
        elif self.state in (enumerations.STATE_READY, enumerations.STATE_PENDING):
            self.state = upload_session.import_session.state
        self.save()

    @property
    def progress(self):
        if self.state in \
                (enumerations.STATE_READY, enumerations.STATE_INVALID, enumerations.STATE_INCOMPLETE):
            return 0.0
        elif self.state == enumerations.STATE_PENDING:
            return 33.0
        elif self.state == enumerations.STATE_WAITING:
            return 50.0
        elif self.state == enumerations.STATE_PROCESSED:
            return 100.0
        elif self.state in (enumerations.STATE_COMPLETE, enumerations.STATE_RUNNING):
            if self.resource and self.resource.processed and self.resource.state == enumerations.STATE_PROCESSED:
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
            return reverse('data_upload_delete', args=[self.id])
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
            if self.state not in (enumerations.STATE_COMPLETE, enumerations.STATE_PROCESSED):
                self.set_processing_state(enumerations.STATE_INVALID)
        if session and self.state != enumerations.STATE_INVALID:
            return f"{ogc_server_settings.LOCATION}rest/imports/{session.id}"
        else:
            return None

    def get_detail_url(self):
        if self.resource and self.resource.processed and self.resource.state == enumerations.STATE_PROCESSED:
            return getattr(self.resource, 'detail_url', None)
        else:
            return None

    def delete(self, *args, **kwargs):
        importer_locations = []
        super().delete(*args, **kwargs)
        try:
            session = gs_uploader.get_session(self.import_id)
        except (NotFound, Exception):
            session = None
        if session:
            for task in session.tasks:
                if getattr(task, 'data'):
                    importer_locations.append(
                        getattr(task.data, 'location'))
            try:
                session.delete()
            except Exception:
                logging.warning('error deleting upload session')

        # we delete directly the folder with the files of the resource
        if self.resource:
            for _file in self.resource.files:
                try:
                    if storage_manager.exists(_file):
                        storage_manager.delete(_file)
                except Exception as e:
                    logger.warning(e)

            # Do we want to delete the files also from the resource?
            ResourceBase.objects.filter(id=self.resource.id).update(files={})

        for _location in importer_locations:
            try:
                shutil.rmtree(_location)
            except Exception as e:
                logger.warning(e)

        # here we are deleting the local that soon will be removed
        if self.upload_dir and os.path.exists(self.upload_dir):
            try:
                shutil.rmtree(self.upload_dir)
            except Exception as e:
                logger.warning(e)

    def set_processing_state(self, state):
        if self.state != state:
            self.state = state
            Upload.objects.filter(id=self.id).update(state=state)
        if self.resource:
            self.resource.set_processing_state(state)
            if state != enumerations.STATE_PROCESSED:
                self.resource.set_dirty_state()

    def __str__(self):
        return f'Upload [{self.pk}] gs{self.import_id} - {self.name}, {self.user}'


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
