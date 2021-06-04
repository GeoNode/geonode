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
from geonode.base.models import ResourceBase
from geonode.storage.manager import storage_manager
import os
import json
import base64
import pickle
import shutil
import logging

from gsimporter.api import NotFound

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now
from geonode import GeoNodeException
from geonode.base import enumerations
from geonode.tasks.tasks import AcquireLock
from geonode.geoserver.helpers import gs_uploader, ogc_server_settings

from .utils import next_step_response, get_next_step

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

    @property
    def get_session(self):
        if self.session:
            return pickle.loads(
                base64.decodebytes(self.session.encode('UTF-8')))

    def update_from_session(self, upload_session, resource: ResourceBase = None):
        self.session = base64.encodebytes(pickle.dumps(upload_session)).decode('UTF-8')
        self.state = upload_session.import_session.state
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
                        shutil.rmtree(self.upload_dir)

        if "COMPLETE" == self.state:
            self.complete = True

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
        elif self.complete or self.state in (enumerations.STATE_COMPLETE, enumerations.STATE_RUNNING):
            if self.resource and self.resource.processed:
                self.set_processing_state(enumerations.STATE_PROCESSED)
                return 100.0
            elif self.state == enumerations.STATE_RUNNING:
                return 66.0
            return 80.0

    def get_resume_url(self):
        if self.state == enumerations.STATE_WAITING and self.import_id:
            return f"{reverse('data_upload')}?id={self.import_id}"
        elif self.state not in (enumerations.STATE_RUNNING, enumerations.STATE_PROCESSED):
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
            if session:
                lock_id = f'{self.import_id}'
                with AcquireLock(lock_id) as lock:
                    if lock.acquire() is True:
                        try:
                            content = next_step_response(None, self.get_session).content
                            if isinstance(content, bytes):
                                content = content.decode('UTF-8')
                            response_json = json.loads(content)
                            if response_json['success'] and 'redirect_to' in response_json:
                                if 'upload/final' not in response_json['redirect_to'] and 'upload/check' not in response_json['redirect_to']:
                                    self.set_processing_state(enumerations.STATE_WAITING)
                                    return f"{reverse('data_upload')}?id={self.import_id}"
                                else:
                                    next = get_next_step(self.get_session)
                                    if not self.resource and session.state == enumerations.STATE_COMPLETE:
                                        if next == 'check' or (next == 'final' and self.state == enumerations.STATE_PENDING):
                                            from .views import final_step_view
                                            final_step_view(None, self.get_session)
                                            self.set_processing_state(enumerations.STATE_RUNNING)
                        except (NotFound, Exception) as e:
                            logger.exception(e)
                            if self.state not in (enumerations.STATE_COMPLETE, enumerations.STATE_PROCESSED):
                                self.set_processing_state(enumerations.STATE_INVALID)
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
        if self.resource and self.state == enumerations.STATE_PROCESSED:
            return getattr(self.resource, 'detail_url', None)
        else:
            return None

    def delete(self, *args, **kwargs):
        importer_locations = []
        super(Upload, self).delete(*args, **kwargs)
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
                    dirname = os.path.dirname(_file)
                    if storage_manager.exists(dirname):
                        storage_manager.delete(dirname)
                        break
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
        self.state = True
        Upload.objects.filter(id=self.id).update(state=state)
        if self.resource:
            self.resource.set_processing_state(state)

    def __str__(self):
        return f'Upload [{self.pk}] gs{self.import_id} - {self.name}, {self.user}'
