# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2023 OSGeo
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

from django.conf import settings
from django.core.management.base import BaseCommand

from geonode.base.management import command_utils
from geonode.base.models import ResourceBase
from geonode.catalogue.models import catalogue_post_save
from geonode.layers.models import Dataset


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-create XML metadata documents"

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--layer',
            dest="layers",
            action='append',
            help="Only process layers with specified name")

        parser.add_argument(
            '-i',
            '--id',
            dest="ids",
            type=int,
            action='append',
            help="Only process resources with specified id")

        parser.add_argument(
            "--skip-logger-setup",
            action="store_false",
            dest="setup_logger",
            help='Skips setup of the "geonode.br" logger, "br" handler and "br" format if not present in settings',
        )
        parser.add_argument(
            '-d',
            '--dry-run',
            dest="dry-run",
            action='store_true',
            help="Do not actually perform any change")

    def handle(self, **options):
        requested_layers = options.get('layers')
        requested_ids = options.get('ids')
        dry_run = options.get('dry-run')

        if options.get("setup_logger"):
            logger = command_utils.setup_logger()

        logger.info(f"==== Running command {__name__}")
        logger.info(f"{self.help}")
        logger.info("")

        logger.debug(f"DRY-RUN is {dry_run}")
        logger.debug(f"LAYERS is {requested_layers}")
        logger.debug(f"IDS is {requested_ids}")

        uuid_handler_class = None
        if hasattr(settings, "LAYER_UUID_HANDLER") and settings.LAYER_UUID_HANDLER:
            from geonode.layers.utils import get_uuid_handler
            uuid_handler_class = get_uuid_handler()

        try:
            resources = Dataset.objects.all().order_by("id")
            tot = resources.count()
            logger.info(f"Total layers in GeoNode: {tot}")
            i = 0
            cnt_ok = 0
            cnt_bad = 0
            cnt_skip = 0

            instance: ResourceBase
            for instance in resources:
                i += 1
                logger.info(f"- {i}/{tot} Processing resource {instance.id} [{instance.typename}] '{instance.title}'")

                include_by_rl = requested_layers and instance.typename in requested_layers
                include_by_id = requested_ids and instance.id in requested_ids
                accepted = (not requested_layers and not requested_ids) or include_by_id or include_by_rl

                if not accepted:
                    logger.info("  - Resource filtered out by args")
                    cnt_skip += 1
                    continue

                if instance.metadata_uploaded and instance.metadata_uploaded_preserve:
                    logger.info("  - Resource filtered out since it uses custom XML")
                    cnt_skip += 1
                    continue

                good = None
                if not dry_run:
                    try:
                        # regenerate UUID
                        if uuid_handler_class:
                            _uuid = uuid_handler_class(instance).create_uuid()
                            if _uuid != instance.uuid:
                                logger.info(f"Replacing UUID: {instance.uuid} --> {_uuid}")
                                instance.uuid = _uuid
                                ResourceBase.objects.filter(id=instance.id).update(uuid=_uuid)

                        # regenerate XML
                        catalogue_post_save(instance, None)
                        good = True
                    except Exception as e:
                        logger.exception(f"Error processing '{instance.title}': {e}", e)

                if dry_run or good:
                    logger.info(f"  - Done {instance.name}")
                    cnt_ok += 1
                else:
                    logger.warning(f"Metadata couldn't be regenerated for instance '{instance.title}' ")
                    cnt_bad += 1

        except Exception as e:
            raise e

        logger.info("Work completed" + (" [DRYRUN]" if dry_run else ""))
        logger.info(f"- Metadata regenerated : {cnt_ok}")
        logger.info(f"- Metadata in error    : {cnt_bad}")
        logger.info(f"- Resources skipped    : {cnt_skip}")
