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
from geonode.geoserver.gwc import GWCClient

logger = setup_logger()


def truncate_layers(layer_names):
    """Truncates one or more specified layers in GWC."""
    logger.info(f"Truncating layers in GWC: {', '.join(layer_names)}")
    client = GWCClient()
    for layer_name in layer_names:
        try:
            logger.info(f"Truncating layer: {layer_name}")
            client.truncate_layer(layer_name)
        except Exception as e:
            logger.error(f"Error invalidating cache for layer {layer_name}: {e}")


def truncate_all_layers():
    """Truncates all layers in GWC."""
    logger.info("Truncating ALL layers in GWC")
    client = GWCClient()
    try:
        client.truncate_all()
        logger.info("Successfully truncated all layers in GWC.")
    except Exception as e:
        logger.error(f"Error executing truncateAll on GeoWebCache: {e}")
