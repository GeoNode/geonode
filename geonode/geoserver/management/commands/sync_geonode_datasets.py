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
import sys
import json
import logging

from django.core.management.base import BaseCommand

from geonode.base.management.command_utils import setup_logger
from geonode.layers.models import Dataset
from geonode.security.views import _perms_info_json
from geonode.base.utils import remove_duplicate_links
from geonode.geoserver.helpers import create_gs_thumbnail, sync_instance_with_geoserver, set_attributes_from_geoserver

logger = logging.getLogger(__name__)


def sync_geonode_datasets(
    ignore_errors,
    filter,
    username,
    removeduplicates,
    updatepermissions,
    updatethumbnails,
    updateattributes,
    updatebbox,
    updatemetadata,
):
    layers = Dataset.objects.all().order_by("name")
    if filter:
        layers = layers.filter(name__icontains=filter)
    if username:
        layers = layers.filter(owner__username=username)
    layers_count = layers.count()
    count = 0
    dataset_errors = []

    if not layers:
        logger.warning(f"No layers selected by filter '{filter}'")
        return

    for layer in layers:
        try:
            count += 1
            logger.info(f"=== Syncing layer {count}/{layers_count}: {layer.name}")
            if updatepermissions:
                logger.info("Syncing permissions...")
                # sync permissions in GeoFence
                perm_spec = json.loads(_perms_info_json(layer))
                # re-sync GeoFence security rules
                layer.set_permissions(perm_spec)
            if updateattributes:
                # recalculate the layer statistics
                logger.info("Setting attributes...")
                set_attributes_from_geoserver(layer, overwrite=True)
            if updatethumbnails:
                logger.info("Regenerating thumbnails...")
                create_gs_thumbnail(layer, overwrite=True, check_bbox=False)
            if updatebbox:
                logger.info("Regenerating BBOX...")
                sync_instance_with_geoserver(layer.id, updatemetadata=False, updatebbox=True)
            if updatemetadata:
                logger.info("Updating metadata...")
                sync_instance_with_geoserver(layer.id, updatemetadata=True, updatebbox=False)
            if removeduplicates:
                # remove duplicates
                logger.info("Removing duplicate links...")
                remove_duplicate_links(layer)
        except (Exception, RuntimeError):
            dataset_errors.append(layer.alternate)
            exception_type, error, traceback = sys.exc_info()
            logger.info(exception_type, error, traceback)
            if ignore_errors:
                pass
            else:
                logger.error(
                    "Stopping process because --ignore-errors was not set and an error was found.", stack_info=True
                )
                return
    logger.info(f"There are {len(dataset_errors)} layers which could not be updated because of errors")
    for dataset_error in dataset_errors:
        logger.info(dataset_error)


class Command(BaseCommand):
    help = "Update the GeoNode layers: permissions (including GeoFence database), statistics, thumbnails"

    def add_arguments(self, parser):
        parser.add_argument(
            "-i",
            "--ignore-errors",
            action="store_true",
            dest="ignore_errors",
            default=False,
            help="Stop after any errors are encountered.",
        )
        parser.add_argument(
            "-d",
            "--remove-duplicates",
            action="store_true",
            dest="removeduplicates",
            default=False,
            help="Remove duplicates first.",
        )
        parser.add_argument(
            "-f",
            "--filter",
            dest="filter",
            default=None,
            help="Only update data the layers that match the given filter.",
        ),
        parser.add_argument(
            "-u", "--username", dest="username", default=None, help="Only update data owned by the specified username."
        )
        parser.add_argument(
            "--updatepermissions",
            action="store_true",
            dest="updatepermissions",
            default=False,
            help="Update the layer permissions.",
        )
        parser.add_argument(
            "--updatethumbnails",
            action="store_true",
            dest="updatethumbnails",
            default=False,
            help="Update the layer styles and thumbnails.",
        )
        parser.add_argument(
            "--updateattributes",
            action="store_true",
            dest="updateattributes",
            default=False,
            help="Update the layer attributes.",
        )
        parser.add_argument(
            "--updatebbox", action="store_true", dest="updatebbox", default=False, help="Update the layer BBOX."
        )
        parser.add_argument(
            "--updatemetadata",
            action="store_true",
            dest="updatemetadata",
            default=False,
            help="Update the Geoserver layer metadata.",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            dest="log_debug",
            default=False,
            help="Enable debug logging.",
        )

    def handle(self, **options):
        log_level = logging.DEBUG if options.get("log_debug") else logging.INFO
        setup_logger(__name__, level=log_level)
        import geonode.geoserver.helpers as helpers

        setup_logger(helpers.__name__, level=log_level)

        ignore_errors = options.get("ignore_errors")
        removeduplicates = options.get("removeduplicates")
        updatepermissions = options.get("updatepermissions")
        updatethumbnails = options.get("updatethumbnails")
        updateattributes = options.get("updateattributes")
        updatebbox = options.get("updatebbox")
        updatemetadata = options.get("updatemetadata")
        filter = options.get("filter")
        if not options.get("username"):
            username = None
        else:
            username = options.get("username")
        sync_geonode_datasets(
            ignore_errors,
            filter,
            username,
            removeduplicates,
            updatepermissions,
            updatethumbnails,
            updateattributes,
            updatebbox,
            updatemetadata,
        )
