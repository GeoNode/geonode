#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django import template

from geonode.base.models import ResourceBase
from geonode.services.models import Service
from geonode.security.utils import get_visible_resources

register = template.Library()


@register.simple_tag
def get_dataset_count_by_services(service_id, user):
    try:
        service = Service.objects.get(id=service_id)
        harvested_resources_ids = []
        if service.harvester:
            _h = service.harvester
            harvested_resources_ids = list(_h.harvestable_resources.filter(
                should_be_harvested=True, geonode_resource__isnull=False).values_list("geonode_resource__id", flat=True))
        return get_visible_resources(
            queryset=ResourceBase.objects.filter(id__in=harvested_resources_ids),
            user=user
        ).count()
    except Exception:
        return 0
