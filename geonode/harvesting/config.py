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

import typing

from django.conf import settings


_DEFAULT_HARVESTERS: typing.Final = [
    "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker",
    "geonode.harvesting.harvesters.wms.OgcWmsHarvester",
    "geonode.harvesting.harvesters.arcgis.ArcgisHarvesterWorker",
]


def _get_harvester_class_paths(custom_class_paths: typing.List[str]) -> typing.List[str]:
    result = _DEFAULT_HARVESTERS[:]
    for i in custom_class_paths:
        if i not in result:
            result.append(i)
    return result


def get_setting(setting_key: str) -> typing.Any:
    result = {
        "HARVESTER_CLASSES": _get_harvester_class_paths(getattr(settings, "HARVESTER_CLASSES", [])),
        "HARVESTED_RESOURCE_FILE_MAX_MEMORY_SIZE": getattr(
            settings, "HARVESTED_RESOURCE_MAX_MEMORY_SIZE", settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        ),
        "HARVESTER_SCHEDULER_FREQUENCY_MINUTES": getattr(settings, "HARVESTER_SCHEDULER_FREQUENCY_MINUTES", 0.5),
    }.get(setting_key, getattr(settings, setting_key, None))
    return result
