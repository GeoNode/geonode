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

"""Harvesters for ArcGIS based remote servers."""

import logging
import typing
from urllib.error import HTTPError

import arcrest
from geonode.layers.models import Dataset

from . import base

logger = logging.getLogger(__name__)


# here are some test servers for development:
# https://pro-ags2.dfs.un.org/arcgis/rest/services/UNMISS/UNMISS_Road_Rehabilitation/MapServer
# http://sit.cittametropolitana.na.it/arcgis/rest/services/CTR2011/MapServer/
# https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer
# https://carto.nationalmap.gov/arcgis/rest/services/transportation/MapServer


class ArcgisHarvesterWorker(base.BaseHarvesterWorker):
    _arc_mapservice: typing.Optional[arcrest.MapService]
    _cached_resources: typing.List[base.BriefRemoteResource]

    def __init__(self, remote_url: str, harvester_id: int) -> None:
        super().__init__(remote_url, harvester_id)
        self._arc_mapservice = None
        self._cached_resources = []

    @property
    def arc_mapservice(self):
        if self._arc_mapservice is None:
            self._arc_mapservice = arcrest.MapService(self.remote_url)
        return self._arc_mapservice

    @property
    def allows_copying_resources(self) -> bool:
        return False

    @classmethod
    def from_django_record(cls, harvester: "Harvester"):
        return cls(
            remote_url=harvester.remote_url,
            harvester_id=harvester.pk
        )

    def get_num_available_resources(self) -> int:
        if len(self._cached_resources) == 0:
            self.list_resources()
        return len(self._cached_resources)

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[base.BriefRemoteResource]:
        result = []
        try:
            for arc_layer in self.arc_mapservice.layers:
                result.append(_parse__brief_layer(arc_layer))
                result.extend(_list_sub_layers(arc_layer))
        except HTTPError:
            logger.exception(msg="Could not list resources")
        self._cached_resources = result
        return result

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        try:
            self.arc_mapservice.description
        except HTTPError:
            logger.exception("Could not contact remote service")
            result = False
        else:
            result = True
        return result

    def get_geonode_resource_type(self, remote_resource_type: str) -> typing.Type:
        return Dataset

    def get_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
    ) -> typing.Optional[base.HarvestedResourceInfo]:
        raise NotImplementedError


def list_layers(arc_mapservice: arcrest.MapService) -> typing.List[base.BriefRemoteResource]:
    result = []
    for arc_layer in arc_mapservice.layers:
        if arc_layer.type != "Group Layer":
            result.append(_parse__brief_layer(arc_layer))
        result.extend(_list_sub_layers(arc_layer))


def _list_sub_layers(arc_layer: arcrest.MapLayer) -> typing.List[base.BriefRemoteResource]:
    result = []
    for sub_layer in arc_layer.subLayers:
        if arc_layer.type != "Group Layer":
            result.append(_parse__brief_layer(sub_layer))
        result.extend(_list_sub_layers(sub_layer))
    return result


def _parse__brief_layer(arc_layer: arcrest.MapLayer) -> base.BriefRemoteResource
    return base.BriefRemoteResource(
        unique_identifier=arc_layer.id,
        title=arc_layer.name,
        resource_type=arc_layer.type,
    )
