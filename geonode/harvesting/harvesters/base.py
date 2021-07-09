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
import typing
import dataclasses

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


@dataclasses.dataclass()
class HarvestedResourceInfo:
    resource_descriptor: resourcedescriptor.RecordDescription
    additional_information: typing.Optional[typing.Any]


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
    def from_django_record(cls, harvester: "Harvester"):  # noqa
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
            harvestable_resource: "HarvestableResource",  # noqa
            harvesting_session_id: int
    ) -> typing.Optional[HarvestedResourceInfo]:
        """Harvest a single resource from the remote service.

        The return value is an instance of `HarvestedResourceInfo`. It stores
        an instance of `RecordDescription` and additionally whatever type is
        required by child classes to be able to customize resource creation/update on
        the local GeoNode. Note that the default implementation of `update_geonode_resource()`
        only needs the `RecordDescription`. The possibility to return additional information
        exists solely for extensibility purposes and can be left as None in the simple cases.

        """

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
            harvested_info: HarvestedResourceInfo,
            harvestable_resource: "HarvestableResource",  # noqa
            harvesting_session_id: int,
    ):
        """Create or update a local GeoNode resource with the input harvested information."""
        harvester = models.Harvester.objects.get(pk=self.harvester_id)
        defaults = self.get_geonode_resource_defaults(
            harvested_info.resource_descriptor, harvestable_resource)
        geonode_resource = harvestable_resource.geonode_resource
        if geonode_resource is None:
            geonode_resource = resource_manager.create(
                str(harvested_info.resource_descriptor.uuid),
                self.get_geonode_resource_type(
                    harvestable_resource.remote_resource_type),
                defaults
            )
        else:
            if not geonode_resource.uuid == str(harvested_info.resource_descriptor.uuid):
                raise RuntimeError(
                    f"Resource {geonode_resource!r} already exists locally but its "
                    f"UUID ({geonode_resource.uuid}) does not match the one found on "
                    f"the remote resource {harvested_info.resource_descriptor.uuid!r}")
            geonode_resource = resource_manager.update(
                str(harvested_info.resource_descriptor.uuid), vals=defaults)

        keywords = list(
            harvested_info.resource_descriptor.identification.other_keywords
        ) + geonode_resource.keyword_list()
        keywords.append(
            harvester.name.lower().replace(
                'harvester ', '').replace(
                'harvester_', '').replace(
                'harvester', '').strip()
        )
        regions = harvested_info.resource_descriptor.identification.place_keywords
        resource_manager.update(
            str(harvested_info.resource_descriptor.uuid), regions=regions, keywords=list(set(keywords)))

        resource_manager.set_permissions(
            str(harvested_info.resource_descriptor.uuid),
            instance=geonode_resource,
            permissions=harvester.default_access_permissions)
        harvestable_resource.geonode_resource = geonode_resource
        harvestable_resource.save()
        self.finalize_resource_update(
            geonode_resource,
            harvested_info,
            harvestable_resource,
            harvesting_session_id
        )

    def finalize_resource_update(
            self,
            geonode_resource: ResourceBase,
            harvested_info: HarvestedResourceInfo,
            harvestable_resource: "HarvestableResource",  # noqa
            harvesting_session_id: int
    ) -> ResourceBase:
        return geonode_resource

    def get_geonode_resource_defaults(
            self,
            resource_descriptor: resourcedescriptor.RecordDescription,
            harvestable_resource: "HarvestableResource",  # noqa
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
