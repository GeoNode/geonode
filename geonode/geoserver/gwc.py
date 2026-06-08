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
import requests

from xml.sax.saxutils import escape

from geoserver.catalog import FailedRequestError
from requests.auth import HTTPBasicAuth

from geonode.geoserver.helpers import ogc_server_settings
from django.conf import settings

logger = logging.getLogger(__name__)


class GWCClient:
    """
    A GeoWebCache REST client for interacting with the GWC API.
    """

    def __init__(self) -> None:
        self.base_url = f"{ogc_server_settings.LOCATION}gwc/rest/"
        self.headers = {"Content-Type": "text/xml"}

    def _post(self, urlpath, data):
        _user, _password = ogc_server_settings.credentials

        url = f"{self.base_url}{urlpath}"
        r = requests.post(url=url, data=data, auth=HTTPBasicAuth(_user, _password))
        logger.debug(f'POST response: code:{r.status_code} --> "{r.text}"')
        return r

    @staticmethod
    def _validate_layer_name(layer_name: str, workspace: str | None = None) -> str:
        if ":" not in layer_name:
            workspace = workspace or getattr(settings, "DEFAULT_WORKSPACE", "geonode")
            logger.info(
                "Workspace not provided for layer '%s'. Using default workspace '%s'.",
                layer_name,
                workspace,
            )

            layer_name = f"{workspace}:{layer_name}"
        return layer_name

    def truncate_layer(self, layer_name: str, workspace: str | None = None) -> None:
        """
        Truncate all cached tiles for a GWC layer.
        """
        layer_name = self._validate_layer_name(layer_name, workspace)
        body = f"<truncateLayer><layerName>{escape(layer_name)}</layerName></truncateLayer>"
        r = self._post("masstruncate", body)
        if r.status_code != 200:
            raise FailedRequestError(f'Error truncating GWC layer: {r.status_code}: "{r.text}"')

        logger.info("Successfully truncated GWC cache for layer '%s'.", layer_name)

    def truncate_all(self) -> None:
        """
        Clear the entire GWC cache.
        """
        r = self._post("masstruncate", "<truncateAll/>")

        if r.status_code != 200:
            raise FailedRequestError(f'Error truncating all GWC layers: {r.status_code}: "{r.text}"')

        logger.info("Successfully truncated the whole GWC cache.")
