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
from celery import shared_task
from geonode.management_commands_http.utils.job_runner import (
    run_management_command
)


@shared_task(
    bind=True,
    name="geonode.management_commands_http.tasks.run_management_command_async",
    queue="management_commands_http",
    ignore_result=False,
)
def run_management_command_async(self, job_id):
    """
    Celery Task responsible to run the management command.
    It justs sends the `job_id` arg to a function that gonna call
    `django.core.management.call_command` with all the required setup.
    """
    run_management_command(job_id, async_result_id=self.request.id)
