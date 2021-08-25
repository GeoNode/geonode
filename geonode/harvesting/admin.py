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
        "remote_url",
        "remote_available",
        "update_frequency",
        "harvester_type",
        "get_num_harvestable_resources",
        "get_num_harvestable_resources_selected",
    )

    readonly_fields = (
        "remote_available",
        "last_checked_availability",
        "last_checked_harvestable_resources",
        "last_check_harvestable_resources_message",
        'task_ids'
    )

    list_editable = (
        "scheduling_enabled",
    )

    actions = [
        "update_harvester_availability",
        "update_harvestable_resources",
        "perform_harvesting",
        "stop_process",
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
                            "resources asynchronously... "
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
                f"Updating harvestable resources asynchronously for {being_updated}..."
            )

    @admin.display(description="Number of selected resources to harvest")
    def get_num_harvestable_resources_selected(self, harvester: models.Harvester):
        return harvester.harvestable_resources.filter(should_be_harvested=True).count()

    @admin.display(description="Number of existing harvestable resources")
    def get_num_harvestable_resources(self, harvester: models.Harvester):
        return harvester.num_harvestable_resources

    @admin.action(description="Perform harvesting on selected harvesters")
    def perform_harvesting(self, request, queryset):
        being_harvested = []
        for harvester in queryset:
            should_continue, error_msg = _should_act(harvester)
            if should_continue:
                harvester.status = harvester.STATUS_PERFORMING_HARVESTING
                harvester.save()
                tasks.harvesting_dispatcher.apply_async(args=(harvester.pk,))
                being_harvested.append(harvester)
            else:
                self.message_user(request, error_msg, level=messages.ERROR)
                continue
        if len(being_harvested) > 0:
            self.message_user(
                request, f"Performing harvesting asynchronously for {being_harvested}")

    @admin.action(description="Stop current processing")
    def stop_process(self, request, queryset):
        for harvester in queryset:
            harvester.stop()


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


@admin.register(models.HarvestingSession)
class HarvestingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "started",
        "updated",
        "ended",
        "total_records_found",
        "records_harvested",
        "harvester",
    )


@admin.register(models.HarvestableResource)
class HarvestableResourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "last_refreshed",
        "last_harvesting_succeeded",
        "last_harvested",
        "unique_identifier",
        "title",
        "harvester",
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


def _worker_config_changed(form) -> bool:
    field_name = "harvester_type_specific_configuration"
    # original = eval(form.data[f"initial-{field_name}"], {})
    original = json.loads(form.data[f"initial-{field_name}"])
    cleaned = form.cleaned_data.get(field_name)
    return original != cleaned
