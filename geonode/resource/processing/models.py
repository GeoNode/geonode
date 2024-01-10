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

from abc import ABCMeta, abstractmethod

from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager

from django.db import models
from django.utils.translation import gettext_noop as _


class AbstractProcessingTaskMeta(ABCMeta, type(PolymorphicModel)):
    @abstractmethod
    def execute(self, resource):
        pass


class AbstractProcessingTaskManager(PolymorphicManager):
    def get_real_instances(self):
        return super().get_queryset().get_real_instances()


class AbstractProcessingTask(PolymorphicModel):
    objects = AbstractProcessingTaskManager()

    name = models.CharField(max_length=255, unique=True)

    is_enabled = models.BooleanField(
        default=True, help_text=_("Disabling this Task will make the Processing Workflow to skip it.")
    )

    def __str__(self):
        get_icon = lambda arg: "[✓]" if arg else "[✗]"
        _enabled_icon = get_icon(self.is_enabled)
        return f"{_enabled_icon} {self.name} | <{type(self).__name__}>"


class ProcessingWorkflow(models.Model):
    name = models.CharField(max_length=255, unique=True)

    processing_tasks = models.ManyToManyField(AbstractProcessingTask, blank=True, through="ProcessingWorkflowTasks")

    is_enabled = models.BooleanField(
        default=True, help_text=_("Disabling this Task will make the Processing Workflow to skip it.")
    )

    def get_tasks(self):
        return list(self.processing_tasks.order_by("link_to_workflow__order"))

    def __str__(self):
        get_icon = lambda arg: "[✓]" if arg else "[✗]"
        _enabled_icon = get_icon(self.is_enabled)
        return f"{_enabled_icon} {self.name}"


class ProcessingWorkflowTasks(models.Model):
    workflow = models.ForeignKey(ProcessingWorkflow, on_delete=models.DO_NOTHING)
    task = models.ForeignKey(AbstractProcessingTask, related_name="link_to_workflow", on_delete=models.DO_NOTHING)
    order = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.order} --- Workflow: {self.workflow} -- Task: {self.task}"

    class Meta:
        verbose_name_plural = _("Processing Workflow Tasks")
        ordering = ("order",)


# ##################################################################################### #
# Samples
# ##################################################################################### #
class SampleProcessingTask(AbstractProcessingTask, metaclass=AbstractProcessingTaskMeta):
    def execute(self, resource):
        print(f"Executing {self.name} against {resource}")
