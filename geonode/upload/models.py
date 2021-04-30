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

import base64
import pickle
import shutil
import logging

from os import path

from django.urls import reverse
from django.db import models
from django.conf import settings
from django.utils.timezone import now

from geonode.layers.models import Layer
from geonode.geoserver.helpers import gs_uploader, ogc_server_settings
from gsimporter import NotFound


class UploadManager(models.Manager):

    def __init__(self):
        models.Manager.__init__(self)

    def update_from_session(self, upload_session):
        self.get(import_id=upload_session.import_session.id).update_from_session(
            upload_session)

    def create_from_session(self, user, import_session):
        return self.create(user=user,
                           import_id=import_session.id,
                           state=import_session.state)

    def get_incomplete_uploads(self, user):
        return self.filter(
            user=user,
            complete=False).exclude(
            state=Upload.STATE_INVALID)


class Upload(models.Model):
    objects = UploadManager()

    import_id = models.BigIntegerField(null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    # hold importer state or internal state (STATE_)
    state = models.CharField(max_length=16)
    date = models.DateTimeField('date', default=now)
    layer = models.ForeignKey(Layer, null=True, on_delete=models.SET_NULL)
    upload_dir = models.TextField(null=True)
    name = models.CharField(max_length=64, null=True)
    complete = models.BooleanField(default=False)
    # hold our serialized session object
    session = models.TextField(null=True, blank=True)
    # hold a dict of any intermediate Layer metadata - not used for now
    metadata = models.TextField(null=True)

    mosaic = models.BooleanField(default=False),
    append_to_mosaic_opts = models.BooleanField(default=False),
    append_to_mosaic_name = models.CharField(max_length=128, null=True),

    mosaic_time_regex = models.CharField(max_length=128, null=True)
    mosaic_time_value = models.CharField(max_length=128, null=True)

    mosaic_elev_regex = models.CharField(max_length=128, null=True)
    mosaic_elev_value = models.CharField(max_length=128, null=True)

    class Meta:
        ordering = ['-date']

    STATE_INVALID = 'INVALID'

    def get_session(self):
        if self.session:
            return pickle.loads(
                base64.decodebytes(self.session.encode('UTF-8')))

    def update_from_session(self, upload_session):
        self.state = upload_session.import_session.state
        self.date = now()
        if "COMPLETE" == self.state:
            self.complete = True
            self.session = None
        else:
            upload_session.user.first_name = upload_session.user.first_name
            upload_session.user.last_name = upload_session.user.last_name
            self.session = base64.encodebytes(pickle.dumps(upload_session)).decode('UTF-8')
        if self.upload_dir is None:
            self.upload_dir = path.dirname(upload_session.base_file)
            self.name = upload_session.layer_title or upload_session.name
        self.save()

    def get_resume_url(self):
        return f"{reverse('data_upload')}?id={self.import_id}"

    def get_delete_url(self):
        return reverse('data_upload_delete', args=[self.import_id])

    def get_import_url(self):
        return f"{ogc_server_settings.LOCATION}rest/imports/{self.import_id}"

    def delete(self, cascade=True):
        models.Model.delete(self)
        if cascade:
            try:
                session = gs_uploader.get_session(self.import_id)
            except NotFound:
                session = None
            if session:
                try:
                    session.delete()
                except Exception:
                    logging.exception('error deleting upload session')
            if self.upload_dir and path.exists(self.upload_dir):
                shutil.rmtree(self.upload_dir)

    def __str__(self):
        return f'Upload [{self.pk}] gs{self.import_id} - {self.name}, {self.user}'


class UploadFile(models.Model):
    upload = models.ForeignKey(Upload, null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="uploads")
    slug = models.SlugField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.slug}"

    def get_absolute_url(self):
        return reverse('data_upload_new', args=[self.slug, ])

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(UploadFile, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(UploadFile, self).delete(*args, **kwargs)
