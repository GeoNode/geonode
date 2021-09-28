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
from django.contrib import admin, messages
from django.forms.models import ModelForm

from geonode.management_commands_http.forms import ManagementCommandJobAdminForm
from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.utils.jobs import (
    start_task,
    stop_task,
    get_celery_task_meta,
)


@admin.register(ManagementCommandJob)
class ManagementCommandJobAdmin(admin.ModelAdmin):
    actions = ["start", "stop"]
    list_per_page = 20
    list_display = (
        "id",
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
    search_fields = ("command", "app_name", "user", "celery_result_id", "output_message")

    def start(self, request, queryset):
        for job in queryset:
            try:
                start_task(job)
            except ValueError as exc:
                messages.error(request, str(exc))

    def stop(self, request, queryset):
        for job in queryset:
            stop_task(job)

    def celery_state(self, instance):
        return get_celery_task_meta(instance).get("status")

    def celery_traceback(self, instance):
        return get_celery_task_meta(instance).get("traceback")

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.status == ManagementCommandJob.CREATED

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        autostart = form.cleaned_data.get("autostart", False)
        if autostart and not change:
            start_task(obj)

    def add_view(self, request, form_url='', extra_context=None):
        self.form = ManagementCommandJobAdminForm
        self.fields = ("command", "args", "kwargs", "autostart",)
        self.readonly_fields = []
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.form = ModelForm
        self.fields = (
            "celery_result_id",
            "user",
            "command",
            "app_name",
            "args",
            "kwargs",
            "created_at",
            "start_time",
            "end_time",
            "modified_at",
            "status",
            "output_message",
            "celery_state",
            "celery_traceback",
        )
        self.readonly_fields = self.fields
        return super().change_view(request, object_id, form_url, extra_context)
