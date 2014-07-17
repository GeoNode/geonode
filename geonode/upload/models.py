#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import cPickle as pickle
import logging
import shutil
from datetime import datetime
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from geonode.layers.models import Layer
from geonode.geoserver.helpers import gs_uploader, ogc_server_settings
from gsimporter import NotFound
from os import path


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    # hold importer state or internal state (STATE_)
    state = models.CharField(max_length=16)
    date = models.DateTimeField('date', default=datetime.now)
    layer = models.ForeignKey(Layer, null=True)
    upload_dir = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=64, null=True)
    complete = models.BooleanField(default=False)
    # hold our serialized session object
    session = models.TextField(null=True)
    # hold a dict of any intermediate Layer metadata - not used for now
    metadata = models.TextField(null=True)

    class Meta:
        ordering = ['-date']

    STATE_INVALID = 'INVALID'

    def get_session(self):
        if self.session:
            return pickle.loads(str(self.session))

    def update_from_session(self, upload_session):
        self.state = upload_session.import_session.state
        self.date = datetime.now()
        if "COMPLETE" == self.state:
            self.complete = True
            self.session = None
        else:
            self.session = pickle.dumps(upload_session)
        if self.upload_dir is None:
            self.upload_dir = path.dirname(upload_session.base_file)
            self.name = upload_session.layer_title or upload_session.name
        self.save()

    def get_resume_url(self):
        return reverse('data_upload') + "?id=%s" % self.import_id

    def get_delete_url(self):
        return reverse('data_upload_delete', args=[self.import_id])

    def get_import_url(self):
        return "%srest/imports/%s" % (
            ogc_server_settings.LOCATION, self.import_id)

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
                except:
                    logging.exception('error deleting upload session')
            if self.upload_dir and path.exists(self.upload_dir):
                shutil.rmtree(self.upload_dir)

    def __unicode__(self):
        return 'Upload [%s] gs%s - %s, %s' % (self.pk,
                                              self.import_id,
                                              self.name,
                                              self.user)


class UploadFile(models.Model):
    upload = models.ForeignKey(Upload, null=True, blank=True)
    file = models.FileField(upload_to="uploads")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.slug

    @models.permalink
    def get_absolute_url(self):
        return ('data_upload_new', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(UploadFile, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(UploadFile, self).delete(*args, **kwargs)
