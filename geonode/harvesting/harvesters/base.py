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
from geonode.base.models import ResourceBase
from geonode.resource.manager import resource_manager

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
    """Base class for harvesters.

    This provides two relevant things:

    - an interface that all custom GeoNode harvesting classes must implement
    - default implementation of some lower-level methods

    """

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
    def get_geonode_resource_type(self, remote_resource_type: str) -> ResourceBase:
        """
        Return the GeoNode type that should be created from the remote resource type
        """

    @abc.abstractmethod
    def get_resource(
            self,
            harvestable_resource: models.HarvestableResource,
            harvesting_session_id: int
    ) -> typing.Optional[resourcedescriptor.RecordDescription]:
        """Harvest a single resource from the remote service"""

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

    def update_geonode_resource(
            self,
            resource_descriptor: resourcedescriptor.RecordDescription,
            harvestable_resource: models.HarvestableResource,
            harvesting_session_id: int
    ):
        """Update GeoNode with the input resource descriptor."""
        harvester = models.Harvester.objects.get(pk=self.harvester_id)
        defaults = self.get_geonode_resource_defaults(
            resource_descriptor, harvestable_resource)
        if resource_manager.exists(str(resource_descriptor.uuid)):
            geonode_resource = resource_manager.update(
                str(resource_descriptor.uuid),
                vals=defaults,
            )
        else:
            geonode_resource = resource_manager.create(
                str(resource_descriptor.uuid),
                self.get_geonode_resource_type(
                    harvestable_resource.remote_resource_type),
                defaults
            )
        resource_manager.set_permissions(
            str(resource_descriptor.uuid),
            instance=geonode_resource,
            permissions=harvester.default_access_permissions)

    def get_geonode_resource_defaults(
            self,
            resource_descriptor: resourcedescriptor.RecordDescription,
            harvestable_resource: models.HarvestableResource,
    ) -> typing.Dict:
        """
        Extract default values to be used by resource manager when updating a resource
        """

        defaults = {
            "owner": harvestable_resource.harvester.default_owner,
            "uuid": str(resource_descriptor.uuid),
            "abstract": resource_descriptor.identification.abstract,
            "bbox_polygon": resource_descriptor.identification.spatial_extent,
            "constraints_other": resource_descriptor.identification.other_constraints,
            "created": resource_descriptor.date_stamp,
            "data_quality_statement": resource_descriptor.data_quality,
            "date": resource_descriptor.identification.date,
            "date_type": resource_descriptor.identification.date_type,
            "language": resource_descriptor.language,
            "purpose": resource_descriptor.identification.purpose,
            "supplemental_information": (
                resource_descriptor.identification.supplemental_information),
            "title": resource_descriptor.identification.title
        }
        # geonode_resource_type = self.get_resource_type_class(
        #     harvestable_resource.remote_resource_type)
        # if geonode_resource_type == Map:
        #     defaults.update({
        #         "zoom": resource_descriptor.zoom,
        #         "center_x": resource_descriptor.center_x,
        #         "center_y": resource_descriptor.center_y,
        #         "projection": resource_descriptor.projection,
        #         "last_modified": resource_descriptor.last_modified
        #     })
        # elif geonode_resource_type == Layer:
        #     defaults.update({
        #         "charset": resource_descriptor.character_set
        #     })
        return {key: value for key, value in defaults.items() if value is not None}
