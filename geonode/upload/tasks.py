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
from datetime import datetime
import logging

from django.conf import settings
from django.utils.timezone import timedelta

from geonode.celery_app import app

logger = logging.getLogger(__name__)

UPLOAD_SESSION_EXPIRY_HOURS = getattr(settings, "UPLOAD_SESSION_EXPIRY_HOURS", 24)


@app.task(bind=False, acks_late=False, queue="clery_cleanup", ignore_result=True)
def cleanup_celery_task_entries():
    from django_celery_results.models import TaskResult

    result_obj = TaskResult.objects.filter(date_done__lte=(datetime.today() - timedelta(days=7)))
    logger.error(f"Total celery task to be deleted: {result_obj.count()}")
    result_obj.delete()
