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
import json
import logging
import sys

from django.core.management import (
    call_command,
    get_commands,
    load_command_class
)
from django.utils import timezone

from .models import ManagementCommandJob

logger = logging.getLogger(__name__)


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
    job = ManagementCommandJob.objects.get(id=job_id)
    with io.StringIO() as output:
        with JobRunner(job, output, async_result_id):
            job_args = json.loads(job.args)
            job_kwargs = json.loads(job.kwargs)
            call_command(job.command, *job_args, **job_kwargs, stdout=output)


def get_management_commands():
    """
    Get the list of all management commands, filter by the attr injected by the
    decorator and returns a dict with the app and command class.
    """
    available_commands = {}
    mngmt_commands = get_commands()

    for name, app_name in mngmt_commands.items():
        # Load command
        try:
            command_class = load_command_class(app_name, name)
        except (ImportError, AttributeError) as exception:
            logging.info(
                f'Command "{name}" from app "{app_name}" cannot be listed or ' f'used by http, exception: "{exception}"'
            )
            continue

        # Verify if its exposed
        is_exposed = hasattr(command_class, "expose_command_over_http") and command_class.expose_command_over_http
        if is_exposed:
            available_commands[name] = {
                "app": app_name,
                "command_class": command_class,
            }

    return available_commands


def get_management_command_details(command_class, command_name):
    """
    Get the help output of the management command.
    """
    parser = command_class.create_parser('', command_name)
    with io.StringIO() as output:
        parser.print_help(output)
        cmd_help_output = output.getvalue()
    return cmd_help_output
