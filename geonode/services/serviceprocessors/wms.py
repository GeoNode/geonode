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

"""Utilities for enabling OGC WMS remote services in geonode."""

import logging
from urlparse import urlsplit
from uuid import uuid4

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.layers.utils import create_thumbnail
from owslib.wms import WebMapService

from .. import enumerations
from ..enumerations import CASCADED
from ..enumerations import INDEXED
from .. import models

from . import base

logger = logging.getLogger(__name__)


class WmsServiceHandler(base.ServiceHandlerBase,
                        base.CascadableServiceHandlerMixin):
    """Remote service handler for OGC WMS services"""

    service_type = enumerations.WMS

    def __init__(self, url):
        self.parsed_service = WebMapService(url)
        self.indexing_method = (
            INDEXED if self._offers_geonode_projection() else CASCADED)
        self.url = self.parsed_service.url
        _title = self.parsed_service.identification.title
        self.name = slugify(
            _title if _title else urlsplit(self.url).netloc)[:40]

    def create_cascaded_store(self):
        store = self._get_store(create=True)
        store.capabilitiesURL = self.url
        cat = store.catalog
        cat.save(store)
        return store

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance

        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile

        """

        instance = models.Service(
            uuid=str(uuid4()),
            base_url=self.url,
            type=self.service_type,
            method=self.indexing_method,
            owner=owner,
            parent=parent,
            version=self.parsed_service.identification.version,
            name=self.name,
            title=self.parsed_service.identification.title or self.name,
            abstract=self.parsed_service.identification.abstract or _(
                "Not provided"),
            online_resource=self.parsed_service.provider.url,
        )
        return instance

    def get_keywords(self):
        return self.parsed_service.identification.keywords

    def get_resource(self, resource_id):
        return self.parsed_service.contents[resource_id]

    def get_resources(self):
        """Return an iterable with the service's resources.

        For WMS we take into account that some layers are just logical groups
        of metadata and do not return those.

        """

        contents_gen = self.parsed_service.contents.itervalues()
        return (r for r in contents_gen if not any(r.children))

    def harvest_resource(self, resource_id, geonode_service):
        """Harvest a single resource from the service

        This method will try to create new ``geonode.layers.models.Layer``
        instance (and its related objects too).

        :arg resource_id: The resource's identifier
        :type resource_id: str
        :arg geonode_service: The already saved service instance
        :type geonode_service: geonode.services.models.Service

        """

        layer_meta = self.get_resource(resource_id)
        logger.debug("layer_meta: {}".format(layer_meta))
        if self.indexing_method == CASCADED:
            logger.debug("About to import cascaded layer...")
            geoserver_resource = self._import_cascaded_resource(layer_meta)
            resource_fields = self._get_cascaded_layer_fields(
                geoserver_resource)
            keywords = []
        else:
            resource_fields = self._get_indexed_layer_fields(layer_meta)
            keywords = resource_fields.pop("keywords")
        existance_test_qs = Layer.objects.filter(
            name=resource_fields["name"],
            store=resource_fields["store"],
            workspace=resource_fields["workspace"]
        )
        if existance_test_qs.exists():
            raise RuntimeError(
                "Resource {!r} has already been harvested".format(resource_id))
        # bear in mind that in ``geonode.layers.models`` there is a
        # ``pre_save_layer`` function handler that is connected to the
        # ``pre_save`` signal for the Layer model. This handler does a check
        # for common fields (such as abstract and title) and adds
        # sensible default values
        geonode_layer = Layer(
            owner=geonode_service.owner,
            service=geonode_service,
            uuid=str(uuid4()),
            **resource_fields
        )
        geonode_layer.full_clean()
        geonode_layer.save()
        geonode_layer.keywords.add(*keywords)
        geonode_layer.set_default_permissions()
        self._create_layer_service_link(geonode_layer)
        self._create_layer_legend_link(geonode_layer)
        self._create_layer_thumbnail(geonode_layer)

    def has_resources(self):
        return True if len(self.parsed_service.contents) > 1 else False

    def _create_layer_thumbnail(self, geonode_layer):
        """Create a thumbnail with a WMS request."""
        params = {
            "service": self.service_type,
            "version": self.parsed_service.version,
            "request": "GetMap",
            "layers": geonode_layer.alternate.encode('utf-8'),
            "bbox": geonode_layer.bbox_string,
            "srs": "EPSG:4326",
            "width": "200",
            "height": "150",
            "format": "image/png",
        }
        kvp = "&".join("{}={}".format(*item) for item in params.items())
        thumbnail_remote_url = "{}?{}".format(
            geonode_layer.ows_url, kvp)
        logger.debug("thumbnail_remote_url: {}".format(thumbnail_remote_url))
        create_thumbnail(
            instance=geonode_layer,
            thumbnail_remote_url=thumbnail_remote_url,
            thumbnail_create_url=None,
            check_bbox=False,
            overwrite=True
        )

    def _create_layer_legend_link(self, geonode_layer):
        """Get the layer's legend and save it locally

        Regardless of the service being INDEXED or CASCADED we're always
        creating the legend by making a request directly to the original
        service.

        """

        params = {
            "service": self.service_type,
            "version": self.parsed_service.version,
            "request": "GetLegendGraphic",
            "format": "image/png",
            "width": 20,
            "height": 20,
            "layer": geonode_layer.name,
            "legend_options": (
                "fontAntiAliasing:true;fontSize:12;forceLabels:on")
        }
        kvp = "&".join("{}={}".format(*item) for item in params.items())
        legend_url = "{}?{}".format(self.url, kvp)
        logger.debug("legend_url: {}".format(legend_url))
        Link.objects.get_or_create(
            resource=geonode_layer.resourcebase_ptr,
            url=legend_url,
            defaults={
                "extension": 'png',
                "name": 'Legend',
                "url": legend_url,
                "mime": 'image/png',
                "link_type": 'image',
            }
        )

    def _create_layer_service_link(self, geonode_layer):
        Link.objects.get_or_create(
            resource=geonode_layer.resourcebase_ptr,
            url=geonode_layer.ows_url,
            defaults={
                "extension": "html",
                "name": "OGC {}: {} Service".format(
                    geonode_layer.service.type,
                    geonode_layer.store
                ),
                "url": geonode_layer.ows_url,
                "mime": "text/html",
                "link_type": "OGC:{}".format(geonode_layer.service.type),
            }
        )

    def _get_cascaded_layer_fields(self, geoserver_resource):
        name = geoserver_resource.name
        workspace = geoserver_resource.workspace.name
        store = geoserver_resource.store
        bbox = geoserver_resource.latlon_bbox
        return {
            "name": name,
            "workspace": workspace,
            "store": store.name,
            "typename": "{}:{}".format(workspace, name),
            "storeType": "remoteStore",  # store.resource_type,
            "title": geoserver_resource.title,
            "abstract": geoserver_resource.abstract,
            "bbox_x0": bbox[0],
            "bbox_x1": bbox[1],
            "bbox_y0": bbox[2],
            "bbox_y1": bbox[3],
        }

    def _get_indexed_layer_fields(self, layer_meta):
        bbox = layer_meta.boundingBoxWGS84
        return {
            "name": layer_meta.name,
            "store": self.name,
            "storeType": "remoteStore",
            "workspace": "remoteWorkspace",
            "typename": layer_meta.name,
            "title": layer_meta.title,
            "abstract": layer_meta.abstract,
            "bbox_x0": bbox[0],
            "bbox_x1": bbox[2],
            "bbox_y0": bbox[1],
            "bbox_y1": bbox[3],
            "keywords": [keyword[:100] for keyword in layer_meta.keywords],
        }

    def _get_store(self, create=True):
        """Return the geoserver store associated with this service.

        The store may optionally be created if it doesn't exist already.
        Store is assumed to be (and created) named after the instance's name
        and belongs to the default geonode workspace for cascaded layers.

        """

        workspace = base.get_geoserver_cascading_workspace(create=create)
        cat = workspace.catalog
        store = cat.get_store(self.name, workspace=workspace)
        logger.debug("name: {}".format(self.name))
        logger.debug("store: {}".format(store))
        if store is None and create:  # store did not exist. Create it
            store = cat.create_wmsstore(
                name=self.name,
                workspace=workspace,
                user=cat.username,
                password=cat.password
            )
        return store

    def _import_cascaded_resource(self, layer_meta):
        """Import a layer into geoserver in order to enable cascading."""
        store = self._get_store(create=False)
        cat = store.catalog
        workspace = store.workspace
        layer_resource = cat.get_resource(layer_meta.id, store, workspace)
        if layer_resource is None:
            layer_resource = cat.create_wmslayer(
                workspace, store, layer_meta.id)
            layer_resource.projection = getattr(
                settings, "DEFAULT_MAP_CRS", "EPSG:3857")
            # Do not use the geoserver.support.REPROJECT enumeration until
            # https://github.com/boundlessgeo/gsconfig/issues/174
            # has been fixed
            layer_resource.projection_policy = "REPROJECT_TO_DECLARED"
            cat.save(layer_resource)
            if layer_resource is None:
                raise RuntimeError("Could not cascade resource {!r} through "
                                   "geoserver".format(layer_meta))
        else:
            logger.info("Layer {} is already present. Skipping...".format(
                layer_meta.id))
        return layer_resource

    def _offers_geonode_projection(self):
        geonode_projection = getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857")
        first_layer = list(self.get_resources())[0]
        return geonode_projection in first_layer.crsOptions


def _get_valid_name(proposed_name):
    """Return a unique slug name for a service"""
    slug_name = slugify(proposed_name)
    name = slug_name
    if len(slug_name) > 40:
        name = slug_name[:40]
    return name
