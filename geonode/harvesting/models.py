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

import jsonschema.exceptions
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import (
    IntervalSchedule,
    PeriodicTask,
)
from jsonfield import JSONField

from . import utils
from .config import HARVESTER_CLASSES
from .harvesters.base import BaseHarvesterWorker

logger = logging.getLogger(__name__)


class Harvester(models.Model):
    STATUS_READY = "ready"
    STATUS_UPDATING_HARVESTABLE_RESOURCES = "updating-harvestable-resources"
    STATUS_PERFORMING_HARVESTING = "harvesting-resources"
    STATUS_CHECKING_AVAILABILITY = "checking-availability"
    STATUS_CHOICES = [
        (STATUS_READY, _("ready")),
        (STATUS_UPDATING_HARVESTABLE_RESOURCES, _("updating-harvestable-resources")),
        (STATUS_PERFORMING_HARVESTING, _("harvesting-resources")),
        (STATUS_CHECKING_AVAILABILITY, _("checking-availability")),
    ]

    name = models.CharField(max_length=100, help_text=_("Harvester name"))
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_READY)
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
    remote_available = models.BooleanField(
        help_text=_("Whether the remote service is known to be available or not"),
        editable=False,
        default=False
    )
    check_availability_frequency = models.PositiveIntegerField(
        help_text=_(
            "How often (in minutes) should the remote service be checked for "
            "availability?"
        ),
        default=30
    )
    last_checked_availability = models.DateTimeField(
        help_text=_("Last time the remote server was checked for availability"),
        blank=True,
        null=True
    )
    last_checked_harvestable_resources = models.DateTimeField(
        help_text=_(
            "Last time the remote server was checked for harvestable resources"),
        blank=True,
        null=True,
    )
    last_check_harvestable_resources_message = models.TextField(blank=True)
    default_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_("Default owner of harvested resources")
    )
    default_access_permissions = JSONField(
        help_text=_("Default access permissions of harvested resources"))
    harvest_new_resources_by_default = models.BooleanField(
        help_text=_(
            "Should new resources be harvested automatically without "
            "explicit selection?"
        ),
        default=False,
    )
    delete_orphan_resources_automatically = models.BooleanField(
        help_text=_(
            "Orphan resources are those that have previously been created by means of "
            "a harvesting operation but that GeoNode can no longer find on the remote "
            "service being harvested. Should these resources be deleted from GeoNode "
            "automatically? This also applies to when a harvester configuration is "
            "deleted, in which case all of the resources that originated from that "
            "harvester are now considered to be orphan."
        ),
        default=False,
    )
    last_updated = models.DateTimeField(
        help_text=_("Date of last update to the harvester configuration."),
        auto_now=True
    )
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
            "documentation on harvesting for more info. This field is mandatory, so at "
            "the very least an empty object (i.e. {}) must be supplied."
        )
    )
    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        help_text=_("Periodic task used to configure harvest scheduling"),
        null=True,
        blank=True,
        editable=False,
    )
    availability_check_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        related_name="checked_harvester",
        help_text=_("Periodic task used to check availability of the remote"),
        null=True,
        blank=True,
        editable=False,
    )

    def __str__(self):
        return f"{self.name}({self.id})"

    def clean(self):
        """Perform model validation by inspecting fields that depend on each other.

        We validate the harvester type specific configuration by determining if it meets
        the configured jsonschema (if any).

        """

        try:
            utils.validate_worker_configuration(
                self.harvester_type, self.harvester_type_specific_configuration)
        except jsonschema.exceptions.ValidationError as exc:
            raise ValidationError(str(exc))

    def setup_periodic_tasks(self) -> None:
        """Setup the related periodic tasks for the instance.

        Periodic tasks are:

        - perform harvesting
        - check availability of the remote server

        This function is automatically called by the
        `signals.create_or_update_periodic_tasks` signal handler whenever a new
        instance is saved (handler is listening to the `post_save` signal). It creates
        the related `PeriodicTask` objects in order to allow the harvester to be
        scheduled by celery beat.

        """

        update_interval, update_created = IntervalSchedule.objects.get_or_create(
            every=self.update_frequency,
            period="minutes"
        )
        self.periodic_task = PeriodicTask.objects.create(
            name=_(self.name),
            task="geonode.harvesting.tasks.harvesting_dispatcher",
            interval=update_interval,
            args=json.dumps([self.id]),
            start_time=timezone.now()
        )
        check_interval, check_created = IntervalSchedule.objects.get_or_create(
            every=self.check_availability_frequency,
            period="minutes"
        )
        self.availability_check_task = PeriodicTask.objects.create(
            name=_("Check availability of %(name)s" % {"name": self.name}),
            task="geonode.harvesting.tasks.check_harvester_available",
            interval=check_interval,
            args=json.dumps([self.id]),
            start_time=timezone.now()
        )
        self.save()

    def get_harvester_worker(self) -> BaseHarvesterWorker:
        worker_class = import_string(self.harvester_type)
        return worker_class.from_django_record(self)


class HarvestingSession(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(null=True, blank=True)
    total_records_found = models.IntegerField(default=0)
    records_harvested = models.IntegerField(default=0)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="harvesting_sessions"
    )


class HarvestableResource(models.Model):
    STATUS_READY = "ready"
    STATUS_UPDATING_HARVESTABLE_RESOURCE = "updating-harvestable-resource"
    STATUS_PERFORMING_HARVESTING = "harvesting-resource"
    STATUS_CHOICES = [
        (STATUS_READY, _("ready")),
        (STATUS_UPDATING_HARVESTABLE_RESOURCE, _("updating-harvestable-resource")),
        (STATUS_PERFORMING_HARVESTING, _("harvesting-resource")),
    ]

    unique_identifier = models.CharField(
        max_length=255,
        help_text=_(
            "Identifier that allows referencing the resource on its remote service in "
            "a unique fashion. This is usually automatically filled by the harvester "
            "worker. The harvester worker needs to know how to either read "
            "or generate this from each remote resource in order to be able to compare "
            "the availability of resources between consecutive harvesting sessions."
        ),
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_READY)
    title = models.CharField(max_length=255)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="harvestable_resources"
    )
    geonode_resource = models.ForeignKey(
        "base.ResourceBase", null=True, on_delete=models.SET_NULL)
    should_be_harvested = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    available = models.BooleanField(default=False)
    remote_resource_type = models.CharField(
        max_length=255,
        help_text=_(
            "Type of the resource in the remote service. Each harvester worker knows "
            "how to fill this field, in accordance with the resources for which "
            "harvesting is supported"
        ),
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("harvester", "unique_identifier"),
                name="unique_id_for_harvester"
            ),
        ]