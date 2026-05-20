#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from geonode.base.management.command_utils import setup_logger
from geonode.geoserver.helpers import _invalidate_geowebcache_dataset, ogc_server_settings, _user, http_client

logger = setup_logger()


def truncate_layers(layer_names):
    """Truncates one or more specified layers in GWC."""
    logger.info(f"Truncating layers in GWC: {', '.join(layer_names)}")
    for layer_name in layer_names:
        try:
            logger.info(f"Truncating layer: {layer_name}")
            _invalidate_geowebcache_dataset(layer_name)
        except Exception as e:
            logger.error(f"Error invalidating cache for layer {layer_name}: {e}")


def truncate_all_layers():
    """Truncates all layers in GWC."""
    logger.info("Truncating ALL layers in GWC")
    headers = {
        "Content-Type": "text/xml",
    }
    body = "<truncateAll></truncateAll>"
    url = f"{ogc_server_settings.LOCATION}gwc/rest/masstruncate"

    try:
        req, content = http_client.post(url, data=body, headers=headers, user=_user)
        if req.status_code != 200:
            logger.error(f"Error {req.status_code} invalidating GeoWebCache at {url}: {content}")
        else:
            logger.info("Successfully truncated all layers in GWC.")
    except Exception as e:
        logger.error(f"Error executing truncateAll on GeoWebCache: {e}")
