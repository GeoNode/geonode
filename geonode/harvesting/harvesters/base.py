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

import abc
import dataclasses
import typing

from django.db.models import F
from django.utils import timezone

from .. import (
    models,
    resourcedescriptor,
)


@dataclasses.dataclass()
class BriefRemoteResource:
    unique_identifier: str
    title: str
    resource_type: str
    should_be_harvested: bool = False


class BaseHarvesterWorker(abc.ABC):
    remote_url: str
    harvester_id: int

    def __init__(self, remote_url: str, harvester_id: int):
        self.remote_url = remote_url
        self.harvester_id = harvester_id

    @property
    @abc.abstractmethod
    def allows_copying_resources(self) -> bool:
        """Whether copying remote resources is implemented by this worker"""

    @classmethod
    @abc.abstractmethod
    def from_django_record(cls, harvester: "Harvester"):
        """Return a new instance of the worker from the django harvester"""

    @abc.abstractmethod
    def get_num_available_resources(self) -> int:
        """Return the number of available resources on the remote service"""

    @abc.abstractmethod
    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[BriefRemoteResource]:
        """Return a list of resources from the remote service"""

    @abc.abstractmethod
    def check_availability(self, timeout_seconds: typing.Optional[int] = 5) -> bool:
        """Check whether the remote service is online"""

    @abc.abstractmethod
    def get_resource(
            self,
            resource_unique_identifier: str,
            resource_type: str,
            harvesting_session_id: typing.Optional[int] = None
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        """Harvest a single resource from the remote service"""

    @abc.abstractmethod
    def update_geonode_resource(
            self,
            resource_descriptor: resourcedescriptor.RecordDescription,
            harvesting_session_id: typing.Optional[int] = None
    ):
        """Update GeoNode with the input resource descriptor"""

    @classmethod
    def get_extra_config_schema(cls) -> typing.Optional[typing.Dict]:
        """Return a jsonschema schema to be used to validate models.Harvester objects"""
        return None

    @classmethod
    def finish_harvesting_session(
            cls,
            session_id: int,
            additional_harvested_records: typing.Optional[int] = None
    ) -> None:
        """Finish the input harvesting session"""
        update_kwargs = {
            "ended": timezone.now()
        }
        if additional_harvested_records is not None:
            update_kwargs["records_harvested"] = (
                    F("records_harvested") + additional_harvested_records)
        models.HarvestingSession.objects.filter(id=session_id).update(**update_kwargs)

    @classmethod
    def update_harvesting_session(
            cls,
            session_id: int,
            total_records_found: typing.Optional[int] = None,
            additional_harvested_records: typing.Optional[int] = None
    ) -> None:
        """Update the input harvesting session"""
        update_kwargs = {}
        if total_records_found is not None:
            update_kwargs["total_records_found"] = total_records_found
        if additional_harvested_records is not None:
            update_kwargs["records_harvested"] = (
                    F("records_harvested") + additional_harvested_records)
        models.HarvestingSession.objects.filter(id=session_id).update(**update_kwargs)


class OldBaseHarvester:
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

    def get_num_available_resources(self) -> int:
        return 0

    def list_resources(
            self, offset: typing.Optional[int] = 0) -> typing.List[BriefRemoteResource]:
        """Return a list of resources from the remote service"""

        return []

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

    def check_availability(self) -> bool:
        """Check whether the remote url is online"""
        raise NotImplementedError

    def perform_metadata_harvesting(self) -> None:
        """Harvest resources from the remote service"""
        raise NotImplementedError