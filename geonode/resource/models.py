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
import uuid

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from geonode.resource.enumerator import ExecutionRequestAction


class ExecutionRequest(models.Model):
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"
    STATUS_RUNNING = "running"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = [
        (STATUS_READY, _("ready")),
        (STATUS_FAILED, _("failed")),
        (STATUS_RUNNING, _("running")),
        (STATUS_FINISHED, _("finished")),
    ]

    ACTION_CHOICES = [(str(v.value), str(v.value)) for v in ExecutionRequestAction]

    exec_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_READY)
    func_name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True)
    last_updated = models.DateTimeField(auto_now=True)

    input_params = models.JSONField(blank=True, default=dict)
    output_params = models.JSONField(blank=True, default=dict)

    geonode_resource = models.ForeignKey("base.ResourceBase", null=True, on_delete=models.SET_NULL)

    step = models.CharField(max_length=250, null=True, default=None)
    log = models.TextField(null=True, default=None)
    name = models.CharField(
        max_length=250, null=True, default=None, help_text="Human readable name for the execution request"
    )
    action = models.CharField(
        max_length=50, choices=ACTION_CHOICES, default=ExecutionRequestAction.UNKNOWN.value, null=True
    )

    source = models.CharField(max_length=250, null=True, default=None)
