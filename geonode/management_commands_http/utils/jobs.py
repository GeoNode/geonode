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
from geonode.celery_app import app as celery_app
from geonode.management_commands_http.tasks import run_management_command_async
from geonode.management_commands_http.models import ManagementCommandJob


def start_task(job: ManagementCommandJob):
    job.status = job.QUEUED
    job.save()
    run_management_command_async.delay(job_id=job.id)


def stop_task(job: ManagementCommandJob):
    celery_app.control.terminate(job.celery_result_id)


def get_celery_task_meta(job: ManagementCommandJob):
    if not job.celery_result_id:
        return {}
    async_result = run_management_command_async.AsyncResult(
        job.celery_result_id
    )
    task_meta = async_result.backend.get_task_meta(job.celery_result_id)
    return task_meta
