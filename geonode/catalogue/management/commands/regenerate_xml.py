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

from django.core.management.base import BaseCommand

from geonode.base.management import command_utils
from geonode.base.models import ResourceBase
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
            help="Only process specified layers ")

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
        dry_run = options.get('dry-run')

        if options.get("setup_logger"):
            logger = command_utils.setup_logger()

        logger.info(f"==== Running command {__name__}")
        logger.info(f"{self.help}")
        logger.info("")

        logger.debug(f"DRY-RUN is {dry_run}")
        logger.debug(f"LAYERS is {requested_layers}")

        try:

            layers = Dataset.objects.all()
            tot = len(layers)
            logger.info(f"Total layers in GeoNode: {tot}")
            i = 0
            cnt_ok = 0
            cnt_bad = 0
            cnt_skip = 0

            instance: ResourceBase
            for instance in layers:
                i += 1
                logger.info(f"- {i}/{tot} Processing layer {instance.id} [{instance.typename}] '{instance.title}'")

                if requested_layers and instance.typename not in requested_layers:
                    logger.info("  - Layer filtered out by args")
                    cnt_skip += 1
                    continue

                if instance.metadata_uploaded and instance.metadata_uploaded_preserve:
                    logger.info("  - Layer filtered out since it uses custom XML")
                    cnt_skip += 1
                    continue

                try:
                    good = None
                    if not dry_run:
                        try:
                            try:
                                # the save() method triggers the metadata regeneration
                                instance.save()
                                good = True
                            except Exception as e:
                                logger.error(f"Error saving instance '{instance.title}': {e}")
                                raise e

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
        except Exception as e:
            raise e

        logger.info("Work completed" + (" [DRYRUN]" if dry_run else ""))
        logger.info(f"- Metadata regenerated : {cnt_ok}")
        logger.info(f"- Metadata in error    : {cnt_bad}")
        logger.info(f"- Resources skipped    : {cnt_skip}")
