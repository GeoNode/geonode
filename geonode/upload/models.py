# -*- coding: utf-8 -*-
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

from slugify import slugify
from gsimporter.api import NotFound

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.files import File
from django.utils.timezone import now
from django.core.files.storage import FileSystemStorage

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
        self.get(
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
        return self.filter(user=user).exclude(
            state=Upload.STATE_PROCESSED)


class Upload(models.Model):

    objects = UploadManager()

    import_id = models.BigIntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    # hold importer state or internal state (STATE_)
    state = models.CharField(max_length=16)
    date = models.DateTimeField('date', default=now)
    layer = models.ForeignKey(Layer, null=True, on_delete=models.CASCADE)
    upload_dir = models.TextField(null=True)
    name = models.CharField(max_length=64, null=True)
    complete = models.BooleanField(default=False)
    # hold our serialized session object
    session = models.TextField(null=True, blank=True)
    # hold a dict of any intermediate Layer metadata - not used for now
    metadata = models.TextField(null=True)

    mosaic = models.BooleanField(default=False)
    append_to_mosaic_opts = models.BooleanField(default=False)
    append_to_mosaic_name = models.CharField(max_length=128, null=True)

    mosaic_time_regex = models.CharField(max_length=128, null=True)
    mosaic_time_value = models.CharField(max_length=128, null=True)

    mosaic_elev_regex = models.CharField(max_length=128, null=True)
    mosaic_elev_value = models.CharField(max_length=128, null=True)

    class Meta:
        ordering = ['-date']

    STATE_READY = "READY"
    STATE_RUNNING = "RUNNING"
    STATE_PENDING = "PENDING"
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
        self.state = upload_session.import_session.state
        self.name = upload_session.name
        self.user = upload_session.user
        self.date = now()

        if not self.upload_dir:
            self.upload_dir = os.path.dirname(upload_session.base_file)

        if layer and not self.layer:
            self.layer = layer
            if upload_session.base_file:
                uploaded_files = upload_session.base_file[0]
                base_file = uploaded_files.base_file
                aux_files = uploaded_files.auxillary_files
                sld_files = uploaded_files.sld_files
                xml_files = uploaded_files.xml_files

                assigned_name = UploadFile.objects.create_from_upload(
                    self,
                    base_file,
                    None,
                    base=True).name

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

        if "COMPLETE" == self.state:
            self.complete = True

        self.save()

    @property
    def progress(self):
        if self.state in \
        (Upload.STATE_READY, Upload.STATE_INVALID, Upload.STATE_INCOMPLETE):
            return 0.0
        elif self.state == Upload.STATE_PENDING:
            return 33.0
        elif self.state == Upload.STATE_RUNNING:
            return 66.0
        elif self.complete:
            if self.layer and self.layer.processed:
                self.state = Upload.STATE_PROCESSED
                Upload.objects.filter(id=self.id).update(state=Upload.STATE_PROCESSED)
                return 100.0
            else:
                return 80.0

    def get_resume_url(self):
        try:
            gs_uploader.get_session(self.import_id)
        except NotFound:
            if self.state not in (Upload.STATE_COMPLETE, Upload.STATE_PROCESSED):
                self.state = Upload.STATE_INVALID
                Upload.objects.filter(id=self.id).update(state=Upload.STATE_INVALID)
        return f"{reverse('data_upload')}?id={self.import_id}"

    def get_delete_url(self):
        return reverse('data_upload_delete', args=[self.import_id])

    def get_import_url(self):
        return f"{ogc_server_settings.LOCATION}rest/imports/{self.import_id}"

    def delete(self, *args, **kwargs):
        importer_locations = []
        upload_files = [_file.file for _file in UploadFile.objects.filter(upload=self)]
        super(Upload, self).delete(*args, **kwargs)
        try:
            session = gs_uploader.get_session(self.import_id)
        except NotFound:
            session = None
        if session:
            for task in session.tasks:
                if getattr(task, 'data'):
                    importer_locations.append(
                        getattr(task.data, 'location'))
            try:
                session.delete()
            except Exception:
                logging.exception('error deleting upload session')
        if self.layer:
            try:
                self.layer.delete()
            except Exception:
                logging.exception('error deleting upload layer')
        for _file in upload_files:
            try:
                if os.path.isfile(_file.path):
                    os.remove(_file.path)
            except Exception as e:
                logger.exception(e)
        for _location in importer_locations:
            try:
                shutil.rmtree(_location)
            except Exception as e:
                logger.exception(e)
        if self.upload_dir and os.path.exists(self.upload_dir):
            try:
                shutil.rmtree(self.upload_dir)
            except Exception as e:
                logger.exception(e)

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
        super(UploadFile, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(UploadFile, self).delete(*args, **kwargs)
