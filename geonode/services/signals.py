#########################################################################
#
# Copyright (C) 2017 OSGeo
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

"""signal handlers for geonode.services"""

import logging


from django.dispatch import receiver
from django.db.models import signals
from geonode.harvesting.models import Harvester
from .models import Service

logger = logging.getLogger(__name__)


@receiver(signals.post_delete, sender=Service)
def remove_harvesters(instance, **kwargs):
    """Remove a Service's harvesters and related resources."""
    try:
        if instance.harvester:
            instance.harvester.delete()
    except Harvester.DoesNotExist as e:
        logger.warn(e)


@receiver(signals.post_save, sender=Service)
def post_save_service(instance, sender, created, **kwargs):
    if created:
        instance.set_default_permissions()
