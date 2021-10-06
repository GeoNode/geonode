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
import io
import sys

from django.core.management import call_command
from django.utils import timezone
from rest_framework import exceptions

from geonode.management_commands_http.models import ManagementCommandJob


class JobRunner:
    """
    With-statement context used to execute a ManagementCommandJob.
    It handles status, start_time and end_time.
    And duplicates stdout and stderr to a specified file stream.
    """

    def __init__(self, job, stream: io.StringIO, celery_result_id: str):
        self.job = job
        self.stream = stream
        self.celery_result_id = celery_result_id

        self.stdout = sys.stdout
        self.stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

    def write(self, data):
        self.stream.write(data)
        self.stdout.write(data)

    def flush(self):
        self.stream.flush()

    def __enter__(self):
        self.job.status = ManagementCommandJob.STARTED
        if self.celery_result_id:
            self.job.celery_result_id = self.celery_result_id
        self.job.start_time = timezone.now()
        self.job.save()
        return self.job

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.job.status = ManagementCommandJob.FINISHED
        self.job.end_time = timezone.now()
        self.job.output_message = self.stream.getvalue()
        self.job.save()


def run_management_command(job_id, async_result_id: str = ""):
    """
    Loads the job model from database and run it using `call_command` inside a
    context responsible to updating the status and redirecting stdout and
    stderr.
    """
    try:
        job = ManagementCommandJob.objects.get(id=job_id)
    except ManagementCommandJob.DoesNotExist:
        raise exceptions.NotFound(
            f"ManagementCommandJob with id {job_id} was not found."
        )
    with io.StringIO() as output:
        with JobRunner(job, output, async_result_id):
            call_command(job.command, *job.args, **job.kwargs, stdout=output)
