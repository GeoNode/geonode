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
from six.moves.urllib.parse import urlencode, urlparse, urljoin, parse_qs, urlunparse

from geonode import geoserver
from geonode.utils import check_ogc_backend

from .. import enumerations
from .. import models

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog as catalog
else:
    catalog = None

logger = logging.getLogger(__name__)


def get_proxified_ows_url(url, version=None, proxy_base=None):
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
    if not version:
        version = '1.1.1'

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
    proxified_url = "{proxy_base}?url={ows_url}%3F{ows_request}".format(proxy_base=proxy_base,
                                                                        ows_url=quote(
                                                                            base_ows_url, safe=''),
                                                                        ows_request=ows_request)
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
