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

from geonode import geoserver  # noqa
from geonode.maps.models import Map, MapLayer

maplayers = [
    {
        "map": "GeoNode Default Map",
        "name": "geonode:CA",
        "current_style": "",
        "ows_url": "http://localhost:8080/geoserver/wms",
    },
    {
        "map": "GeoNode Default Map",
        "name": None,
        "current_style": "",
    },
    {
        "map": "GeoNode Default Map",
        "name": None,
        "current_style": "",
    },
    {
        "map": "GeoNode Default Map",
        "name": "SATELLITE",
        "current_style": "",
    },
    {
        "map": "GeoNode Default Map",
        "name": None,
        "current_style": "",
    },
]


def create_maplayers():
    from geonode.utils import DisableDjangoSignals

    with DisableDjangoSignals():
        for ml in maplayers:
            MapLayer.objects.create(
                name=ml["name"],
                current_style=ml["current_style"],
                map=Map.objects.get(title=ml["map"]),
            )
