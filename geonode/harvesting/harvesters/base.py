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

    def set_harvesting_session_id(self, id_: int) -> None:
        self._harvesting_session_id = id_

    def get_harvesting_session(self) -> "HarvestingSession":
        if self._harvesting_session_id is None:
            session = models.HarvestingSession.objects.create(
                harvester_id=self.harvester_id)
            self._harvesting_session_id = session.id
            result = session
        else:
            result = models.HarvestingSession.objects.get(
                pk=self._harvesting_session_id)
        return result

    def finish_harvesting_session(
            self, records_harvested: typing.Optional[int] = None) -> None:
        session = self.get_harvesting_session()
        session.ended = timezone.now()
        if records_harvested is not None:
            session.records_harvested = records_harvested
        session.save()

    def update_harvesting_session(
            self,
            total_records_found: typing.Optional[int] = None,
            records_harvested: typing.Optional[int] = None
    ) -> None:
        session = self.get_harvesting_session()
        if total_records_found is not None:
            session.total_records_found = total_records_found
        if records_harvested is not None:
            session.records_harvested = records_harvested
        session.save()

    def perform_metadata_harvesting(self) -> None:
        """Harvest resources from the remote service"""
        raise NotImplementedError

    def harvest_batch(self, *args, **kwargs):
        raise NotImplementedError