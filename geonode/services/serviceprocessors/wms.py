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
import traceback

from uuid import uuid4
from urllib.parse import (
    urljoin,
    unquote,
    urlparse,
    urlsplit,
    urlencode,
    parse_qsl,
    ParseResult,
)

from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from geonode.base.models import Link, TopicCategory
from geonode.layers.models import Layer
from geonode.layers.utils import resolve_regions
from geonode.thumbs.thumbnails import create_thumbnail
from geonode.geoserver.helpers import set_attributes_from_geoserver
from geonode.utils import http_client

from owslib.map import wms111, wms130
from owslib.util import clean_ows_url

from .. import enumerations
from ..enumerations import CASCADED
from ..enumerations import INDEXED
from .. import models
from .. import utils
from . import base

logger = logging.getLogger(__name__)


def WebMapService(url,
                  version='1.3.0',
                  xml=None,
                  username=None,
                  password=None,
                  parse_remote_metadata=False,
                  timeout=30,
                  headers=None,
                  proxy_base=None):
    """
    API for Web Map Service (WMS) methods and metadata.

    Currently supports only version 1.1.1 of the WMS protocol.
    """
    '''wms factory function, returns a version specific WebMapService object

    @type url: string
    @param url: url of WFS capabilities document
    @type xml: string
    @param xml: elementtree object
    @type parse_remote_metadata: boolean
    @param parse_remote_metadata: whether to fully process MetadataURL elements
    @param timeout: time (in seconds) after which requests should timeout
    @return: initialized WebFeatureService_2_0_0 object
    '''

    if not proxy_base:
        clean_url = clean_ows_url(url)
        base_ows_url = clean_url
    else:
        (clean_version, proxified_url, base_ows_url) = base.get_proxified_ows_url(
            url, version=version, proxy_base=proxy_base)
        version = clean_version
        clean_url = proxified_url

    if version in ['1.1.1']:
        return (base_ows_url, wms111.WebMapService_1_1_1(clean_url, version=version, xml=xml,
                                                         parse_remote_metadata=parse_remote_metadata,
                                                         username=username, password=password,
                                                         timeout=timeout, headers=headers))
    elif version in ['1.3.0']:
        return (base_ows_url, wms130.WebMapService_1_3_0(clean_url, version=version, xml=xml,
                                                         parse_remote_metadata=parse_remote_metadata,
                                                         username=username, password=password,
                                                         timeout=timeout, headers=headers))
    raise NotImplementedError(
        f'The WMS version ({version}) you requested is not implemented. Please use 1.1.1 or 1.3.0.')


class WmsServiceHandler(base.ServiceHandlerBase,
                        base.CascadableServiceHandlerMixin):
    """Remote service handler for OGC WMS services"""

    service_type = enumerations.WMS

    def __init__(self, url):
        base.ServiceHandlerBase.__init__(self, url)
        self.proxy_base = urljoin(
            settings.SITEURL, reverse('proxy'))
        self.url = url
        self._parsed_service = None
        self.indexing_method = (
            INDEXED if self._offers_geonode_projection() else CASCADED)
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
        ).geturl()
        return (new_url, _service, _version, _request)

    @property
    def parsed_service(self):
        cleaned_url, service, version, request = WmsServiceHandler.get_cleaned_url_params(self.url)
        ogc_server_settings = settings.OGC_SERVER['default']
        _url, _parsed_service = WebMapService(
            cleaned_url,
            version=version,
            proxy_base=None,
            timeout=ogc_server_settings.get('TIMEOUT', 60))
        return _parsed_service

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
            proxy_base=None,  # self.proxy_base,
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
        contents_gen = self.parsed_service.contents.values()
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
        logger.debug(f"layer_meta: {layer_meta}")
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
                f"Resource {resource_id!r} has already been harvested")
        resource_fields["keywords"] = keywords
        resource_fields["is_approved"] = True
        resource_fields["is_published"] = True
        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            resource_fields["is_approved"] = False
            resource_fields["is_published"] = False
        try:
            geonode_layer = self._create_layer(geonode_service, **resource_fields)
            self._create_layer_service_link(geonode_layer)
            self._create_layer_legend_link(geonode_layer)
            self._create_layer_thumbnail(geonode_layer)
        except Exception as e:
            logger.error(e)

    def has_resources(self):
        return True if len(self.parsed_service.contents) > 0 else False

    def _create_layer(self, geonode_service, **resource_fields):
        # bear in mind that in ``geonode.layers.models`` there is a
        # ``pre_save_layer`` function handler that is connected to the
        # ``pre_save`` signal for the Layer model. This handler does a check
        # for common fields (such as abstract and title) and adds
        # sensible default values
        keywords = resource_fields.pop("keywords") or []
        geonode_layer = Layer(
            owner=geonode_service.owner,
            remote_service=geonode_service,
            uuid=str(uuid4()),
            **resource_fields
        )
        geonode_layer.full_clean()
        try:
            geonode_layer.save(notify=True)
        except Exception as e:
            logger.error(e)
        geonode_layer.keywords.add(*keywords)
        geonode_layer.set_default_permissions()
        set_attributes_from_geoserver(geonode_layer)
        return geonode_layer

    def _create_layer_thumbnail(self, geonode_layer):
        """Create a thumbnail with a WMS request."""

        create_thumbnail(
            instance=geonode_layer,
            wms_version=self.parsed_service.version,
            bbox=geonode_layer.bbox,
            forced_crs=geonode_layer.srid,
            overwrite=True,
        )

    def _create_layer_legend_link(self, geonode_layer):
        """Get the layer's legend and save it locally

        Regardless of the service being INDEXED or CASCADED we're always
        creating the legend by making a request directly to the original
        service.
        """
        _p_url = urlparse(self.url)
        _q_separator = "&" if _p_url.query else "?"
        params = {
            "service": "WMS",
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
        legend_url = f"{geonode_layer.remote_service.service_url}{_q_separator}{kvp}"
        logger.debug(f"legend_url: {legend_url}")
        Link.objects.get_or_create(
            resource=geonode_layer.resourcebase_ptr,
            url=legend_url,
            name='Legend',
            defaults={
                "extension": 'png',
                "name": 'Legend',
                "url": legend_url,
                "mime": 'image/png',
                "link_type": 'image',
            }
        )

    def _create_layer_service_link(self, geonode_layer):
        ogc_wms_url = geonode_layer.ows_url
        ogc_wms_name = f'OGC WMS: {geonode_layer.store} Service'
        ogc_wms_link_type = 'OGC:WMS'
        if Link.objects.filter(resource=geonode_layer.resourcebase_ptr,
                               name=ogc_wms_name,
                               link_type=ogc_wms_link_type,).count() < 2:
            Link.objects.update_or_create(
                resource=geonode_layer.resourcebase_ptr,
                name=ogc_wms_name,
                link_type=ogc_wms_link_type,
                defaults=dict(
                    extension='html',
                    url=ogc_wms_url,
                    mime='text/html',
                    link_type=ogc_wms_link_type
                )
            )

    def _get_cascaded_layer_fields(self, geoserver_resource):
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
            "storeType": "remoteStore",
            "title": geoserver_resource.title,
            "abstract": geoserver_resource.abstract,
            "bbox_x0": bbox[0],
            "bbox_x1": bbox[1],
            "bbox_y0": bbox[2],
            "bbox_y1": bbox[3],
            "srid": bbox[4] if len(bbox) > 4 else "EPSG:4326",
        }

    def _get_indexed_layer_fields(self, layer_meta):
        bbox = utils.decimal_encode(layer_meta.boundingBox)
        return {
            "name": layer_meta.name,
            "store": self.name,
            "storeType": "remoteStore",
            "workspace": "remoteWorkspace",
            "typename": layer_meta.name,
            "alternate": layer_meta.name,
            "title": layer_meta.title,
            "abstract": layer_meta.abstract,
            "bbox_x0": bbox[0],
            "bbox_x1": bbox[2],
            "bbox_y0": bbox[1],
            "bbox_y1": bbox[3],
            "srid": bbox[4] if len(bbox) > 4 else "EPSG:4326",
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
        logger.debug(f"name: {self.name}")
        logger.debug(f"store: {store}")
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
        layer_resource = cat.get_resource(
            name=layer_meta.id,
            store=store,
            workspace=workspace)
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
                raise RuntimeError(f"Could not cascade resource {layer_meta!r} through geoserver")
            layer_resource = layer_resource.resource
        else:
            logger.debug(f"Layer {layer_meta.id} is already present. Skipping...")
        layer_resource.refresh()
        return layer_resource

    def _offers_geonode_projection(self):
        geonode_projection = getattr(settings, "DEFAULT_MAP_CRS", "EPSG:3857")
        if len(list(self.get_resources())) > 0:
            first_layer = list(self.get_resources())[0]
            return geonode_projection in first_layer.crsOptions
        else:
            return geonode_projection


class GeoNodeServiceHandler(WmsServiceHandler):
    """Remote service handler for OGC WMS services"""

    service_type = enumerations.GN_WMS

    LAYER_FIELDS = [
        "abstract",
        "bbox_x0",
        "bbox_x1",
        "bbox_y0",
        "bbox_y1",
        "srid",
        "constraints_other",
        "data_quality_statement",
        "date",
        "date_type",
        "edition",
        "has_time",
        "language",
        "license",
        "maintenance_frequency",
        "name",
        "purpose",
        "restriction_code_type",
        "spatial_representation_type",
        "supplemental_information",
        "temporal_extent_end",
        "temporal_extent_start",
        "title"
    ]

    def __init__(self, url):
        self.proxy_base = urljoin(
            settings.SITEURL, reverse('proxy'))
        ogc_server_settings = settings.OGC_SERVER['default']
        url = self._probe_geonode_wms(url)
        self.url, _ = WebMapService(
            url,
            proxy_base=self.proxy_base,
            timeout=ogc_server_settings.get('TIMEOUT', 60))
        self.indexing_method = (
            INDEXED if self._offers_geonode_projection() else CASCADED)
        self.name = slugify(self.url)[:255]

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
                f"Resource {resource_id!r} has already been harvested")
        resource_fields["keywords"] = keywords
        resource_fields["is_approved"] = True
        resource_fields["is_published"] = True
        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            resource_fields["is_approved"] = False
            resource_fields["is_published"] = False
        try:
            geonode_layer = self._create_layer(geonode_service, **resource_fields)
            self._enrich_layer_metadata(geonode_layer)
            self._create_layer_service_link(geonode_layer)
            self._create_layer_legend_link(geonode_layer)
        except Exception as e:
            logger.error(e)

    def _probe_geonode_wms(self, raw_url):
        url = urlsplit(raw_url)
        base_url = f'{url.scheme}://{url.netloc}/'
        response = requests.get(
            f'{base_url}api/ows_endpoints/', {},
            timeout=30,
            verify=False)
        content = response.content
        status = response.status_code
        content_type = response.headers['Content-Type']

        # NEW-style OWS Enabled GeoNode
        if status == 200 and 'application/json' == content_type:
            try:
                _json_obj = json.loads(content)
                if 'data' in _json_obj:
                    data = _json_obj['data']
                    for ows_endpoint in data:
                        if 'OGC:OWS' == ows_endpoint['type']:
                            return f"{ows_endpoint['url']}?{url.query}"
            except Exception:
                pass

        # OLD-style not OWS Enabled GeoNode
        _url = f"{url.scheme}://{url.netloc}/geoserver/ows"
        return _url

    def _enrich_layer_metadata(self, geonode_layer):
        workspace, layername = geonode_layer.name.split(
            ":") if ":" in geonode_layer.name else (None, geonode_layer.name)
        url = urlsplit(self.url)
        base_url = f'{url.scheme}://{url.netloc}/'
        response = requests.get(
            f'{base_url}api/layers/?name={layername}', {},
            timeout=10,
            verify=False)
        content = response.content
        status = response.status_code
        content_type = response.headers['Content-Type']

        if status == 200 and 'application/json' == content_type:
            try:
                if isinstance(content, bytes):
                    content = content.decode('UTF-8')
                _json_obj = json.loads(content)
                if _json_obj['meta']['total_count'] == 1:
                    _layer = _json_obj['objects'][0]
                    if _layer:
                        r_fields = {}

                        # Update plain fields
                        for field in GeoNodeServiceHandler.LAYER_FIELDS:
                            if field in _layer and _layer[field]:
                                r_fields[field] = _layer[field]
                        if r_fields:
                            Layer.objects.filter(
                                id=geonode_layer.id).update(
                                **r_fields)
                            geonode_layer.refresh_from_db()

                        # Update Thumbnail
                        if "thumbnail_url" in _layer and _layer["thumbnail_url"]:
                            thumbnail_remote_url = _layer["thumbnail_url"]
                            _url = urlsplit(thumbnail_remote_url)
                            if not _url.scheme:
                                thumbnail_remote_url = f"{geonode_layer.remote_service.service_url}{_url.path}"
                            resp, image = http_client.request(
                                thumbnail_remote_url)
                            if 'ServiceException' in str(image) or \
                               resp.status_code < 200 or resp.status_code > 299:
                                msg = f'Unable to obtain thumbnail: {image}'
                                logger.debug(msg)

                                # Replace error message with None.
                                image = None

                            if image is not None:
                                thumbnail_name = f'layer-{geonode_layer.uuid}-thumb.png'
                                geonode_layer.save_thumbnail(
                                    thumbnail_name, image=image)
                            else:
                                self._create_layer_thumbnail(geonode_layer)
                        else:
                            self._create_layer_thumbnail(geonode_layer)

                        # Add Keywords
                        if "keywords" in _layer and _layer["keywords"]:
                            keywords = _layer["keywords"]
                            if keywords:
                                geonode_layer.keywords.clear()
                                geonode_layer.keywords.add(*keywords)

                        # Add Regions
                        if "regions" in _layer and _layer["regions"]:
                            (regions_resolved, regions_unresolved) = resolve_regions(
                                _layer["regions"])
                            if regions_resolved:
                                geonode_layer.regions.clear()
                                geonode_layer.regions.add(*regions_resolved)

                        # Add Topic Category
                        if "category__gn_description" in _layer and _layer["category__gn_description"]:
                            try:
                                categories = TopicCategory.objects.filter(
                                    Q(gn_description__iexact=_layer["category__gn_description"]))
                                if categories:
                                    geonode_layer.category = categories[0]
                            except Exception:
                                traceback.print_exc()
            except Exception:
                traceback.print_exc()
            finally:
                try:
                    geonode_layer.save(notify=True)
                except Exception as e:
                    logger.error(e)


def _get_valid_name(proposed_name):
    """Return a unique slug name for a service"""
    slug_name = slugify(proposed_name)
    name = slug_name
    if len(slug_name) > 40:
        name = slug_name[:40]
    return name
