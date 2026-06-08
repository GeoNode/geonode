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

from geonode.base.management.command_utils import setup_logger
from geonode.geoserver.gwc import GWCClient

from django.core.management.base import CommandError

logger = setup_logger()


def handle(options: dict) -> None:
    layers = options.get("layers") or []
    truncate_all = options.get("truncate_all") or False

    logger.info(
        "Truncate command received. layers=%s, truncate_all=%s",
        layers,
        truncate_all,
    )

    if not layers and not truncate_all:
        raise CommandError("'truncate' command requires either the -l/--layer parameter(s) or the --all flag.")

    if layers and truncate_all:
        raise CommandError("Cannot use both -l/--layer and --all at the same time.")

    if truncate_all:
        truncate_all_layers()
    else:
        logger.info(f"Truncating {len(layers)} layer{'s' if len(layers) > 1 else ''}")
        truncate_layers(layers)


def truncate_layers(layer_names):
    """Truncates one or more specified layers in GWC."""
    logger.info(f"Truncating layers in GWC: {', '.join(layer_names)}")
    client = GWCClient()
    failed_layers = []
    for layer_name in layer_names:
        try:
            logger.info(f"Truncating layer: {layer_name}")
            client.truncate_layer(layer_name)
        except Exception as e:
            logger.error(f"Error invalidating cache for layer {layer_name}: {e}")
            failed_layers.append(layer_name)
    if failed_layers:
        raise CommandError(f"Failed to truncate the following layers: {', '.join(failed_layers)}")


def truncate_all_layers():
    """Truncates all layers in GWC."""
    logger.info("Truncating ALL layers in GWC")
    client = GWCClient()
    try:
        client.truncate_all()
        logger.info("Successfully truncated all layers in GWC.")
    except Exception as e:
        logger.error(f"Error executing truncateAll on GeoWebCache: {e}")
        raise CommandError(f"Error executing truncateAll on GeoWebCache: {e}")
