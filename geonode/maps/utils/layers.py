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
import logging

from django.conf import settings

from geonode.maps.models import Map, MapLayer

logger = logging.getLogger(__name__)


def fix_baselayers(map_id):
    """
    Fix base layers for a given map.
    """

    try:
        id = int(map_id)
    except ValueError:
        logger.error("map_id must be an integer")
        return

    if not Map.objects.filter(pk=id).exists():
        logger.error(f"There is not a map with id {id}")
        return

    map = Map.objects.get(pk=id)
    # first we delete all of the base layers
    map.maplayers.filter(local=False).delete()

    # now we re-add them
    source = 0
    for base_dataset in settings.MAP_BASELAYERS:
        if "group" in base_dataset:
            # let's create the map layer
            name = ""
            if "name" in base_dataset:
                name = base_dataset["name"]
            else:
                if "args" in base_dataset:
                    name = base_dataset["args"][0]
            map_dataset = MapLayer(
                map=map,
                name=name,
            )
            map_dataset.save()
        source += 1
