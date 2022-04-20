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
import shutil
import pickle
import logging

from slugify import slugify
from gsimporter.api import NotFound

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.files import File
from django.utils.timezone import now
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinLengthValidator, MinValueValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer
from geonode.geoserver.helpers import gs_uploader, ogc_server_settings

logger = logging.getLogger(__name__)


class UploadManager(models.Manager):

    def __init__(self):
        models.Manager.__init__(self)

    def invalidate_from_session(self, upload_session):
        return self.filter(
            user=upload_session.user,
            import_id=upload_session.import_session.id
        ).update(state=Upload.STATE_INVALID)

    def update_from_session(self, upload_session, layer=None):
        return self.get(
            user=upload_session.user,
            name=upload_session.name,
            import_id=upload_session.import_session.id).update_from_session(
            upload_session, layer=layer)

    def create_from_session(self, user, import_session):
        return self.create(
            user=user,
            name=import_session.name,
            import_id=import_session.id,
            state=import_session.state)

    def get_incomplete_uploads(self, user):
        return self.filter(user=user).exclude(state=Upload.STATE_PROCESSED).exclude(
            state=Upload.STATE_WAITING)


class UploadSizeLimitManager(models.Manager):

    def create_default_limit(self):
        max_size_db_obj = self.create(
            slug="total_upload_size_sum",
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


class Upload(models.Model):

    objects = UploadManager()

    import_id = models.BigIntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=16)
    create_date = models.DateTimeField('create_date', default=now)
    date = models.DateTimeField('date', default=now)
    layer = models.ForeignKey(Layer, null=True, on_delete=models.SET_NULL)
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
        ordering = ['-date']

    STATE_READY = "READY"
    STATE_RUNNING = "RUNNING"
    STATE_PENDING = "PENDING"
    STATE_WAITING = "WAITING"
    STATE_INCOMPLETE = "INCOMPLETE"
    STATE_COMPLETE = "COMPLETE"
    STATE_INVALID = "INVALID"
    STATE_PROCESSED = "PROCESSED"

    @property
    def get_session(self):
        if self.session:
            return pickle.loads(
                base64.decodebytes(self.session.encode('UTF-8')))

    def update_from_session(self, upload_session, layer=None):
        self.session = base64.encodebytes(pickle.dumps(upload_session)).decode('UTF-8')
        self.name = upload_session.name
        self.user = upload_session.user
        self.date = now()

        if not self.upload_dir:
            self.upload_dir = os.path.dirname(upload_session.base_file)

        if layer and not self.layer:
            self.layer = layer

            if upload_session.base_file and self.layer and self.layer.name:
                uploaded_files = upload_session.base_file[0]
                base_file = uploaded_files.base_file
                aux_files = uploaded_files.auxillary_files
                sld_files = uploaded_files.sld_files
                xml_files = uploaded_files.xml_files

                if self.store_spatial_files and not UploadFile.objects.filter(upload=self, file=base_file).count():
                    uploaded_file = UploadFile.objects.create_from_upload(
                        self,
                        base_file,
                        None,
                        base=True)

                    if uploaded_file and uploaded_file.name:
                        assigned_name = uploaded_file.name
                        for _f in aux_files:
                            UploadFile.objects.create_from_upload(
                                self,
                                _f,
                                assigned_name)

                        for _f in sld_files:
                            UploadFile.objects.create_from_upload(
                                self,
                                _f,
                                assigned_name)

                        for _f in xml_files:
                            UploadFile.objects.create_from_upload(
                                self,
                                _f,
                                assigned_name)

        if self.layer:
            if self.layer.processed:
                self.state = Upload.STATE_PROCESSED
            else:
                self.state = Upload.STATE_RUNNING
        elif self.state in (Upload.STATE_READY, Upload.STATE_PENDING):
            self.state = upload_session.import_session.state
            if self.state == Upload.STATE_COMPLETE:
                self.complete = True

        self.save()
        return self.get_session

    @property
    def progress(self):
        if self.state in \
                (Upload.STATE_READY, Upload.STATE_INVALID, Upload.STATE_INCOMPLETE):
            return 0.0
        elif self.state == Upload.STATE_PENDING:
            return 33.0
        elif self.state == Upload.STATE_WAITING:
            return 50.0
        elif self.state == Upload.STATE_PROCESSED:
            if self.layer and self.layer.processed:
                return 100.0
            return 80.0
        elif self.state in (Upload.STATE_COMPLETE, Upload.STATE_RUNNING):
            if self.layer and self.layer.processed and self.layer.instance_is_processed:
                self.state = Upload.STATE_PROCESSED
                self.save()
                return 90.0
            return 80.0

    def set_resume_url(self, resume_url):
        if self.resume_url != resume_url:
            self.resume_url = resume_url
            Upload.objects.filter(id=self.id).update(resume_url=resume_url)

    def get_resume_url(self):
        if self.state == Upload.STATE_WAITING and self.import_id:
            return self.resume_url
        return None

    def get_delete_url(self):
        if self.state != Upload.STATE_PROCESSED:
            return reverse('data_upload_delete', args=[self.id])
        return None

    def get_import_url(self):
        session = None
        try:
            if not self.import_id:
                raise NotFound
            session = self.get_session.import_session
            if not session or session.state != Upload.STATE_COMPLETE:
                session = gs_uploader.get_session(self.import_id)
        except (NotFound, Exception):
            if not session and self.state not in (Upload.STATE_COMPLETE, Upload.STATE_PROCESSED):
                self.set_processing_state(Upload.STATE_INVALID)
        if session and self.state != Upload.STATE_INVALID:
            return f"{ogc_server_settings.LOCATION}rest/imports/{session.id}"
        else:
            return None

    def get_detail_url(self):
        if self.layer and self.layer.processed:
            return getattr(self.layer, 'detail_url', None)
        else:
            return None

    def delete(self, *args, **kwargs):
        upload_files = [_file.file for _file in UploadFile.objects.filter(upload=self)]
        super().delete(*args, **kwargs)

        # we delete directly the folder with the files of the resource
        if self.layer:
            for _file in upload_files:
                try:
                    if os.path.isfile(_file.path):
                        os.remove(_file.path)
                except Exception as e:
                    logger.warning(e)

        # here we are deleting the local that soon will be removed
        if self.upload_dir and os.path.exists(self.upload_dir):
            shutil.rmtree(self.upload_dir, ignore_errors=True)

    def set_processing_state(self, state):
        if self.state != state:
            self.state = state
            Upload.objects.filter(id=self.id).update(state=state)
        if self.layer:
            self.layer.set_processing_state(state)

    def __str__(self):
        return f'Upload [{self.pk}] gs{self.import_id} - {self.name}, {self.user}'


class UploadFileManager(models.Manager):

    def __init__(self):
        models.Manager.__init__(self)

    def create_from_upload(self,
                           upload,
                           base_file,
                           assigned_name,
                           base=False):
        try:
            if os.path.isfile(base_file) and os.path.exists(base_file):
                with open(base_file, 'rb') as f:
                    file_name, type_name = os.path.splitext(os.path.basename(base_file))
                    file = File(
                        f, name=f'{assigned_name or upload.layer.name}{type_name}')

                    # save the system assigned name for the remaining files
                    if not assigned_name:
                        the_file = file.name
                        assigned_name = os.path.splitext(os.path.basename(the_file))[0]

                    return self.create(
                        upload=upload,
                        file=file,
                        name=assigned_name,
                        slug=slugify(file_name),
                        base=base)
        except Exception as e:
            logger.exception(e)


class UploadFile(models.Model):

    objects = UploadFileManager()

    upload = models.ForeignKey(Upload, null=True, blank=True, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=4096, blank=True)
    name = models.CharField(max_length=4096, blank=True)
    base = models.BooleanField(default=False)
    file = models.FileField(
        upload_to='layers/%Y/%m/%d',
        storage=FileSystemStorage(
            base_url=settings.LOCAL_MEDIA_URL),
        max_length=4096)

    def __str__(self):
        return str(self.slug)

    def get_absolute_url(self):
        return reverse('data_upload_new', args=[self.slug, ])

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super().delete(*args, **kwargs)


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
    max_size = models.BigIntegerField(
        help_text=_("The maximum file size allowed for upload (bytes)."),
        default=settings.DEFAULT_MAX_UPLOAD_SIZE,
        validators=[MinValueValidator(limit_value=0)],
    )

    @property
    def max_size_label(self):
        return filesizeformat(self.max_size)

    def __str__(self):
        return f'UploadSizeLimit for "{self.slug}" (max_size: {self.max_size_label})'

    class Meta:
        ordering = ("slug",)
