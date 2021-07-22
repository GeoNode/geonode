# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from datetime import timedelta, datetime
from django.test import TestCase
from django.conf import settings

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.upload.tasks import delete_incomplete_session_uploads
from geonode.tests.factories import UploadFactory
from geonode.upload.models import Upload


class TasksTest(GeoNodeBaseTestSupport):

    """
    Tests geonode.messaging
    """

    def setUp(self):
        super(TasksTest, self).setUp()

        self.adm_un = "admin"
        self.adm_pw = "admin"


class TestDeleteIncompleteSessionUploadsTask(TestCase):
    def setUp(self):
        self.expiry_time = datetime.now() - timedelta(hours=settings.SESSION_EXPIRY_HOURS)
        self.minutes_before = self.expiry_time - timedelta(minutes=2)
        self.minutes_after = self.expiry_time - timedelta(minutes=-2)

        # Uploads either PROCESSED or within expiry time
        self.uploads_to_survive = [
            UploadFactory(state=Upload.STATE_INVALID, date=self.minutes_after),
            UploadFactory(state=Upload.STATE_COMPLETE, date=self.minutes_after),
            UploadFactory(state=Upload.STATE_PROCESSED, date=self.minutes_after),
            UploadFactory(state=Upload.STATE_PROCESSED, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_INCOMPLETE),
            UploadFactory(state=Upload.STATE_PENDING),
            UploadFactory(state=Upload.STATE_READY),
            UploadFactory(state=Upload.STATE_RUNNING),
            UploadFactory(state=Upload.STATE_WAITING)
        ]
        self.survived_upload_ids = {u.id for u in self.uploads_to_survive}

        # Uploads not PROCESSED and before expiry time
        self.uploads_to_be_deleted = [
            UploadFactory(state=Upload.STATE_INVALID, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_COMPLETE, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_INCOMPLETE, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_PENDING, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_READY, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_RUNNING, date=self.minutes_before),
            UploadFactory(state=Upload.STATE_WAITING, date=self.minutes_before)
        ]
        self.delete_upload_ids = {u.id for u in self.uploads_to_be_deleted}


    def test_only_expected_uploads_are_deleted(self):
        uploads = Upload.objects.all()
        upload_ids = {u.id for u in uploads}
        self.assertEqual(uploads.count(), len(self.uploads_to_survive) + len(self.uploads_to_be_deleted))
        self.assertEqual(upload_ids, self.survived_upload_ids.union(self.delete_upload_ids))

        delete_incomplete_session_uploads.delay()
        uploads = Upload.objects.all()
        upload_ids = {u.id for u in uploads}
        # Only uploads_to_survive are not deleted
        self.assertEqual(uploads.count(), len(self.uploads_to_survive))
        self.assertEqual(upload_ids, self.survived_upload_ids)
