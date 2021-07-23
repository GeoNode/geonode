# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from django.utils.timezone import timedelta, now
from django.conf import settings
from celery.schedules import crontab

from geonode.upload.models import Upload
from geonode.celery_app import app


@app.task
def delete_incomplete_session_uploads():
    """ Task is to delete resources which didn't complete the processes within
    their session. We have to make sure To NOT Delete those Unprocessed Ones,
    which are in live sessions. """

    expiry_time = now() - timedelta(hours=settings.SESSION_EXPIRY_HOURS)
    Upload.objects.exclude(state=Upload.STATE_PROCESSED).exclude(date__gt=expiry_time).delete()

settings.CELERY_BEAT_SCHEDULE["delete-incomplete-session-resources"] = {
    "task": "geonode.upload.tasks.delete_incomplete_session_uploads",
    "schedule": crontab(hour='*/12'),
}