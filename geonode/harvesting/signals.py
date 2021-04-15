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

import logging
import typing

from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models

logger = logging.getLogger(__name__)


@receiver(
    post_save, sender=models.Harvester, dispatch_uid="create_or_update_periodic_task")
def create_or_update_periodic_task(
        sender: typing.Type[models.Harvester],
        instance: models.Harvester,
        created: bool,
        **kwargs
):
    logger.debug("Inside handle_harvester_save")
    if created:
        logger.debug(
            "A new instance has been created. Call its `setup_periodic_task()` method")
        instance.setup_periodic_task()
    elif instance.periodic_task is not None:
        logger.debug(
            "The instance already existed. Adjust its periodic task properties...")
        instance.periodic_task.name = instance.name
        instance.periodic_task.enabled = instance.scheduling_enabled
        instance.periodic_task.every = instance.update_frequency
        instance.periodic_task.period = "minutes"
        instance.periodic_task.save()