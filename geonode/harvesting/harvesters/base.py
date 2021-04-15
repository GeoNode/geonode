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
import typing

from django.utils import timezone

from .. import models

logger = logging.getLogger(__name__)


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

    @property
    def harvesting_session(self):
        if self._harvesting_session_id is None:
            session = self._start_harvesting_session()
            self._harvesting_session_id = session.id
            result = session
        else:
            result = models.HarvestingSession.objects.get(
                pk=self._harvesting_session_id)
        return result

    def _start_harvesting_session(self) -> "HarvestingSession":
        return models.HarvestingSession.objects.create(harvester_id=self.harvester_id)

    def finish_harvesting_session(self, records_harvested: typing.Optional[int] = None):
        self.harvesting_session.ended = timezone.now()
        self.update_harvesting_session(records_harvested)

    def update_harvesting_session(self, records_harvested: typing.Optional[int] = None):
        if records_harvested is not None:
            self.harvesting_session.records_harvested = records_harvested
        self.harvesting_session.save()

    def perform_metadata_harvesting(self):
        """Harvest resources from the remote service"""
        raise NotImplementedError