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

from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.utils.jobs import (
    start_task,
    stop_task,
    get_celery_task_meta,
)


@admin.register(ManagementCommandJob)
class ManagementCommandJobAdmin(admin.ModelAdmin):
    """
    Allow us to see the Jobs on admin, and (re-)execute a job if needed.
    """

    list_display = (
        "command",
        "app_name",
        "user",
        "args",
        "kwargs",
        "created_at",
        "start_time",
        "end_time",
        "status",
        "celery_result_id",
    )
    list_filter = ("command", "app_name", "user")
    list_per_page = 20

    search_fields = ("command", "app_name", "user", "celery_result_id", "output_message")
    readonly_fields = (
        "celery_result_id",
        "command",
        "app_name",
        "user",
        "created_at",
        "start_time",
        "end_time",
        "modified_at",
        "status",
        "args",
        "kwargs",
        "output_message",
        "celery_state",
        "celery_traceback",
    )
    actions = ["execute", "stop"]

    def execute(self, request, queryset):
        for job in queryset:
            start_task(job)

    def stop(self, request, queryset):
        for job in queryset:
            stop_task(job)

    def celery_state(self, instance):
        return get_celery_task_meta(instance).get("status")

    def celery_traceback(self, instance):
        return get_celery_task_meta(instance).get("traceback")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
