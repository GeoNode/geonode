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

from django.contrib import admin

from . import (
    models,
    tasks,
)


@admin.register(models.Harvester)
class HarvesterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "name",
        "scheduling_enabled",
        "remote_url",
        "remote_available",
        "update_frequency",
        "harvester_type",
    )
    readonly_fields = (
        "remote_available",
        "last_checked_availability",
    )

    list_editable = (
        "scheduling_enabled",
    )

    actions = [
        "update_harvester_availability",
        "update_harvestable_resources",
    ]

    def update_harvester_availability(self, request, queryset):
        updated_harvesters = []
        for harvester in queryset:
            worker = harvester.get_harvester_worker()
            worker.update_availability()
            updated_harvesters.append(harvester)
        self.message_user(
            request, f"Updated availability for harvesters: {updated_harvesters}")
    update_harvester_availability.short_description = (
        "Update availability of selected harvesters")

    def update_harvestable_resources(self, request, queryset):
        for harvester in queryset:
            tasks.update_harvestable_resources.apply_async(args=(harvester.pk,))
        self.message_user(request, f"Updating harvestable resources asynchronously...")
    update_harvestable_resources.short_description = "Update harvestable resources"


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
        "available",
        "unique_identifier",
        "title",
        "harvester",
        "should_be_harvested",
    )
    readonly_fields = (
        "unique_identifier",
        "title",
        "harvester",
        "last_updated",
        "available",
    )
    list_filter = (
        "harvester",
        "should_be_harvested",
        "available",
    )
    list_editable = (
        "should_be_harvested",
    )