#########################################################################
#
# Copyright (C) 2017 OSGeo
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

"""Remote service handling base classes and helpers."""

import logging

from django.conf import settings
from django.db import IntegrityError

from geonode.utils import check_ogc_backend
from geonode import GeoNodeException, geoserver
from geonode.harvesting.tasks import harvest_resources
from geonode.harvesting.models import AsynchronousHarvestingSession, Harvester

from geonode.services import models, enumerations

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog as catalog
else:
    catalog = None

logger = logging.getLogger(__name__)


def get_geoserver_cascading_workspace(create=True):
    """Return the geoserver workspace used for cascaded services
    The workspace can be created it if needed.
    """
    name = getattr(settings, "CASCADE_WORKSPACE", "cascaded-services")
    workspace = catalog.get_workspace(name)
    if workspace is None and create:
        uri = f"http://www.geonode.org/{name}"
        workspace = catalog.create_workspace(name, uri)
    return workspace


def build_unique_resource_name(name, max_length=255):
    """Return a Service/Harvester name that is unique in both models."""
    max_length = max(1, int(max_length))
    candidate = (name or "service")[:max_length]
    base_name = candidate
    idx = 1
    while models.Service.objects.filter(name=candidate).exists() or Harvester.objects.filter(name=candidate).exists():
        suffix = f"-{idx}"
        if len(suffix) >= max_length:
            # When max_length is tiny, keep the most specific part of the suffix.
            candidate = suffix[-max_length:]
        else:
            prefix_len = max_length - len(suffix)
            candidate = f"{base_name[:prefix_len]}{suffix}"
        idx += 1
    return candidate


def create_with_unique_name(name, create_fn, max_length=255, max_attempts=3):
    """Call create_fn(unique_name) with a freshly generated unique candidate name,
    retrying under a new candidate if a concurrent registration raced us to the
    same name and tripped the DB's uniqueness constraint on Service.name.

    build_unique_resource_name's own existence check is not atomic with the
    caller's actual create(), so two concurrent registrations can still land
    on the same candidate; this retries the whole attempt with a fresh name
    instead of surfacing the resulting IntegrityError to the caller.

    :arg create_fn: callable invoked with the candidate name; must perform the
        actual object creation(s) and raise IntegrityError if the name turned
        out to already be taken.
    """
    for attempt in range(max_attempts):
        candidate = build_unique_resource_name(name, max_length=max_length)
        try:
            return create_fn(candidate)
        except IntegrityError:
            if attempt == max_attempts - 1:
                raise


class ServiceHandlerBase(object):  # LGTM: @property will not work in old-style classes
    """Base class for remote service handlers

    This class is not to be instantiated directly, but rather subclassed by
    concrete implementations. The method stubs defined here must be implemented
    in derived classes.

    """

    url = None
    name = None
    service_type = None
    indexing_method = None
    geonode_service_id = None

    def __init__(self, url, geonode_service_id=None):
        self.url = url
        self.geonode_service_id = geonode_service_id

    @property
    def is_cascaded(self):
        return True if self.indexing_method == enumerations.CASCADED else False

    def probe(self):
        from geonode.utils import http_client

        try:
            resp, _ = http_client.request(self.url)
            return resp.status_code in (200, 201)
        except Exception:
            return False

    def get_harvester_configuration_options(self):
        return {}

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance
        Saving the service instance in the database is not a concern of this
        method, it only deals with creating the instance.

        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile
        """

        raise NotImplementedError

    def has_resources(self):
        if self.geonode_service_id:
            _service = models.Service.objects.get(id=self.geonode_service_id)
            if _service.harvester:
                _h = _service.harvester
                num_harvestable_resources = _h.num_harvestable_resources
                if num_harvestable_resources == 0:
                    _h.update_availability()
                    _h.initiate_update_harvestable_resources()
                return num_harvestable_resources > 0
        return False

    def has_unharvested_resources(self, geonode_service):
        if geonode_service or self.geonode_service_id:
            try:
                _service = geonode_service or models.Service.objects.get(id=self.geonode_service_id)
                if _service.harvester:
                    _h = _service.harvester
                    num_harvestable_resources = _h.num_harvestable_resources
                    num_harvestable_resources_selected = _h.harvestable_resources.filter(
                        should_be_harvested=False
                    ).count()
                    if num_harvestable_resources == 0:
                        _h.update_availability()
                        _h.initiate_update_harvestable_resources()
                    if (
                        num_harvestable_resources > 0
                        and num_harvestable_resources_selected <= num_harvestable_resources
                    ):
                        return True
            except Exception as e:
                logger.exception(e)
        return False

    def get_keywords(self):
        raise NotImplementedError

    def get_resource(self, resource_id):
        """Return a single resource's representation."""
        try:
            if self.geonode_service_id:
                _service = models.Service.objects.get(id=self.geonode_service_id)
                if _service.harvester:
                    _h = _service.harvester
                    return _h.harvestable_resources.get(id=resource_id)
        except Exception as e:
            logger.exception(e)
        return None

    def get_resources(self):
        """Return an iterable with the service's resources."""
        if self.geonode_service_id:
            _service = models.Service.objects.get(id=self.geonode_service_id)
            if _service.harvester:
                _h = _service.harvester
                return _h.harvestable_resources.filter(should_be_harvested=False).order_by("id").iterator()
        return []

    def harvest_resource(self, resource_id, geonode_service):
        """Harvest a single resource from the service
        This method creates new ``geonode.layers.models.Dataset``
        instances (and their related objects too) and save them in the
        database.

        :arg resource_id: The resource's identifier
        :type resource_id: str
        :arg geonode_service: The already saved service instance
        :type geonode_service: geonode.services.models.Service
        """
        if geonode_service or self.geonode_service_id:
            try:
                _service = geonode_service or models.Service.objects.get(id=self.geonode_service_id)
                if _service.harvester:
                    _h = _service.harvester
                    _h.harvestable_resources.filter(id=resource_id).update(should_be_harvested=True)
                    _h.status = _h.STATUS_PERFORMING_HARVESTING
                    _h.save()
                    _h_session = AsynchronousHarvestingSession.objects.create(
                        harvester=_h, session_type=AsynchronousHarvestingSession.TYPE_HARVESTING
                    )
                    harvest_resources.apply_async(
                        args=(
                            [
                                resource_id,
                            ],
                            _h_session.pk,
                        ),
                        expiration=30,
                    )
            except Exception as e:
                logger.exception(e)
        else:
            raise GeoNodeException(f"Could not harvest resource id {resource_id} for service {self.name}")


class CascadableServiceHandlerMixin:
    def create_cascaded_store(self, service):
        raise NotImplementedError
