#########################################################################
#
# Copyright (C) 2018 OSGeo
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
import json
import logging
import requests

from uuid import uuid4
from urllib.parse import (
    unquote,
    urlparse,
    urlsplit,
    urlencode,
    parse_qsl,
    ParseResult,
)

from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from geonode import GeoNodeException
from geonode.base.bbox_utils import BBOXHelper
from geonode.harvesting.models import Harvester
from geonode.harvesting.harvesters.wms import OgcWmsHarvester, WebMapService

from .. import enumerations
from ..enumerations import CASCADED
from ..enumerations import INDEXED
from .. import models
from .. import utils
from . import base

logger = logging.getLogger(__name__)


class WmsServiceHandler(base.ServiceHandlerBase,
                        base.CascadableServiceHandlerMixin):
    """Remote service handler for OGC WMS services"""

    service_type = enumerations.WMS

    def __init__(self, url, geonode_service_id=None):
        base.ServiceHandlerBase.__init__(self, url, geonode_service_id)
        self._parsed_service = None
        self.indexing_method = INDEXED if self._offers_geonode_projection() else CASCADED
        self.name = slugify(self.url)[:255]

    @staticmethod
    def get_cleaned_url_params(url):
        # Unquoting URL first so we don't loose existing args
        url = unquote(url)
        # Extracting url info
        parsed_url = urlparse(url)
        # Extracting URL arguments from parsed URL
        get_args = parsed_url.query
        # Converting URL arguments to dict
        parsed_get_args = dict(parse_qsl(get_args))
        # Strip out redoundant args
        _version = parsed_get_args.pop('version', '1.3.0') if 'version' in parsed_get_args else '1.3.0'
        _service = parsed_get_args.pop('service') if 'service' in parsed_get_args else None
        _request = parsed_get_args.pop('request') if 'request' in parsed_get_args else None
        # Converting URL argument to proper query string
        encoded_get_args = urlencode(parsed_get_args, doseq=True)
        # Creating new parsed result object based on provided with new
        # URL arguments. Same thing happens inside of urlparse.
        new_url = ParseResult(
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, encoded_get_args, parsed_url.fragment
        )
        return (new_url, _service, _version, _request)

    @property
    def parsed_service(self):
        cleaned_url, service, version, request = WmsServiceHandler.get_cleaned_url_params(self.url)
        _url, _parsed_service = WebMapService(
            cleaned_url.geturl(),
            version=version)
        return _parsed_service

    def probe(self):
        try:
            return True if len(self.parsed_service.contents) > 0 else False
        except Exception:
            return False

    def create_cascaded_store(self, service):
        ogc_wms_url = service.service_url
        ogc_wms_get_capabilities = service.operations.get('GetCapabilities', None)
        if ogc_wms_get_capabilities and ogc_wms_get_capabilities.get('methods', None):
            for _op_method in ogc_wms_get_capabilities.get('methods'):
                if _op_method.get('type', None).upper() == 'GET' and _op_method.get('url', None):
                    ogc_wms_url = _op_method.get('url')

        store = self._get_store(create=True)
        store.capabilitiesURL = ogc_wms_url
        cat = store.catalog
        cat.save(store)
        return store

    def create_geonode_service(self, owner, parent=None):
        """Create a new geonode.service.models.Service instance
        :arg owner: The user who will own the service instance
        :type owner: geonode.people.models.Profile

        """
        cleaned_url, service, version, request = WmsServiceHandler.get_cleaned_url_params(self.url)
        with transaction.atomic():
            instance = models.Service.objects.create(
                uuid=str(uuid4()),
                base_url=f"{cleaned_url.scheme}://{cleaned_url.netloc}{cleaned_url.path}".encode("utf-8", "ignore").decode('utf-8'),
                extra_queryparams=cleaned_url.query,
                type=self.service_type,
                method=self.indexing_method,
                owner=owner,
                metadata_only=True,
                version=str(self.parsed_service.identification.version).encode("utf-8", "ignore").decode('utf-8'),
                name=self.name,
                title=str(self.parsed_service.identification.title).encode("utf-8", "ignore").decode('utf-8') or self.name,
                abstract=str(self.parsed_service.identification.abstract).encode("utf-8", "ignore").decode('utf-8') or _(
                    "Not provided"),
                operations=OgcWmsHarvester.get_wms_operations(self.parsed_service.url, version=version)
            )
            service_harvester = Harvester.objects.create(
                name=self.name,
                default_owner=owner,
                scheduling_enabled=False,
                remote_url=instance.service_url,
                delete_orphan_resources_automatically=True,
                harvester_type=enumerations.HARVESTER_TYPES[self.service_type],
                harvester_type_specific_configuration=self.get_harvester_configuration_options()
            )
            if service_harvester.update_availability():
                service_harvester.initiate_update_harvestable_resources()
            else:
                logger.exception(GeoNodeException("Could not reach remote endpoint."))
            instance.harvester = service_harvester

        self.geonode_service_id = instance.id
        return instance

    def get_keywords(self):
        return self.parsed_service.identification.keywords

    def _get_cascaded_dataset_fields(self, geoserver_resource):
        name = geoserver_resource.name
        workspace = geoserver_resource.workspace.name if hasattr(geoserver_resource, 'workspace') else None
        store = geoserver_resource.store if hasattr(geoserver_resource, 'store') else None
        bbox = utils.decimal_encode(geoserver_resource.native_bbox) if hasattr(geoserver_resource, 'native_bbox') else \
            utils.decimal_encode(geoserver_resource.boundingBox)
        return {
            "name": name,
            "workspace": workspace or "remoteWorkspace",
            "store": store.name if store and hasattr(store, 'name') else self.name,
            "typename": f"{workspace}:{name}" if workspace not in name else name,
            "alternate": f"{workspace}:{name}" if workspace not in name else name,
            "subtype": "remote",
            "title": geoserver_resource.title,
            "abstract": geoserver_resource.abstract,
            "bbox_polygon": BBOXHelper.from_xy([bbox[0], bbox[2], bbox[1], bbox[3]]).as_polygon(),
            "srid": bbox[4] if len(bbox) > 4 else "EPSG:4326",
        }

    def _get_indexed_dataset_fields(self, dataset_meta):
        bbox = utils.decimal_encode(dataset_meta.boundingBox)
        if len(bbox) < 4:
            raise RuntimeError(
                f"Resource BBOX is not valid: {bbox}")
        return {
            "name": dataset_meta.name,
            "store": self.name,
            "subtype": "remote",
            "workspace": "remoteWorkspace",
            "typename": dataset_meta.name,
            "alternate": dataset_meta.name,
            "title": dataset_meta.title,
            "abstract": dataset_meta.abstract,
            "bbox_polygon": BBOXHelper.from_xy([bbox[0], bbox[2], bbox[1], bbox[3]]).as_polygon(),
            "srid": bbox[4] if len(bbox) > 4 else "EPSG:4326",
            "keywords": [keyword[:100] for keyword in dataset_meta.keywords],
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
        if store is None and create:  # store did not exist. Create it
            logger.debug(f"name: {self.name} - store: {store}")
            store = cat.create_wmsstore(
                name=self.name,
                workspace=workspace,
                user=cat.username,
                password=cat.password
            )
        return store

    def _import_cascaded_resource(self, service, dataset_meta):
        """Import a layer into geoserver in order to enable cascading."""
        store = self._get_store(create=False)
        if not store:
            store = self.create_cascaded_store(service)
        if not store:
            raise RuntimeError("Could not create WMS CASCADE store.")
        cat = store.catalog
        workspace = store.workspace
        dataset_resource = cat.get_resource(
            name=dataset_meta.id,
            store=store,
            workspace=workspace)
        if dataset_resource is None:
            dataset_resource = cat.create_wmslayer(
                workspace, store, dataset_meta.id)
            dataset_resource.projection = getattr(
                settings, "DEFAULT_MAP_CRS", "EPSG:3857")
            # Do not use the geoserver.support.REPROJECT enumeration until
            # https://github.com/boundlessgeo/gsconfig/issues/174
            # has been fixed
            dataset_resource.projection_policy = "REPROJECT_TO_DECLARED"
            cat.save(dataset_resource)
            if dataset_resource is None:
                raise RuntimeError(f"Could not cascade resource {dataset_meta} through "
                                   "geoserver")
            dataset_resource = dataset_resource.resource
        else:
            logger.debug(f"Dataset {dataset_meta.id} is already present. Skipping...")
        dataset_resource.refresh()
        return dataset_resource

    def _offers_geonode_projection(self):
        geonode_projection = getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857")
        contents_gen = self.parsed_service.contents.values()
        geonode_resources = list(r for r in contents_gen if not any(r.children))
        if len(geonode_resources) > 0:
            first_dataset = geonode_resources[0]
            return geonode_projection in first_dataset.crsOptions
        else:
            return geonode_projection


class GeoNodeServiceHandler(WmsServiceHandler):
    """Remote service handler for OGC WMS services"""

    service_type = enumerations.GN_WMS

    def __init__(self, url, geonode_service_id=None):
        base.ServiceHandlerBase.__init__(self, url, geonode_service_id)
        self.indexing_method = INDEXED
        self.name = slugify(self.url)[:255]

    @property
    def parsed_service(self):
        cleaned_url, service, version, request = WmsServiceHandler.get_cleaned_url_params(self.ows_endpoint())
        _url, _parsed_service = WebMapService(
            cleaned_url.geturl(),
            version=version)
        return _parsed_service

    def probe(self):
        return base.ServiceHandlerBase.probe(self)

    def get_harvester_configuration_options(self):
        return {
            "harvest_datasets": True,
            "harvest_documents": True,
            "copy_datasets": False,
            "copy_documents": False
        }

    def ows_endpoint(self):
        url = urlsplit(self.url)
        base_url = f'{url.scheme}://{url.netloc}/'
        response = requests.get(
            f'{base_url}api/ows_endpoints/', {},
            timeout=30,
            verify=False)
        content = response.content
        status = response.status_code
        content_type = response.headers['Content-Type']

        # NEW-style OWS Enabled GeoNode
        if int(status) == 200 and 'application/json' == content_type:
            try:
                _json_obj = json.loads(content)
                if 'data' in _json_obj:
                    data = _json_obj['data']
                    for ows_endpoint in data:
                        if ows_endpoint['type'] in ('OGC:OWS', 'OGC:WMS'):
                            _params = url.query if url.query else ''
                            _query_separator = '?' if '?' not in ows_endpoint['url'] else ''
                            _url = f"{ows_endpoint['url']}{_query_separator}{_params}"
                            return _url
            except Exception as e:
                logger.exception(e)
                return False

        # OLD-style not OWS Enabled GeoNode
        _url = f"{url.scheme}://{url.netloc}/geoserver/ows"
        return _url
