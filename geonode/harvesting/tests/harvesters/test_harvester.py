##############################################
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

import typing
from geonode.harvesting.harvesters.base import (
    BaseHarvesterWorker,
    BriefRemoteResource,
    HarvestedResourceInfo
)
from geonode.harvesting.models import Harvester, HarvestableResource
from geonode.layers.models import Dataset
from geonode.harvesting.tests.factories import brief_remote_resource_example


class TestHarvester(BaseHarvesterWorker):
    """
    Override base harvester as test harvester
    """

    @property
    def allows_copying_resources(self) -> bool:
        return True

    @classmethod
    def from_django_record(cls, record: Harvester):
        return cls(
            record.remote_url,
            record.id)

    def get_num_available_resources(self) -> int:
        return 1

    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[BriefRemoteResource]:
        return [brief_remote_resource_example]

    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        return True

    def get_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
            harvesting_session_id: int
    ) -> typing.Optional[HarvestedResourceInfo]:
        return None

    def get_geonode_resource_type(self, remote_resource_type: str):
        """Return resource type class from resource type string."""
        return Dataset
