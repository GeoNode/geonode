# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2025 OSGeo
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
from geonode.indexing.manager import index_manager
from geonode.metadata.manager import metadata_manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-create tsvector indexes"

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--uuid',
            dest="uuid",
            action='append',
            help="Only process resources with given UUIDs")

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
        parser.add_argument(
            '--debug',
            dest="debug",
            action='store_true',
            help="Set log level to debug")

    def handle(self, **options):
        requested_uuids = options.get('uuid')
        dry_run = options.get('dry-run')

        if options.get("setup_logger"):
            level = logging.DEBUG if options.get('debug') else logging.INFO
            logger = command_utils.setup_logger(level=level)
            import geonode.indexing.manager as m
            command_utils.setup_logger(m.__name__, level=level)

        logger.info(f"==== Running command {__name__}")
        logger.info(f"{self.help}")
        logger.info("")

        logger.debug(f"DRY-RUN is {dry_run}")
        logger.debug(f"UUIDS is {requested_uuids}")

        try:

            qs_resources = ResourceBase.objects
            tot = qs_resources.count()
            logger.info(f"Total resources in GeoNode: {tot}")
            i = 0
            cnt_ok = 0
            cnt_bad = 0
            cnt_skip = 0

            resource: ResourceBase
            for resource in qs_resources.all():
                i += 1
                logger.info(f"- {i}/{tot} Processing resource {resource.id} [{resource.uuid}] '{resource.title}'")

                if requested_uuids and resource.uuid not in requested_uuids:
                    logger.info("  - Resource filtered out by uuid")
                    cnt_skip += 1
                    continue

                try:
                    good = None
                    try:
                        jsonschema = metadata_manager.get_schema()
                        jsoninstance = metadata_manager.build_schema_instance(resource)
                        if not dry_run:
                            index_manager.update_index(resource.id, jsonschema, jsoninstance)
                        good = True

                    except Exception as e:
                        logger.error(f"Error processing '{resource.uuid}:{resource.title}': {e}", exc_info=e)

                    if dry_run or good:
                        logger.info(f"  - Done {resource.title}")
                        cnt_ok += 1
                    else:
                        logger.warning(f"Index couldn't be regenerated for instance {resource.uuid}:{resource.title}")
                        cnt_bad += 1

                except Exception as e:
                    raise e
        except Exception as e:
            raise e

        logger.info("Work completed" + (" [DRYRUN]" if dry_run else ""))
        logger.info(f"- Index regenerated : {cnt_ok}")
        logger.info(f"- Errors            : {cnt_bad}")
        logger.info(f"- Resources skipped : {cnt_skip}")
