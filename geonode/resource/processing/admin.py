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

from .models import (
    ProcessingWorkflow,
    ProcessingWorkflowTasks,
    SampleProcessingTask)


class ProcessingWorkflowTasksInline(admin.TabularInline):
    model = ProcessingWorkflowTasks


@admin.register(ProcessingWorkflow)
class ProcessingWorkflowAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_enabled', 'name')  # , 'date', 'description')
    list_display_links = ('id', 'name',)
    filter_horizontal = ('processing_tasks',)
    inlines = [ProcessingWorkflowTasksInline]


@admin.register(ProcessingWorkflowTasks)
class ProcessingWorkflowTasksAdmin(admin.ModelAdmin):
    pass


@admin.register(SampleProcessingTask)
class SampleProcessingTaskAdmin(admin.ModelAdmin):
    pass
