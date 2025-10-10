#########################################################################
#
# Copyright (C) 2025 OSGeo
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
import logging
from django.utils import timezone
from geonode.harvesting.models import HarvestableResource, Harvester


logger = logging.getLogger(__name__)


def create_harvestable_resource(geonode_resource, service_url):
    """
    Will generate a Harvestable resource, if the service_url is passed
    it tries to connect it with an existing harvester
    """
    harvester = Harvester.objects.filter(remote_url=service_url).first()
    if not harvester:
        logger.warning("The WMS layer does not belong to any known remote service")
        return

    if hresource := HarvestableResource.objects.filter(unique_identifier=geonode_resource.alternate).first():
        logger.info("Harvestable resource already exists, linking geonode resource...")
        # if exists, we need to be sure that the resource from geonode is getting connected
        if not hresource.geonode_resource:
            hresource.geonode_resource = geonode_resource
            hresource.should_be_harvested = False
            hresource.save()
        elif hresource.geonode_resource.pk != geonode_resource.pk:
            logger.warning(
                "The Resource assigned to the current HarvestableResource is different from the one provided, skipping..."
            )
            return
        return

    timestamp = timezone.now()

    HarvestableResource.objects.create(
        harvester=harvester,
        unique_identifier=geonode_resource.alternate,
        geonode_resource=geonode_resource,
        title=geonode_resource.title,
        should_be_harvested=True,
        remote_resource_type=geonode_resource.resource_type,
        last_updated=timestamp,
        last_refreshed=timestamp,
        last_harvested=timestamp,
        last_harvesting_succeeded=True,
    )
