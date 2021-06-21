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

import re
import logging

from django.dispatch import receiver
from django.db.models import signals

from ..layers.models import Layer

from .models import Service
from .models import HarvestJob
from .serviceprocessors import base

logger = logging.getLogger(__name__)


@receiver(signals.post_delete, sender=Layer)
def remove_harvest_job(sender, **kwargs):
    """Remove a Layer's harvest job so that it may be re-imported later."""
    layer = kwargs["instance"]
    if layer.remote_service is not None:
        workspace = base.get_geoserver_cascading_workspace(create=False)
        resource_id = layer.alternate.split("-")[0] if re.match(r'^[0-9]+-', layer.alternate) else layer.alternate
        resource_id = layer.alternate.split(":")[1] if re.match(f'^{workspace.name}:', resource_id) else layer.alternate
        if HarvestJob.objects.filter(resource_id=resource_id):
            for job in HarvestJob.objects.filter(resource_id=resource_id, service=layer.remote_service):
                logger.debug(f"job: {job.id}")
                job.delete()
    else:
        pass  # layer was not harvested from a service, we've nothing to do


@receiver(signals.post_save, sender=Service)
def post_save_service(instance, sender, created, **kwargs):
    if created:
        instance.set_default_permissions()
