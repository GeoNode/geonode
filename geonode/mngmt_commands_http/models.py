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
from django.contrib.auth import get_user_model
from django.db import models


class ManagementCommandJob(models.Model):
    """
    Stores the requests to run a management command using this app.
    It allows us to have more control over the celery TaskResults.
    """

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    FINISHED = "FINISHED"
    STATUS_CHOICES = (
        (CREATED, "Created"),
        (QUEUED, "Queued"),
        (STARTED, "Started"),
        (FINISHED, "Finished"),
    )
    command = models.CharField(max_length=250, null=False)
    app_name = models.CharField(max_length=250, null=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    modified_at = models.DateTimeField(auto_now=True)

    # NOTE: Change to JsonField when updating to django 3.1
    args = models.TextField(default="[]", blank=True)
    kwargs = models.TextField(default="{}", blank=True)

    celery_result_id = models.UUIDField(null=True, blank=True)
    output_message = models.TextField(null=True)

    status = models.CharField(
        choices=STATUS_CHOICES,
        default=CREATED,
        max_length=max([len(e[0]) for e in STATUS_CHOICES]),
    )

    def __str__(self):
        return (
            f"ManagementCommandJob"
            f"({self.id}, {self.command}, {self.user}, {self.created_at})"
        )

    def start_task(self):
        from .tasks import run_management_command_async
        self.status = self.QUEUED
        self.save()
        run_management_command_async.delay(job_id=self.id)

    def stop_task(self):
        from geonode.celery_app import app as celery_app
        celery_app.control.terminate(self.celery_result_id)

    @property
    def celery_task_meta(self):
        from .tasks import run_management_command_async

        if not self.celery_result_id:
            return {}
        async_result = run_management_command_async.AsyncResult(self.celery_result_id)
        task_meta = async_result.backend.get_task_meta(self.celery_result_id)
        return task_meta
