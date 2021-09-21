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
import html
import logging
import typing
import urllib.parse

import requests
from django.core.files import uploadedfile
from django.db.models import F
from django.utils import timezone
from geonode.base.models import ResourceBase
from geonode.resource.manager import resource_manager
from geonode.storage.manager import storage_manager

from .. import (
    config,
    models,
    resourcedescriptor,
)

logger = logging.getLogger(__name__)


class HarvestingException(Exception):
    pass


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
    copied_resources: typing.Optional[typing.List] = dataclasses.field(default_factory=list)


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
        """Return the number of available resources on the remote service.

        If there is a problem retrieving the number of available resource, this
        method shall raise `HarvestingException`.

        """

    @abc.abstractmethod
    def list_resources(
            self,
            offset: typing.Optional[int] = 0
    ) -> typing.List[BriefRemoteResource]:
        """Return a list of resources from the remote service.

        If there is a problem listing resource, this method shall
        raise `HarvestingException`.

        """

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
        defaults = self.get_geonode_resource_defaults(
            harvested_info, harvestable_resource)
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
        harvester = models.Harvester.objects.get(pk=self.harvester_id)
        keywords.append(
            harvester.name.lower().replace(
                'harvester ', '').replace(
                'harvester_', '').replace(
                'harvester', '').strip()
        )
        regions = harvested_info.resource_descriptor.identification.place_keywords
        harvestable_resource.geonode_resource = geonode_resource
        harvestable_resource.save()
        # Make sure you set the "harvestable_resource.geonode_resource" before calling the "resource_manager"
        resource_manager.update(
            str(harvested_info.resource_descriptor.uuid), regions=regions, keywords=list(set(keywords)))

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
        """Perform additional actions just after having created/updated a local GeoNode resource.

        This method can be used to further manipulate the relevant GeoNode Resource that is being
        created/updated in the context of a harvesting operation. It is typically called from within
        `base.BaseHarvesterWorker.update_geonode_resource` as the last step, after having already
        acted upon the GeoNode resource.
        The default implementation does nothing.

        """

        return geonode_resource

    def finalize_harvestable_resource_deletion(
            self,
            harvestable_resource: "HarvestableResource"  # noqa
    ) -> bool:
        """Perform additional actions just before deleting a harvestable resource.

        This method is typically called from within `models.HarvestableResource.delete()`, just before
        deleting the actual harvestable resource. It can be useful for child classes that customize
        resource creation in order to also customize the deletion of harvestable resources.
        The default implementation does nothing.

        """

        return True

    def should_copy_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
    ) -> bool:
        """Return True if the worker is able to copy the remote resource.

        The base implementation just returns False. Subclasses must re-implement this method
        if they support copying remote resources onto the local GeoNode.

        """

        return False

    def copy_resource(
            self,
            harvestable_resource: "HarvestableResource",  # noqa
            harvested_resource_info: HarvestedResourceInfo,
    ) -> typing.Optional[str]:
        """Copy a remote resource's data to the local GeoNode.

        The base implementation provides a generic copy using GeoNode's `storage_manager`.
        Subclasses may need to re-implement this method if they require specialized behavior.

        """

        url = harvested_resource_info.resource_descriptor.distribution.original_format_url
        result = None
        if url is not None:
            parsed_url = urllib.parse.urlparse(url)
            sanitized_base_name = _sanitize_file_name(parsed_url.path)
            harvester = models.Harvester.objects.get(pk=self.harvester_id)
            name_fragments = (
                f"{harvester.name}-{harvester.id}",
                str(harvested_resource_info.resource_descriptor.uuid),
                sanitized_base_name
            )
            target_name = "_".join(name_fragments)
            try:
                result = download_resource_file(url, target_name)
            except requests.exceptions.HTTPError:
                logger.exception(f"Could not download resource file from {url!r}")
        else:
            logger.warning(
                "harvested resource info does not provide a URL for retrieving the "
                "resource, skipping..."
            )
        return result

    def get_geonode_resource_defaults(
            self,
            harvested_info: HarvestedResourceInfo,
            harvestable_resource: "HarvestableResource",  # noqa
    ) -> typing.Dict:
        """
        Extract default values to be used by resource manager when updating a resource
        """

        defaults = {
            "owner": harvestable_resource.harvester.default_owner,
            "uuid": str(harvested_info.resource_descriptor.uuid),
            "abstract": harvested_info.resource_descriptor.identification.abstract,
            "bbox_polygon": harvested_info.resource_descriptor.identification.spatial_extent,
            "constraints_other": harvested_info.resource_descriptor.identification.other_constraints,
            "created": harvested_info.resource_descriptor.date_stamp,
            "data_quality_statement": harvested_info.resource_descriptor.data_quality,
            "date": harvested_info.resource_descriptor.identification.date,
            "date_type": harvested_info.resource_descriptor.identification.date_type,
            "language": harvested_info.resource_descriptor.language,
            "purpose": harvested_info.resource_descriptor.identification.purpose,
            "supplemental_information": (
                harvested_info.resource_descriptor.identification.supplemental_information),
            "title": harvested_info.resource_descriptor.identification.title,
            "files": harvested_info.copied_resources,
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
        # elif geonode_resource_type == Dataset:
        #     defaults.update({
        #         "charset": resource_descriptor.character_set
        #     })
        return {key: value for key, value in defaults.items() if value is not None}


def download_resource_file(url: str, target_name: str) -> str:
    """Download a resource file and store it using GeoNode's `storage_manager`.

    Downloads use the django `UploadedFile` helper classes. Depending on the size of the
    remote resource, we may download it into an in-memory buffer or store it on a
    temporary location on disk. After having downloaded the file, we use `storage_manager`
    to save it in the appropriate location.

    """

    response = requests.get(url, stream=True)
    response.raise_for_status()
    file_size = response.headers.get("Content-Length")
    content_type = response.headers.get("Content-Type")
    charset = response.apparent_encoding
    size_threshold = config.get_setting("HARVESTED_RESOURCE_FILE_MAX_MEMORY_SIZE")
    if file_size is not None and int(file_size) < size_threshold:
        logger.debug("Downloading to an in-memory buffer...")
        file_ = uploadedfile.InMemoryUploadedFile(
            None, None, target_name, content_type, file_size, charset)
    else:
        logger.debug("Downloading to a temporary file...")
        file_ = uploadedfile.TemporaryUploadedFile(
            target_name, content_type, file_size, charset)
    with file_.open("wb+") as fd:
        for chunk in response.iter_content(chunk_size=None, decode_unicode=False):
            fd.write(chunk)
        fd.seek(0)
        result = storage_manager.save(target_name, fd)
    return result


def _sanitize_file_name(file_name: str) -> typing.Optional[str]:
    """Inspired by django's `django.http.multipartparser.MultiPartParser.sanitize_file_name()` method."""

    file_name = html.unescape(file_name)
    file_name = file_name.rsplit("/")[-1]
    file_name = file_name.rsplit("\\")[-1]

    if file_name in {"", ".", ".."}:
        result = None
    else:
        result = file_name
    return result
