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

import typing

from django.db.models import F
from django.utils import timezone

from .. import models


class BaseHarvester:
    remote_url: str
    harvester_id: int
    _harvesting_session_id: typing.Optional[int]

    def __init__(self, remote_url: str, harvester_id: int):
        self.remote_url = remote_url
        self.harvester_id = harvester_id
        self._harvesting_session_id = None

    @classmethod
    def from_django_record(cls, record: "Harvester"):
        return cls(
            record.remote_url,
            record.id,
        )

    def get_extra_config_schema(self) -> typing.Optional[typing.Dict]:
        """
        Return a jsonschema schema that is used to validate models.Harvester objects.
        """

        return None

    def create_harvesting_session(self) -> int:
        session = models.HarvestingSession.objects.create(
            harvester_id=self.harvester_id)
        self._harvesting_session_id = session.id
        return self._harvesting_session_id

    def set_harvesting_session_id(self, id_: int) -> None:
        self._harvesting_session_id = id_

    def finish_harvesting_session(
            self, additional_harvested_records: typing.Optional[int] = None) -> None:

        update_kwargs = {
            "ended": timezone.now()
        }
        if additional_harvested_records is not None:
            update_kwargs["records_harvested"] = (
                    F("records_harvested") + additional_harvested_records)
        models.HarvestingSession.objects.filter(
            id=self._harvesting_session_id).update(**update_kwargs)

    def update_harvesting_session(
            self,
            total_records_found: typing.Optional[int] = None,
            additional_harvested_records: typing.Optional[int] = None
    ) -> None:

        update_kwargs = {}
        if total_records_found is not None:
            update_kwargs["total_records_found"] = total_records_found
        if additional_harvested_records is not None:
            update_kwargs["records_harvested"] = (
                    F("records_harvested") + additional_harvested_records)
        models.HarvestingSession.objects.filter(
            id=self._harvesting_session_id).update(**update_kwargs)

    def perform_metadata_harvesting(self) -> None:
        """Harvest resources from the remote service"""
        raise NotImplementedError