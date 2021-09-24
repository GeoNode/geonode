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
import typing

import jsonschema
import jsonschema.exceptions
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import (
    IntervalSchedule,
    PeriodicTask,
)

from geonode import celery_app

from .config import get_setting

logger = logging.getLogger(__name__)


class Harvester(models.Model):
    STATUS_READY = "ready"
    STATUS_UPDATING_HARVESTABLE_RESOURCES = "updating-harvestable-resources"
    STATUS_ABORTING_UPDATE_HARVESTABLE_RESOURCES = "aborting-update-harvestable-resources"
    STATUS_PERFORMING_HARVESTING = "harvesting-resources"
    STATUS_ABORTING_PERFORMING_HARVESTING = "aborting-harvesting-resources"
    STATUS_CHECKING_AVAILABILITY = "checking-availability"
    STATUS_CHOICES = [
        (STATUS_READY, _("ready")),
        (STATUS_UPDATING_HARVESTABLE_RESOURCES, _("updating-harvestable-resources")),
        (STATUS_ABORTING_UPDATE_HARVESTABLE_RESOURCES, _("aborting-update-harvestable-resources")),
        (STATUS_PERFORMING_HARVESTING, _("harvesting-resources")),
        (STATUS_ABORTING_PERFORMING_HARVESTING, _("aborting-harvesting-resources")),
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
        choices=(((i, i) for i in get_setting("HARVESTER_CLASSES"))),
        default=get_setting("HARVESTER_CLASSES")[0]
    )
    harvester_type_specific_configuration = models.JSONField(
        default=dict,
        blank=True,
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
    num_harvestable_resources = models.IntegerField(
        blank=True,
        default=0
    )

    class Meta:
        # Note: name must be unique because we use it to create a periodic task for the harvester
        constraints = [
            models.UniqueConstraint(fields=("name",), name="unique name")
        ]

    def __str__(self):
        return f"{self.name}({self.id})"

    def clean(self):
        """Perform model validation by inspecting fields that depend on each other.

        We validate the harvester type specific configuration by determining if it meets
        the configured jsonschema (if any).

        """

        try:
            self.validate_worker_configuration(
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
            name=_(f"Check availability of {self.name}"),
            task="geonode.harvesting.tasks.check_harvester_available",
            interval=check_interval,
            args=json.dumps([self.id]),
            start_time=timezone.now()
        )
        self.save()

    def update_availability(
            self,
            timeout_seconds: typing.Optional[int] = 5
    ):
        """Use the harvesting worker to check if the remote service is available"""
        worker = self.get_harvester_worker()
        self.last_checked_availability = timezone.now()
        available = worker.check_availability(timeout_seconds=timeout_seconds)
        self.remote_available = available
        self.save()
        return available

    def initiate_update_harvestable_resources(self):
        should_continue, error_msg = self.worker_can_perform_action()
        if should_continue:
            self.status = self.STATUS_UPDATING_HARVESTABLE_RESOURCES
            self.save()
            refresh_session = HarvestableResourceRefreshSession.objects.create(harvester=self)
            refresh_session.initiate()
        else:
            raise RuntimeError(error_msg)

    def initiate_perform_harvesting_session(self):
        should_continue, error_msg = self.worker_can_perform_action()
        if should_continue:
            self.status = self.STATUS_PERFORMING_HARVESTING
            self.save()
            harvesting_session = HarvestingSession.objects.create(harvester=self)
            harvesting_session.initiate()
        else:
            raise RuntimeError(error_msg)

    def initiate_abort_update_harvestable_resources(self):
        should_continue, error_msg = self.worker_can_perform_action(
            self.STATUS_UPDATING_HARVESTABLE_RESOURCES)
        if should_continue:
            self.status = self.STATUS_ABORTING_UPDATE_HARVESTABLE_RESOURCES
            self.save()
            latest_refresh_session = self.refresh_sessions.latest("started")
            latest_refresh_session.abort()
        else:
            raise RuntimeError(error_msg)

    def initiate_abort_perform_harvesting_session(self):
        should_continue, error_msg = self.worker_can_perform_action(
            self.STATUS_PERFORMING_HARVESTING)
        if should_continue:
            latest_harvesting_session = self.harvesting_sessions.latest("started")
            latest_harvesting_session.abort()
        else:
            raise RuntimeError(error_msg)

    def get_harvester_worker(self) -> "BaseHarvesterWorker":  # noqa
        worker_class = import_string(self.harvester_type)
        return worker_class.from_django_record(self)

    def validate_worker_configuration(self):
        worker_class = import_string(self.harvester_type)
        schema = worker_class.get_extra_config_schema()
        if schema is not None:
            try:
                jsonschema.validate(self.harvester_type_specific_configuration, schema)
            except jsonschema.exceptions.SchemaError as exc:
                raise RuntimeError(f"Invalid schema: {exc}")

    def worker_can_perform_action(
            self,
            target_status: typing.Optional[str] = STATUS_READY,
    ) -> typing.Tuple[bool, str]:
        if self.status != target_status:
            error_message = (
                f"Harvester {self!r} is currently busy. Please wait until its status "
                f"is {target_status!r} before retrying"
            )
            result = False
        else:
            result = True
            error_message = ""
        return result, error_message


class HarvestingSession(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ON_GOING = "on-going"
    STATUS_FINISHED_ALL_OK = "finished-all-ok"
    STATUS_FINISHED_ALL_FAILED = "finished-all-failed"
    STATUS_FINISHED_SOME_FAILED = "finished-some-failed"
    STATUS_ABORTING = "aborting"
    STATUS_ABORTED = "aborted"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("pending")),
        (STATUS_ON_GOING, _("on-going")),
        (STATUS_FINISHED_ALL_OK, _("finished-all-ok")),
        (STATUS_FINISHED_ALL_FAILED, _("finished-all-failed")),
        (STATUS_FINISHED_SOME_FAILED, _("finished-some-failed")),
        (STATUS_ABORTING, _("aborting")),
        (STATUS_ABORTED, _("aborted")),
    ]
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(null=True, blank=True)
    records_to_harvest = models.IntegerField(default=0, editable=False)
    records_harvested = models.IntegerField(default=0)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="harvesting_sessions"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        editable=False,
    )
    session_details = models.TextField(
        blank=True,
        help_text=_("Details about the harvesting session")
    )

    # FIXME: do not use celery revoke task
    def initiate(self):
        """Initiate a new harvesting session according with the harvester's selected harvestable resources"""
        async_result = celery_app.app.send_task(
            "geonode.harvesting.tasks.harvesting_dispatcher",
            args=(self.pk,)
        )
        self.status = self.STATUS_PENDING
        self.task_ids = [async_result.id]
        self.save()

    def abort(self):
        """Abort a pending or on-going session.

        If the session already has running async tasks, then it will
        transition to the `aborting` state, whereby the ongoing tasks
        will still finish their execution.

        """

        if self.status == self.STATUS_PENDING:
            celery_app.app.control.revoke(self.task_ids)
            self.status = self.STATUS_ABORTED
            self.save()
        elif self.status == self.STATUS_ON_GOING:
            celery_app.app.control.revoke(self.task_ids)
            self.status = self.STATUS_ABORTING
            self.save()
        else:
            logger.debug("Session is not currently in an state that can be aborted, skipping...")


class HarvestableResourceRefreshSession(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ON_GOING = "on-going"
    STATUS_FINISHED_ALL_OK = "finished-all-ok"
    STATUS_FINISHED_ALL_FAILED = "finished-all-failed"
    STATUS_FINISHED_SOME_FAILED = "finished-some-failed"
    STATUS_ABORTING = "aborting"
    STATUS_ABORTED = "aborted"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("pending")),
        (STATUS_ON_GOING, _("on-going")),
        (STATUS_FINISHED_ALL_OK, _("finished-all-ok")),
        (STATUS_FINISHED_ALL_FAILED, _("finished-all-failed")),
        (STATUS_FINISHED_SOME_FAILED, _("finished-some-failed")),
        (STATUS_ABORTING, _("aborting")),
        (STATUS_ABORTED, _("aborted")),
    ]
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(null=True, blank=True)
    remote_records = models.IntegerField(default=0, editable=False)
    records_refreshed = models.IntegerField(default=0)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="refresh_sessions"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        editable=False,
    )
    session_details = models.TextField(
        blank=True,
        help_text=_("Details about the session")
    )

    # FIXME: do not use celery revoke task
    def initiate(self):
        """Initiate the asynchronous process that performs the update of harvestable resources"""
        async_result = celery_app.app.send_task(
            "geonode.harvesting.tasks.update_harvestable_resources",
            args=(self.pk,)
        )
        self.status = self.STATUS_PENDING
        self.task_ids = [async_result.id]
        self.save()

    def abort(self):
        """Abort a pending or on-going session."""
        if self.status == self.STATUS_PENDING:
            celery_app.app.control.revoke(self.task_ids)
            self.status = self.STATUS_ABORTED
            self.session_details = "Aborted"
            self.save()
        elif self.status == self.STATUS_ON_GOING:
            celery_app.app.control.revoke(self.task_ids)
            self.status = self.STATUS_ABORTING
            self.save()
        else:
            logger.debug("Session is not currently in an state that can be aborted, skipping...")


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
    last_refreshed = models.DateTimeField()
    last_harvested = models.DateTimeField(null=True, blank=True)
    last_harvesting_message = models.TextField(blank=True)
    last_harvesting_succeeded = models.BooleanField(default=False)
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

    def delete(self, using=None, keep_parents=False):
        delete_orphan_resource = self.harvester.delete_orphan_resources_automatically
        worker = self.harvester.get_harvester_worker()
        if self.geonode_resource is not None and delete_orphan_resource:
            self.geonode_resource.delete()
        if delete_orphan_resource:
            worker.finalize_harvestable_resource_deletion(self)
        return super().delete(using, keep_parents)
