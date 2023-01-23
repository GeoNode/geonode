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

from django.contrib import (
    admin,
    messages,
)
from django.contrib.humanize.templatetags import humanize
from django.urls import reverse
from django.utils.html import (
    format_html,
    mark_safe,
)
from django.utils.translation import gettext_lazy as _

from . import (
    forms,
    models,
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
        "show_link_to_selected_harvestable_resources",
        "show_link_to_latest_harvesting_session",
        "show_link_to_latest_refresh_session",
        "get_worker_specific_configuration",
        "get_time_until_next_availability_update",
        "get_time_until_next_refresh",
        "get_time_until_next_harvesting",
    )
    list_filter = ("status",)

    readonly_fields = (
        "status",
        "remote_available",
        "last_checked_availability",
        "last_checked_harvestable_resources",
        "last_check_harvestable_resources_message",
        "num_harvestable_resources",
        "show_link_to_selected_harvestable_resources",
        "show_link_to_latest_harvesting_session",
        "show_link_to_latest_refresh_session",
    )

    list_editable = ("scheduling_enabled",)

    actions = [
        "update_harvester_availability",
        "initiate_update_harvestable_resources",
        "initiate_abort_update_harvestable_resources",
        "initiate_perform_harvesting",
        "initiate_abort_perform_harvesting",
        "reset_harvester_status",
    ]

    def save_model(self, request, harvester: models.Harvester, form, change):
        super().save_model(request, harvester, form, change)
        if _worker_config_changed(form):
            self.message_user(
                request,
                (
                    "Harvester worker specific configuration has been changed. "
                    "You should update the list of this harvester's harvestable "
                    "resources now in order to ensure consistency."
                ),
                level=messages.WARNING,
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
            available = harvester.update_availability()
            updated_harvesters.append(harvester)
            if not available:
                non_available_harvesters.append(harvester)
        self.message_user(request, f"Updated availability for harvesters: {updated_harvesters}")
        if len(non_available_harvesters) > 0:
            self.message_user(
                request,
                (f"The following harvesters are not " f"available: {non_available_harvesters}"),
                messages.WARNING,
            )

    @admin.action(description="Update harvestable resources for selected harvesters")
    def initiate_update_harvestable_resources(self, request, queryset):
        being_updated = []
        for harvester in queryset:
            try:
                if harvester.update_availability():
                    harvester.initiate_update_harvestable_resources()
                    being_updated.append(harvester)
                else:
                    raise RuntimeError(f"Harvester {harvester!r} is not available")
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
        if len(being_updated) > 0:
            message = (
                f"Updating harvestable resources asynchronously for {being_updated}. "
                f"This operation can take a while to complete. Check the harvesters' "
                f"status for when it becomes `ready` or inspect its latest refresh "
                f"session and monitor the reported progress"
            )
        else:
            message = _("No ready harvesters have been selected, skipping...")
        self.message_user(request, message)

    @admin.action(description="Abort on-going update of harvestable resources for selected harvesters")
    def initiate_abort_update_harvestable_resources(self, request, queryset):
        being_aborted = []
        for harvester in queryset:
            try:
                if harvester.update_availability():
                    harvester.initiate_abort_update_harvestable_resources()
                    being_aborted.append(harvester)
                else:
                    raise RuntimeError(f"Harvester {harvester!r} is not available")
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
        if len(being_aborted) > 0:
            message = (
                f"Aborting update of harvestable resources for {being_aborted}. "
                f"This operation can take a while to complete. Check the harvesters' "
                f"status for when it becomes `ready`"
            )
        else:
            message = _("No active refresh sessions have been found for the selected harvesters. Skipping...")
        self.message_user(request, message)

    @admin.action(description="Perform harvesting on selected harvesters")
    def initiate_perform_harvesting(self, request, queryset):
        being_harvested = []
        for harvester in queryset:
            try:
                if harvester.update_availability():
                    harvester.initiate_perform_harvesting()
                    being_harvested.append(harvester)
                else:
                    raise RuntimeError(f"Harvester {harvester!r} is not available")
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
        if len(being_harvested) > 0:
            message = f"Performing harvesting asynchronously for {being_harvested}..."
        else:
            message = _("No ready harvesters have been selected, skipping...")
        self.message_user(request, message)

    @admin.action(description="Abort on-going harvesting sessions for selected harvesters")
    def initiate_abort_perform_harvesting(self, request, queryset):
        being_aborted = []
        for harvester in queryset:
            try:
                if harvester.update_availability():
                    harvester.initiate_abort_perform_harvesting()
                    being_aborted.append(harvester)
                else:
                    raise RuntimeError(f"Harvester {harvester!r} is not available")
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
        if len(being_aborted) > 0:
            message = (
                f"Aborting current harvesting sessions for {being_aborted}. "
                f"This operation can take a while to complete. Check the harvesters' "
                f"status for when it becomes `ready`"
            )
        else:
            message = _("No active harvesting sessions have been found for the selected harvesters. Skipping...")
        self.message_user(request, message)

    @admin.action(description="Reset harvester status")
    def reset_harvester_status(self, request, queryset):
        for harvester in queryset:
            if harvester.status != models.Harvester.STATUS_READY:
                harvester.status = models.Harvester.STATUS_READY
                harvester.save()
                self.message_user(request, _("Resetting status for harvester %(name)s...") % {"name": harvester.name})

    @admin.display(description="Updating availability in")
    def get_time_until_next_availability_update(self, harvester: models.Harvester):
        return humanize.naturaltime(harvester.get_next_check_availability_dispatch_time())

    @admin.display(description="Refreshing harvestable resources in")
    def get_time_until_next_refresh(self, harvester: models.Harvester):
        return humanize.naturaltime(harvester.get_next_refresh_session_dispatch_time())

    @admin.display(description="Performing harvesting in")
    def get_time_until_next_harvesting(self, harvester: models.Harvester):
        return humanize.naturaltime(harvester.get_next_harvesting_session_dispatch_time())

    @admin.display(description=_("Harvestable resources"))
    def get_num_harvestable_resources(self, harvester: models.Harvester):
        return harvester.num_harvestable_resources

    @admin.display(description="Worker-specific configuration")
    def get_worker_specific_configuration(self, harvester: models.Harvester):
        result = "<ul>"
        try:
            worker = harvester.get_harvester_worker()
            worker_config = worker.get_current_config()
            for key, value in worker_config.items():
                result += format_html("<li>{}: {}</li>", key, value)
        except Exception as e:
            logger.exception(e)
        result += "</ul>"
        return mark_safe(result)

    @admin.display(description="Selected harvestable resources")
    def show_link_to_selected_harvestable_resources(self, harvester: models.Harvester):
        num_selected = models.HarvestableResource.objects.filter(harvester=harvester, should_be_harvested=True).count()
        if num_selected > 0:
            changelist_uri = reverse("admin:harvesting_harvestableresource_changelist")
            result = mark_safe(
                format_html(
                    f'<a class="button grp-button" href="{changelist_uri}?harvester__id__exact={harvester.id}&should_be_harvested__exact=1">({num_selected}) Go</a>'
                )
            )
        else:
            result = None
        return result

    @admin.display(description="Latest harvesting session")
    def show_link_to_latest_harvesting_session(self, harvester: models.Harvester):
        session = harvester.latest_harvesting_session
        if session is not None:
            changelist_uri = reverse(
                "admin:harvesting_asynchronousharvestingsession_change", args=(harvester.latest_harvesting_session.id,)
            )
            return mark_safe(format_html(f'<a class="button grp-button" href="{changelist_uri}">Go</a>'))

    @admin.display(description="Latest refresh session")
    def show_link_to_latest_refresh_session(self, harvester: models.Harvester):
        session = harvester.latest_refresh_session
        if session is not None:
            changelist_uri = reverse(
                "admin:harvesting_asynchronousharvestingsession_change", args=(harvester.latest_refresh_session.id,)
            )
            return mark_safe(format_html(f'<a class="button grp-button" href="{changelist_uri}">Go</a>'))


@admin.register(models.AsynchronousHarvestingSession)
class AsynchronousHarvestingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_type",
        "status",
        "started",
        "updated",
        "ended",
        "harvester",
        "total_records_to_process",
        "records_done",
        "get_progress_percentage",
    )
    readonly_fields = (
        "id",
        "session_type",
        "status",
        "started",
        "updated",
        "ended",
        "harvester",
        "total_records_to_process",
        "records_done",
        "get_progress_percentage",
        "details",
    )

    def has_add_permission(self, request):
        return False


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
    search_fields = ("title",)
    list_editable = ("should_be_harvested",)

    actions = [
        "toggle_should_be_harvested",
        "initiate_harvest_selected_resources",
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
            harvestable_resource.should_be_harvested = not harvestable_resource.should_be_harvested
            harvestable_resource.save()

        self.message_user(request, "Toggled harvestable resources' `should_be_harvested` attribute")

    @admin.action(description="Harvest selected resources")
    def initiate_harvest_selected_resources(self, request, queryset):
        selected_harvestable_resources = {}
        for harvestable_resource in queryset:
            harvester_resources = selected_harvestable_resources.setdefault(harvestable_resource.harvester, [])
            harvester_resources.append(harvestable_resource.id)
        for harvester, harvestable_resource_ids in selected_harvestable_resources.items():
            try:
                if harvester.update_availability():
                    harvester.initiate_perform_harvesting(harvestable_resource_ids)
                    self.message_user(
                        request,
                        f"Harvesting {len(harvestable_resource_ids)} resources from {harvester.name!r} harvester...",
                    )
                else:
                    raise RuntimeError(f"Harvester {harvester!r} is not available")
            except RuntimeError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    @admin.display(description="harvester")
    def show_link_to_harvester(self, harvestable_resource: models.HarvestableResource):
        harvester = harvestable_resource.harvester
        uri = reverse("admin:harvesting_harvester_change", args=(harvester.pk,))
        return mark_safe(format_html(f'<a grp-button" href="{uri}">{harvester.name}</a>'))


def _worker_config_changed(form) -> bool:
    field_name = "harvester_type_specific_configuration"
    try:
        original = json.loads(form.data[f"initial-{field_name}"])
    except KeyError:
        result = True
    else:
        cleaned = form.cleaned_data.get(field_name)
        result = original != cleaned
    return result
