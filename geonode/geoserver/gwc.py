#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from xml.sax.saxutils import escape

from geoserver.catalog import FailedRequestError

from geonode.utils import http_client
from geonode.geoserver.helpers import ogc_server_settings, _user
from django.conf import settings

logger = logging.getLogger(__name__)


class GWCClient:
    """
    A GeoWebCache REST client for interacting with the GWC API.
    """

    def __init__(self, base_url: str = None, user: str = None) -> None:
        if not base_url:
            base_url = f"{ogc_server_settings.LOCATION}gwc/rest"

        if not base_url.endswith("/"):
            base_url += "/"

        self.base_url = base_url
        self.user = user or _user
        self.headers = {"Content-Type": "text/xml"}

    def truncate_layer(self, layer_name: str, workspace: str | None = None) -> None:
        """
        Truncate all cached tiles for a GWC layer.
        """
        if ":" not in layer_name:
            workspace = workspace or getattr(settings, "DEFAULT_WORKSPACE", "geonode")

            logger.info(
                "Workspace not provided for layer '%s'. Using default workspace '%s'.",
                layer_name,
                workspace,
            )

            layer_name = f"{workspace}:{layer_name}"

        url = f"{self.base_url}masstruncate"

        body = f"<truncateLayer><layerName>{escape(layer_name)}</layerName></truncateLayer>"

        response, content = http_client.post(
            url,
            data=body,
            headers=self.headers,
            user=self.user,
        )

        if response.status_code != 200:
            logger.error(
                "Failed to truncate GWC layer '%s'. Status: %s, Response: %s",
                layer_name,
                response.status_code,
                content,
            )

            raise FailedRequestError(
                f"Failed to truncate layer '{layer_name}'. " f"Status: {response.status_code}, Response: {content}"
            )

        logger.info("Successfully truncated GWC cache for layer '%s'.", layer_name)

    def truncate_all(self) -> None:
        """
        Clear the entire GWC cache.
        """
        url = f"{self.base_url}masstruncate/"
        body = "<truncateAll></truncateAll>"

        req, content = http_client.post(url, data=body, headers=self.headers, user=self.user)

        if req.status_code != 200:
            raise FailedRequestError(f"Error {req.status_code} truncating all GWC layers: {content}")
