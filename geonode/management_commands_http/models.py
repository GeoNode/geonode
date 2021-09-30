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
from django.utils.translation import ugettext_lazy as _

from geonode.management_commands_http.utils.commands import (
    get_management_commands_apps,
)


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

    args = models.JSONField(
        blank=True, default=list,
        verbose_name=_('Positional Arguments'),
        help_text=_(
            'JSON encoded positional arguments '
            '(Example: ["arg1", "arg2"])'
        ),
    )
    kwargs = models.JSONField(
        blank=True, default=dict,
        verbose_name=_('Keyword Arguments'),
        help_text=_(
            'JSON encoded keyword arguments '
            '(Example: {"argument": "value"})'
        ),
    )

    celery_result_id = models.UUIDField(null=True, blank=True)
    output_message = models.TextField(null=True)

    status = models.CharField(
        choices=STATUS_CHOICES,
        default=CREATED,
        max_length=max([len(e[0]) for e in STATUS_CHOICES]),
    )

    def clean(self):
        available_commands = get_management_commands_apps()
        if self.command not in available_commands:
            raise ValueError("Command not found")
        if not self.app_name:
            self.app_name = available_commands[self.command]
        return super().clean()

    def __str__(self):
        return (
            f"ManagementCommandJob"
            f"({self.id}, {self.command}, {self.user}, {self.created_at})"
        )
