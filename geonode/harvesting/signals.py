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

"""Signal handlers for harvesting"""

import typing

from django.db.models.signals import (
    post_delete,
    post_save,
)
from django.dispatch import receiver
from django_celery_beat.models import IntervalSchedule

from . import models


@receiver(
    post_save, sender=models.Harvester, dispatch_uid="create_or_update_periodic_task")
def create_or_update_periodic_task(
        sender: typing.Type[models.Harvester],
        instance: models.Harvester,
        created: bool,
        **kwargs
):
    if created:
        instance.setup_periodic_task()
    elif instance.periodic_task is not None:
        instance.periodic_task.enabled = instance.scheduling_enabled
        instance.periodic_task.name = instance.name
        interval, interval_created = IntervalSchedule.objects.get_or_create(
            every=instance.update_frequency,
            period="minutes"
        )
        if interval_created:
            instance.periodic_task.interval = interval
        instance.periodic_task.save()


@receiver(
    post_delete, sender=models.Harvester, dispatch_uid="delete_periodic_task")
def delete_periodic_task(
        sender: typing.Type[models.Harvester],
        instance: models.Harvester,
        **kwargs
):
    if instance.periodic_task is not None:
        instance.periodic_task.delete()
