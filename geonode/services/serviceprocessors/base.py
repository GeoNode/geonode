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
from geoserver.catalog import Catalog

from .. import enumerations
from .. import models

logger = logging.getLogger(__name__)


def get_geoserver_cascading_workspace(create=True):
    """Return the geoserver workspace used for cascaded services

    The workspace can be created it if needed.

    """

    catalog = Catalog(
        service_url=settings.OGC_SERVER["default"]["LOCATION"] + "rest",
        username=settings.OGC_SERVER["default"]["USER"],
        password=settings.OGC_SERVER["default"]["PASSWORD"]
    )
    name = getattr(settings, "CASCADE_WORKSPACE", "cascaded-services")
    workspace = catalog.get_workspace(name)
    if workspace is None and create:
        uri = "http://www.geonode.org/{}".format(name)
        workspace = catalog.create_workspace(name, uri)
    return workspace


class ServiceHandlerBase(object):
    """Base class for remote service handlers

    This class is not to be instantiated directly, but rather subclassed by
    concrete implementations. The method stubs defined here must be implemented
    in derived classes.

    """

    url = None
    service_type = None
    name = ""
    indexing_method = None

    def __init__(self, url):
        self.url = url

    @property
    def is_cascaded(self):
        return True if self.indexing_method == enumerations.CASCADED else False

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance

        Saving the service instance in the database is not a concern of this
        method, it only deals with creating the instance.

        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile

        """

        raise NotImplementedError

    def get_keywords(self):
        raise NotImplementedError

    def get_resource(self, resource_id):
        """Return a single resource's representation."""
        raise NotImplementedError

    def get_resources(self):
        """Return an iterable with the service's resources."""
        raise NotImplementedError

    def harvest_resource(self, resource_id, geonode_service):
        """Harvest a single resource from the service

        This method creates new ``geonode.layers.models.Layer``
        instances (and their related objects too) and save them in the
        database.

        :arg resource_id: The resource's identifier
        :type resource_id: str
        :arg geonode_service: The already saved service instance
        :type geonode_service: geonode.services.models.Service

        """

        raise NotImplementedError

    def has_resources(self):
        raise NotImplementedError

    def has_unharvested_resources(self, geonode_service):
        already_done = list(models.HarvestJob.objects.values_list(
            "resource_id", flat=True).filter(service=geonode_service))
        for resource in self.get_resources():
            if resource.id not in already_done:
                result = True
                break
        else:
            result = False
        return result


class CascadableServiceHandlerMixin(object):

    def create_cascaded_store(self):
        raise NotImplementedError
