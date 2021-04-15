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

import json
import logging

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import (
    IntervalSchedule,
    PeriodicTask,
)
from jsonfield import JSONField

from .config import HARVESTER_CLASSES
from .harvesters.base import BaseHarvester

logger = logging.getLogger(__name__)


class Harvester(models.Model):
    name = models.CharField(max_length=100, help_text=_("Harvester name"))
    remote_url = models.URLField(
        help_text=_("Base URL of the remote service that is to be harvested"))
    scheduling_enabled = models.BooleanField(
        help_text=_(
            "Whether to periodically schedule this harvester to look for resources on "
            "the remote service"
        ),
        default=True
    )
    update_frequency = models.PositiveIntegerField(
        help_text=_(
            "How often (in minutes) should new harvesting sessions be automatically "
            "scheduled? Setting this value to zero has the same effect as setting "
            "`scheduling_enabled` to False "
        ),
        default=60
    )
    default_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_("Default owner of harvested resources")
    )
    default_access_permissions = JSONField(
        help_text=_("Default access permissions of harvested resources"))
    harvester_type = models.CharField(
        max_length=255,
        help_text=_(
            "Harvester class used to perform harvesting sessions. New harvester types "
            "can be added by an admin by changing the main GeoNode `settings.py` file"
        ),
        choices=(((i, i) for i in HARVESTER_CLASSES)),
        default=HARVESTER_CLASSES[0]
    )
    harvester_type_specific_configuration = JSONField(
        help_text=_(
            "Configuration specific to each harvester type. Please consult GeoNode "
            "documentation on harvesting for more info.")
    )
    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        help_text=_("Periodic task used to configure harvest scheduling"),
        null=True,
        blank=True,
        editable=False,
    )

    def setup_periodic_task(self) -> None:
        """Setup the related `periodic_task` for the instance.

        This function is automatically called by the
        `signals.create_or_update_periodic_task` signal handler whenever a new
        instance is saved (handler is listening to the `post_save` signal). It creates
        the related `PeriodicTask` object in order to allow the harvester to be
        scheduled by celery beat.

        """

        logger.debug("inside setup_periodic_task")
        schedule_interval, created = IntervalSchedule.objects.get_or_create(
            every=self.update_frequency,
            period="minutes"
        )
        self.periodic_task = PeriodicTask.objects.create(
            name=_(self.name),
            task="geonode.harvesting.tasks.harvesting_session_dispatcher",
            interval=schedule_interval,
            args=json.dumps([self.id]),
            start_time=timezone.now()
        )
        self.save()

    def get_harvester_worker(self) -> BaseHarvester:
        logger.debug("Inside get_harvester_worker")
        worker_class = import_string(self.harvester_type)
        return worker_class.from_django_record(self)

    # TODO: This does not work OK when deletion is done via the django admin - Implement via post_delete signal instead
    #
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.on_delete
    #
    def delete(self, *args, **kwargs):
        """Delete the corresponding periodic task too, if it exists."""
        if self.periodic_task is not None:
            self.periodic_task.delete()
        return super().delete(*args, **kwargs)


class HarvestingSession(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(null=True, blank=True)
    records_harvested = models.IntegerField(default=0)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="harvesting_sessions"
    )