#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import logging
import typing
from urllib.parse import urlencode

import requests
from lxml import etree
from django.utils.translation import gettext_lazy as _

from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.utils import XML_PARSER, WebMapService, safe_request_url
from geonode.sources.base import BaseSourceProvider, BrowseEntry, Capability, SourceProviderError
from geonode.sources.wms.auth import WmsAuthHandler
from geonode.sources.wms.forms import WmsConnectionForm

logger = logging.getLogger(__name__)

WMS_CAPABILITIES_ROOTS = {"1.3.0": "WMS_Capabilities", "1.1.1": "WMT_MS_Capabilities"}


class WmsSourceProvider(BaseSourceProvider):
    """
    Layers of an OGC WMS, listed from its GetCapabilities document: one entry per named leaf layer.
    The uri is wms:?layer=<name>, relative to the connection that stores the url and the credentials
    """

    key = "wms"
    label = _("OGC WMS")
    # for now the layers are only looked at, never changed
    declared_capabilities = Capability.READ
    connection_form = WmsConnectionForm

    TIMEOUT = 30

    def _get_capabilities(self, handler: WmsAuthHandler):
        """Fetch and parse the capabilities, raising SourceProviderError when they cannot be read"""
        try:
            # SafeSession checks the url and every redirect: http(s) only, no private or local host
            response = safe_request_url(
                "GET",
                handler.url,
                params={"service": "WMS", "request": "GetCapabilities", "version": handler.version},
                auth=handler.get_request_auth(),
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            # no entities and no network: the 1.1.1 DOCTYPE is read but never resolved
            root = etree.fromstring(response.content, parser=XML_PARSER)
        except (requests.RequestException, etree.XMLSyntaxError) as e:
            raise SourceProviderError("Could not read the WMS capabilities") from e
        if etree.QName(root).localname != WMS_CAPABILITIES_ROOTS[handler.version]:
            raise SourceProviderError(
                f"Not a WMS {handler.version} capabilities document: {etree.QName(root).localname}"
            )
        try:
            # with the xml given owslib only parses: the root is serialized without the DOCTYPE, nothing to resolve
            _url, _wms = WebMapService(handler.url, version=handler.version, xml=etree.tostring(root))
            return _wms
        except Exception as e:
            # owslib raises whatever its parsing hits on a malformed document
            raise SourceProviderError("Could not parse the WMS capabilities") from e

    def test_connection(self, auth_config: AuthConfig) -> typing.Tuple[bool, str]:
        try:
            self._get_capabilities(auth_handler_registry.build(auth_config))
            return True, ""
        except SourceProviderError as e:
            # the cause may expose server details, the caller only gets a generic reason
            logger.exception(e)
            return False, str(_("Could not read the WMS capabilities with the provided parameters"))

    def browse(self, auth_config: AuthConfig) -> typing.List[BrowseEntry]:
        """List the named leaf layers: group layers only collect other layers"""
        _wms = self._get_capabilities(auth_handler_registry.build(auth_config))
        return [self._to_browse_entry(layer) for layer in _wms.contents.values() if not layer.children]

    def _to_browse_entry(self, layer) -> BrowseEntry:
        return BrowseEntry(
            # the scheme is the provider key, so that the uri always tells which provider reads it
            uri=f"{self.key}:?{urlencode({'layer': layer.name})}",
            title=layer.title or layer.name.rpartition(":")[-1],
            details={
                "name": layer.name,
                "abstract": layer.abstract or "",
                "keywords": list(layer.keywords or []),
                # west, south, east, north in EPSG:4326, when the service advertises it
                "bbox": list(layer.boundingBoxWGS84) if layer.boundingBoxWGS84 else None,
            },
        )
