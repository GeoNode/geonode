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

from geonode.base.management.command_utils import setup_logger
from geonode.geoserver.gwc import GWCClient

from django.core.management.base import CommandError

logger = setup_logger()


def add_arguments(parser):
    parser.add_argument(
        "-l",
        "--layer",
        dest="layers",
        action="append",
        help="Name of the layer(s) to truncate. Can be repeated.",
    )

    parser.add_argument(
        "--all",
        dest="truncate_all",
        action="store_true",
        help="Truncate all caches in GWC",
    )


def handle(options: dict) -> None:
    dry_run = options.get('dry-run', False)
    debug = options.get('debug', False)
    setup_logger(level=logging.DEBUG if debug else logging.INFO)

    layers = options.get("layers", [])
    truncate_all = options.get("truncate_all")

    if not layers and not truncate_all:
        raise CommandError("'truncate' command requires either the -l/--layer parameter(s) or the --all flag.")

    if layers and truncate_all:
        raise CommandError("Cannot use both -l/--layer and --all at the same time.")

    logger.info(
        "Truncate command received. layers=%s, truncate_all=%s",
        layers,
        truncate_all,
    )

    if truncate_all:
        truncate_all_layers(dryrun=dry_run, debug=debug)
    else:
        logger.info(f"Truncating {len(layers)} layer{'s' if len(layers) > 1 else ''}")
        truncate_layers(layers, dryrun=dry_run, debug=debug)


def truncate_layers(layer_names, dryrun=False, debug=False):
    """Truncates one or more specified layers in GWC."""
    logger.info(f"Truncating layers in GWC: {', '.join(layer_names)}")
    client = GWCClient(debug=debug)
    failed_layers = []
    for layer_name in layer_names:
        try:
            logger.info(f"Truncating layer: {layer_name}")
            if not dryrun:
                client.truncate_layer(layer_name)
        except Exception as e:
            logger.error(f"Error invalidating cache for layer {layer_name}: {e}")
            failed_layers.append(layer_name)
    if failed_layers:
        raise CommandError(f"Failed to truncate the following layers: {', '.join(failed_layers)}")


def truncate_all_layers(dryrun=False, debug=False):
    """Truncates all layers in GWC."""
    logger.info("Truncating ALL layers in GWC")
    client = GWCClient(debug=debug)
    try:
        if not dryrun:
            client.truncate_all()
        logger.info("Successfully truncated all layers in GWC.")
    except Exception as e:
        logger.error(f"Error executing truncateAll on GeoWebCache: {e}")
        raise CommandError(f"Error executing truncateAll on GeoWebCache: {e}")
