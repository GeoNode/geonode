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

import functools
import json
import logging
import typing

from django.contrib import (
    admin,
    messages,
)
from django.db import transaction
from django.urls import reverse
from django.utils.html import (
    format_html,
    mark_safe,
)

from . import (
    forms,
    models,
    tasks,
    utils,
)

logger = logging.getLogger(__name__)


@admin.register(models.Harvester)
class HarvesterAdmin(admin.ModelAdmin):
    form = forms.HarvesterForm

    list_display = (
        "id",
        "status",
        "name",
        "scheduling_enabled",
        "remote_available",
        "get_num_harvestable_resources",
        "get_num_harvestable_resources_selected",
        "get_worker_specific_configuration",
        "show_link_to_selected_harvestable_resources",
        "show_link_to_latest_harvesting_session",
    )
    list_filter = (
        "status",
    )

    readonly_fields = (
        "status",
        "remote_available",
        "last_checked_availability",
        "last_checked_harvestable_resources",
        "last_check_harvestable_resources_message",
        "num_harvestable_resources",
        "show_link_to_selected_harvestable_resources",
        "show_link_to_latest_harvesting_session",
    )

    list_editable = (
        "scheduling_enabled",
    )

    actions = [
        "update_harvester_availability",
        "update_harvestable_resources",
        "perform_harvesting"
    ]

    def save_model(self, request, obj: models.Harvester, form, change):
        # TODO: disallow changing the model if it is not ready
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            available = utils.update_harvester_availability(obj)
            if available:
                partial_task = functools.partial(
                    tasks.update_harvestable_resources.apply_async, args=(obj.pk,))
                # NOTE: below we are using transaction.on_commit in order to ensure
                # the harvester is already saved in the DB before we schedule the
                # celery task. This is needed in order to avoid the celery worker
                # picking up the task before it is saved in the DB. More info:
                #
                # https://docs.djangoproject.com/en/2.2/topics/db/transactions/#performing-actions-after-commit
                #
                if not change:
                    transaction.on_commit(partial_task)
                    message = (
                        f"Updating harvestable resources asynchronously for {obj!r}...")
                    self.message_user(request, message)
                    logger.debug(message)
                elif _worker_config_changed(form):
                    self.message_user(
                        request,
                        (
                            "Harvester worker specific configuration has been changed. "
                            "Updating list of this harvester's harvestable "
                            "resources asynchronously. When this is done the harvester "
                            "status will be set to `ready`. Refresh this page in order to monitor it."
                        ),
                        level=messages.WARNING
                    )
                    # models.HarvestableResource.objects.filter(harvester=obj).delete()
                    transaction.on_commit(partial_task)
            else:
                self.message_user(
                    request,
                    f"Harvester {obj} is{'' if available else ' not'} available",
                    messages.INFO if available else messages.WARNING
                )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields["default_owner"].initial = request.user
        return form

    @admin.action(description="Check availability of selected harvesters")
    def update_harvester_availability(self, request, queryset):
        updated_harvesters = []
        non_available_harvesters = []
        for harvester in queryset:
            available = utils.update_harvester_availability(harvester)
            updated_harvesters.append(harvester)
            if not available:
                non_available_harvesters.append(harvester)
        self.message_user(
            request, f"Updated availability for harvesters: {updated_harvesters}")
        if len(non_available_harvesters) > 0:
            self.message_user(
                request,
                (
                    f"The following harvesters are not "
                    f"available: {non_available_harvesters}"
                ),
                messages.WARNING
            )

    @admin.action(description="Update harvestable resources from selected harvesters")
    def update_harvestable_resources(self, request, queryset):
        being_updated = []
        for harvester in queryset:
            should_continue, error_msg = _should_act(harvester)
            if should_continue:
                harvester.status = harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
                harvester.save()
                tasks.update_harvestable_resources.apply_async(args=(harvester.pk,))
                being_updated.append(harvester)
            else:
                self.message_user(request, error_msg, level=messages.ERROR)
                continue
        if len(being_updated) > 0:
            self.message_user(
                request,
                (
                    f"Updating harvestable resources asynchronously for {being_updated}. "
                    f"This operation can take a while to complete. Check the harvesters' "
                    f"status for when it becomes `ready`"
                )
            )

    @admin.action(description="Perform harvesting on selected harvesters")
    def perform_harvesting(self, request, queryset):
        being_harvested = []
        for harvester in queryset:
            should_continue, error_msg = _should_act(harvester)
            if should_continue:
                harvester.status = harvester.STATUS_PERFORMING_HARVESTING
                harvester.save()
                harvesting_session = models.HarvestingSession.objects.create(harvester=harvester)
                tasks.harvesting_dispatcher.apply_async(args=(harvester.pk, harvesting_session.pk))
                being_harvested.append(harvester)
            else:
                self.message_user(request, error_msg, level=messages.ERROR)
                continue
        if len(being_harvested) > 0:
            self.message_user(
                request, f"Performing harvesting asynchronously for {being_harvested}")

    @admin.display(description="Number of selected resources to harvest")
    def get_num_harvestable_resources_selected(self, harvester: models.Harvester):
        return harvester.harvestable_resources.filter(should_be_harvested=True).count()

    @admin.display(description="Number of existing harvestable resources")
    def get_num_harvestable_resources(self, harvester: models.Harvester):
        return harvester.num_harvestable_resources

    @admin.display(description="current worker-specific configuration")
    def get_worker_specific_configuration(self, harvester: models.Harvester):
        worker = harvester.get_harvester_worker()
        worker_config = worker.get_current_config()
        result = "<ul>"
        for key, value in worker_config.items():
            result += format_html("<li>{}: {}</li>", key, value)
        result += "</ul>"
        return mark_safe(result)

    @admin.display(description="Go to selected harvestable resources")
    def show_link_to_selected_harvestable_resources(self, harvester: models.Harvester):
        num_selected = models.HarvestableResource.objects.filter(
            harvester=harvester, should_be_harvested=True).count()
        if num_selected > 0:
            changelist_uri = reverse("admin:harvesting_harvestableresource_changelist")
            result = mark_safe(
                format_html(
                    f'<a class="button grp-button" href="{changelist_uri}?harvester__id__exact={harvester.id}&should_be_harvested__exact=1">Go</a>'
                )
            )
        else:
            result = None
        return result

    @admin.display(description="Go to latest harvesting session")
    def show_link_to_latest_harvesting_session(self, harvester: models.Harvester):
        latest = models.HarvestingSession.objects.filter(harvester=harvester).latest("started")
        changelist_uri = reverse("admin:harvesting_harvestingsession_change", args=(latest.id,))
        return mark_safe(
            format_html(
                f'<a class="button grp-button" href="{changelist_uri}">Go</a>'
            )
        )


@admin.register(models.HarvestingSession)
class HarvestingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "started",
        "updated",
        "ended",
        "records_to_harvest",
        "records_harvested",
        "calculate_harvesting_progress",
        "harvester",
    )
    readonly_fields = (
        "id",
        "status",
        "started",
        "updated",
        "ended",
        "records_to_harvest",
        "records_harvested",
        "calculate_harvesting_progress",
        "harvester",
        "session_details",
    )

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @admin.display(description="progress(%)")
    def calculate_harvesting_progress(self, harvesting_session: models.HarvestingSession):
        if harvesting_session.records_to_harvest == 0:
            result = 0
        else:
            result = int((harvesting_session.records_harvested / harvesting_session.records_to_harvest) * 100)
        return result


@admin.register(models.HarvestableResource)
class HarvestableResourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "last_refreshed",
        "last_harvesting_succeeded",
        "last_harvested",
        "unique_identifier",
        "title",
        "show_link_to_harvester",
        "should_be_harvested",
        "remote_resource_type",
    )
    readonly_fields = (
        "unique_identifier",
        "title",
        "harvester",
        "last_updated",
        "last_refreshed",
        "last_harvested",
        "last_harvesting_message",
        "last_harvesting_succeeded",
        "remote_resource_type",
    )
    list_filter = (
        "harvester",
        "should_be_harvested",
        "last_updated",
        "remote_resource_type",
        "last_harvesting_succeeded",
    )
    search_fields = (
        "title",
    )
    list_editable = (
        "should_be_harvested",
    )

    actions = [
        "toggle_should_be_harvested",
        "harvest_selected_resources",
    ]

    def delete_queryset(self, request, queryset):
        """
        Re-implemented to assure individual instance's `delete()` method is called.

        `HarvestableResource.delete()` has some custom logic to check whether the
        related GeoNode resource should also be deleted. Therefore we don't want Django
        to potentially optimize this into performing the deletion on the DB, as that
        would not run our custom logic.

        Further info:

        https://docs.djangoproject.com/en/3.2/topics/db/queries/#deleting-objects

        """

        for harvestable_resource in queryset:
            harvestable_resource.delete()
        self.message_user(request, "Harvestable resources have been deleted")

    @admin.action(description="Toggle selected resources' `should_be_harvested` property")
    def toggle_should_be_harvested(self, request, queryset):
        for harvestable_resource in queryset:
            harvestable_resource: models.HarvestableResource
            harvestable_resource.should_be_harvested = (
                not harvestable_resource.should_be_harvested)
            harvestable_resource.save()

        self.message_user(
            request, "Toggled harvestable resources' `should_be_harvested` attribute")

    @admin.action(description="Harvest selected resources")
    def harvest_selected_resources(self, request, queryset):
        selected_harvestable_resources = {}
        for harvestable_resource in queryset:
            harvester_resources = selected_harvestable_resources.setdefault(harvestable_resource.harvester, [])
            harvester_resources.append(harvestable_resource.id)
        for harvester, harvestable_resource_ids in selected_harvestable_resources.items():
            should_continue, error_msg = _should_act(harvester)
            if should_continue:
                harvester.status = models.Harvester.STATUS_PERFORMING_HARVESTING
                harvester.save()
                harvesting_session = models.HarvestingSession.objects.create(harvester=harvester)
                tasks.harvest_resources.apply_async(args=(harvestable_resource_ids, harvesting_session.pk))
                self.message_user(
                    request,
                    f"Harvesting {len(harvestable_resource_ids)} resources from {harvester.name!r} harvester..."
                )
            else:
                self.message_user(
                    request,
                    error_msg,
                    level=messages.ERROR
                )

    @admin.display(description="harvester")
    def show_link_to_harvester(self, harvestable_resource: models.HarvestableResource):
        harvester = harvestable_resource.harvester
        uri = reverse("admin:harvesting_harvester_change", args=(harvester.pk,))
        return mark_safe(
            format_html(
                f'<a grp-button" href="{uri}">{harvester.name}</a>'
            )
        )


def _should_act(harvester: models.Harvester) -> typing.Tuple[bool, str]:
    if harvester.status != harvester.STATUS_READY:
        error_message = (
            f"Harvester {harvester!r} is currently busy. Please wait until its status "
            f"is {harvester.STATUS_READY!r} before retrying"
        )
        result = False
    else:
        available = utils.update_harvester_availability(harvester)
        if not available:
            error_message = (
                f"harvester {harvester!r} is not available, skipping harvesting...")
            result = False
        else:
            result = True
            error_message = ""
    return result, error_message


def _worker_config_changed(form) -> bool:
    field_name = "harvester_type_specific_configuration"
    original = json.loads(form.data[f"initial-{field_name}"])
    cleaned = form.cleaned_data.get(field_name)
    return original != cleaned
