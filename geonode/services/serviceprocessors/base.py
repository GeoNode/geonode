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

from urllib.parse import quote

from django.conf import settings
from django.urls import reverse
from urllib.parse import (
    urlencode,
    urlparse,
    urljoin,
    parse_qs,
    urlunparse)

from geonode.utils import check_ogc_backend
from geonode import GeoNodeException, geoserver
from geonode.harvesting.tasks import harvest_resources
from geonode.harvesting.models import AsynchronousHarvestingSession

from .. import models
from .. import enumerations

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog as catalog
else:
    catalog = None

logger = logging.getLogger(__name__)


def get_proxified_ows_url(url, version='1.3.0', proxy_base=None):
    """
    clean an OWS URL of basic service elements
    source: https://stackoverflow.com/a/11640565
    """

    if url is None or not url.startswith('http'):
        return url

    filtered_kvp = {}
    basic_service_elements = ('service', 'version', 'request')

    parsed = urlparse(url)
    qd = parse_qs(parsed.query, keep_blank_values=True)
    version = qd['version'][0] if 'version' in qd else version

    for key, value in qd.items():
        if key.lower() not in basic_service_elements:
            filtered_kvp[key] = value

    base_ows_url = urlunparse([
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        quote(urlencode(filtered_kvp, doseq=True), safe=''),
        parsed.fragment
    ])

    ows_request = quote(
        urlencode(
            qd,
            doseq=True),
        safe='') if qd else f"version%3D{version}%26request%3DGetCapabilities%26service%3Dwms"
    proxy_base = proxy_base if proxy_base else urljoin(
        settings.SITEURL, reverse('proxy'))
    ows_url = quote(base_ows_url, safe='')
    proxified_url = f"{proxy_base}?url={ows_url}%3F{ows_request}"
    return (version, proxified_url, base_ows_url)


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
                        should_be_harvested=False).count()
                    if num_harvestable_resources > 0 and num_harvestable_resources_selected <= num_harvestable_resources:
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
                return _h.harvestable_resources.filter(
                    should_be_harvested=False).order_by('id').iterator()
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
                        harvester=_h,
                        session_type=AsynchronousHarvestingSession.TYPE_HARVESTING
                    )
                    harvest_resources.apply_async(args=([resource_id, ], _h_session.pk))
            except Exception as e:
                logger.exception(e)
                raise GeoNodeException(e)
        else:
            raise GeoNodeException(f"Could not harvest resource id {resource_id} for service {self.name}")


class CascadableServiceHandlerMixin:

    def create_cascaded_store(self, service):
        raise NotImplementedError
