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

"""Configuration for the harvesting app

This module provides sensible default values for the harvesting app.

"""

from django.conf import settings

_default_harvesters = [
    "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester",
    # "geonode.harvesting.harvesters.geonode.GeonodeCswHarvester",
    "geonode.harvesting.harvesters.wms.OgcWmsHarvester",
]

try:
    _configured_harvester_classes = getattr(settings, "HARVESTER_CLASSES")
    HARVESTER_CLASSES = (
        _default_harvesters +
        [i for i in _configured_harvester_classes if i not in _default_harvesters]
    )
except AttributeError:
    HARVESTER_CLASSES = _default_harvesters
