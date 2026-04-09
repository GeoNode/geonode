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

import sys
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from geonode.upload.orchestrator import orchestrator
from geonode.layers.models import Dataset
from geonode.upload.models import ResourceHandlerInfo

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Command(BaseCommand):
    help = ("Generate the missing ResourceHandlerInfo for all the layers")

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--dryrun',
            dest='dryrun',
            default=False,
            action='store_true',
            help='Perform a dryrun, will show the File to be moved, their new path and the file to be deleted'
        )

    def handle(self, *args, **options):
        start = datetime.now()
        dorun = not options.get('dryrun')

        if not dorun:
            logging.info("Dry RUN requested, not action will be performed")

        handler_to_use = None

        for resource in Dataset.objects.exclude(
            pk__in=ResourceHandlerInfo.objects.values_list("resource_id", flat=True)
        ).exclude(subtype__in=["remote", None]).iterator():

            logger.info(f"Evaluating dataset: {resource}")

            match resource.subtype:
                case 'vector':
                    # taking a default handler for all the vector file
                    handler_to_use = orchestrator.load_handler_by_id("shp")
                case 'raster':
                    # taking a default handler for all the raster file
                    handler_to_use = orchestrator.load_handler_by_id("tiff")
                case '3dtiles':
                    handler_to_use = orchestrator.load_handler_by_id("3dtiles")
                case 'tabular':
                    handler_to_use = orchestrator.load_handler_by_id("csv")
                case 'flatgeobuf':
                    handler_to_use = orchestrator.load_handler("geonode.upload.handlers.remote.flatgeobuf.RemoteFlatGeobufResourceHandler")
                case 'cog':
                    handler_to_use = orchestrator.load_handler("geonode.upload.handlers.remote.cog.RemoteCOGResourceHandler")
                case _:
                    handler_to_use = None

            if handler_to_use and dorun:
                logger.info(f"handler found: {handler_to_use} for resource {resource}")
                try:
                    handler_to_use().create_resourcehandlerinfo(
                        handler_module_path=str(handler_to_use()),
                        resource=resource,
                        execution_id=None,
                        kwargs={"is_legacy": True},
                    )
                    logger.info("creation completed")
                except Exception as e:
                    logger.exception(e)
                    logger.error(f"The following dataset {resource} raised an error during the generation of the resourcehandlerinfo")

        logger.info(f"Total time: {(datetime.now() - start).seconds} seconds")
