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

import datetime as dt
import logging
import typing

import jsonschema
import jsonschema.exceptions
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

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

    name = models.CharField(max_length=255, help_text=_("Harvester name"))
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
    harvesting_session_update_frequency = models.PositiveIntegerField(
        help_text=_(
            "How often (in minutes) should new harvesting sessions be automatically scheduled?"),
        default=60
    )
    refresh_harvestable_resources_update_frequency = models.PositiveIntegerField(
        help_text=_(
            "How often (in minutes) should new refresh sessions be automatically scheduled?"),
        default=30
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
        default=10
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

    @property
    def latest_refresh_session(self):
        try:
            result = self.sessions.filter(
                session_type=AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES
            ).latest("started")
        except AsynchronousHarvestingSession.DoesNotExist:
            result = None
        return result

    @property
    def latest_harvesting_session(self):
        try:
            result = self.sessions.filter(
                session_type=AsynchronousHarvestingSession.TYPE_HARVESTING
            ).latest("started")
        except AsynchronousHarvestingSession.DoesNotExist:
            result = None
        return result

    def get_next_check_availability_dispatch_time(self) -> dt.datetime:
        now = timezone.now()
        latest_check = self.last_checked_availability
        try:
            next_schedule = latest_check + dt.timedelta(minutes=self.check_availability_frequency)
        except TypeError:
            result = now
        else:
            result = now if next_schedule < now else next_schedule
        return result

    def get_next_refresh_session_dispatch_time(self) -> typing.Optional[dt.datetime]:
        return self._get_next_dispatch_time(
            AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES)

    def get_next_harvesting_session_dispatch_time(self) -> typing.Optional[dt.datetime]:
        return self._get_next_dispatch_time(
            AsynchronousHarvestingSession.TYPE_HARVESTING)

    def _get_next_dispatch_time(self, session_type: str) -> typing.Optional[dt.datetime]:
        related_session_object_name, frequency_attribute = {
            AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES: (
                "latest_refresh_session",
                "refresh_harvestable_resources_update_frequency"
            ),
            AsynchronousHarvestingSession.TYPE_HARVESTING: (
                "latest_harvesting_session",
                "harvesting_session_update_frequency"
            ),
        }[session_type]
        latest_session: typing.Optional[AsynchronousHarvestingSession] = getattr(
            self, related_session_object_name)
        frequency = getattr(self, frequency_attribute)
        now = timezone.now()
        if not self.scheduling_enabled:
            result = None
        elif latest_session is None:
            result = now
        else:
            next_schedule = latest_session.started + dt.timedelta(minutes=frequency)
            if next_schedule < now:
                result = now
            else:
                result = next_schedule
        return result

    def is_availability_check_due(self):
        next_check_time = self.get_next_check_availability_dispatch_time()
        now = timezone.now()
        return next_check_time < now

    def is_harvestable_resources_refresh_due(self):
        next_session_time = self.get_next_refresh_session_dispatch_time()
        now = timezone.now()
        return next_session_time < now

    def is_harvesting_due(self):
        next_session_time = self.get_next_harvesting_session_dispatch_time()
        now = timezone.now()
        return next_session_time < now

    def clean(self):
        """Perform model validation by inspecting fields that depend on each other.

        We validate the harvester type specific configuration by determining if it meets
        the configured jsonschema (if any).

        """

        try:
            validate_worker_configuration(self.harvester_type, self.harvester_type_specific_configuration)
        except jsonschema.exceptions.ValidationError as exc:
            raise ValidationError(str(exc))

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
            refresh_session = AsynchronousHarvestingSession.objects.create(
                harvester=self,
                session_type=AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES
            )
            refresh_session.initiate()
        else:
            raise RuntimeError(error_msg)

    def initiate_perform_harvesting(
            self,
            harvestable_resource_ids: typing.Optional[typing.List[int]] = None
    ):
        should_continue, error_msg = self.worker_can_perform_action()
        if should_continue:
            self.status = self.STATUS_PERFORMING_HARVESTING
            self.save()
            harvesting_session = AsynchronousHarvestingSession.objects.create(
                harvester=self,
                session_type=AsynchronousHarvestingSession.TYPE_HARVESTING
            )
            harvesting_session.initiate(harvestable_resource_ids)
        else:
            raise RuntimeError(error_msg)

    def initiate_abort_update_harvestable_resources(self):
        should_continue, error_msg = self.worker_can_perform_action(
            self.STATUS_UPDATING_HARVESTABLE_RESOURCES)
        if should_continue:
            self.status = self.STATUS_ABORTING_UPDATE_HARVESTABLE_RESOURCES
            self.save()
            self.latest_refresh_session.abort()
        else:
            raise RuntimeError(error_msg)

    def initiate_abort_perform_harvesting(self):
        should_continue, error_msg = self.worker_can_perform_action(
            self.STATUS_PERFORMING_HARVESTING)
        if should_continue:
            self.status = self.STATUS_ABORTING_PERFORMING_HARVESTING
            self.save()
            self.latest_harvesting_session.abort()
        else:
            raise RuntimeError(error_msg)

    def get_harvester_worker(self) -> "BaseHarvesterWorker":  # noqa
        worker_class = import_string(self.harvester_type)
        return worker_class.from_django_record(self)

    def worker_can_perform_action(
            self,
            target_status: typing.Optional[str] = STATUS_READY,
    ) -> typing.Tuple[bool, str]:
        if self.status != target_status:
            error_message = (
                f"Harvester {self!r} cannot currently perform the desired action. Please wait until its status "
                f"is reported as {target_status!r} before retrying."
            )
            result = False
        else:
            result = True
            error_message = ""
        return result, error_message


class AsynchronousHarvestingSession(models.Model):
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
    TYPE_HARVESTING = "harvesting"
    TYPE_DISCOVER_HARVESTABLE_RESOURCES = "discover-harvestable-resources"
    TYPE_CHOICES = [
        (TYPE_HARVESTING, _("harvesting")),
        (TYPE_DISCOVER_HARVESTABLE_RESOURCES, _("discover-harvestable-resources")),
    ]
    session_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        editable=False
    )
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(null=True, blank=True)
    harvester = models.ForeignKey(
        Harvester,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        editable=False,
    )
    details = models.TextField(blank=True,)
    total_records_to_process = models.IntegerField(
        default=0,
        editable=False,
        help_text=_("Number of records being processed in this session")
    )
    records_done = models.IntegerField(
        default=0,
        help_text=_("Number of records that have already been processed")
    )

    @admin.display(description="Progress (%)")
    def get_progress_percentage(self) -> int:
        try:
            result = (self.records_done / self.total_records_to_process) * 100
        except ZeroDivisionError:
            result = 0
        return result

    def initiate(self, harvestable_resource_ids: typing.Optional[typing.List[int]] = None):
        """Initiate the asynchronous process that performs the work related to this session."""
        # NOTE: below we are calling celery tasks using the method of creating a
        # signature from the main celery app object in order to avoid having
        # to import the `tasks` module, which would create circular
        # dependency issues - this is a common celery pattern, described here:
        #
        # https://docs.celeryproject.org/en/stable/faq.html#can-i-call-a-task-by-name
        #
        # Also note that using `app.send_task()` does not seem to work in this case (which
        # is mysterious, since the celery docs say it should work)
        if self.session_type == self.TYPE_DISCOVER_HARVESTABLE_RESOURCES:
            task_signature = celery_app.app.signature(
                "geonode.harvesting.tasks.update_harvestable_resources",
                args=(self.pk,)
            )
        elif self.session_type == self.TYPE_HARVESTING:
            if harvestable_resource_ids is None:
                task_signature = celery_app.app.signature(
                    "geonode.harvesting.tasks.harvesting_dispatcher",
                    args=(self.pk,)
                )
            else:
                task_signature = celery_app.app.signature(
                    "geonode.harvesting.tasks.harvest_resources",
                    args=(harvestable_resource_ids or [], self.pk)
                )
        else:
            raise RuntimeError("Invalid selection")
        self.status = self.STATUS_PENDING
        self.save()
        task_signature.apply_async()

    def abort(self):
        """Abort a pending or on-going session."""

        # NOTE: We do not use celery's task revoke feature when aborting a session. This
        # is an explicit design choice. The main reason being that we keep track of a session's
        # state and want to know when it has finished. This is done by leveraging celery's `chord`
        # feature, whereby the async tasks are executed in parallel and there is a final
        # synchronization step when they are done that updates the session's state in the DB.
        # Maintaining this synchronization step working OK together with revoking tasks would be
        # harder to address.
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_ABORTED
            self.session_details = "Aborted"
        elif self.status == self.STATUS_ON_GOING:
            self.status = self.STATUS_ABORTING
        else:
            logger.debug("Session is not currently in an state that can be aborted, skipping...")
        self.save()


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
    abstract = models.TextField(max_length=2000, blank=True)
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


def validate_worker_configuration(
        worker_type: "BaseHarvesterWorker",  # noqa
        worker_config: typing.Dict
):
    worker_class = import_string(worker_type)
    schema = worker_class.get_extra_config_schema()
    if schema is not None:
        try:
            jsonschema.validate(worker_config, schema)
        except jsonschema.exceptions.SchemaError as exc:
            raise RuntimeError(f"Invalid schema: {exc}")
