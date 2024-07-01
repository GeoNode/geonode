#########################################################################
#
# Copyright (C) 2024 OSGeo
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

import os
import sys
import shutil
import logging
from django.conf import settings
from geonode.assets.local import LocalAssetHandler
from geonode.assets.models import LocalAsset
from geonode.base.management.commands.helpers import confirm
from django.core.management.base import BaseCommand
from geonode.geoserver.helpers import gs_catalog

from geonode.base.models import ResourceBase

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Command(BaseCommand):

    help = """
        Migrate the files from MEDIA_ROOT to ASSETS_ROOT, update LocalAsset.location and GeoServer
        REF: https://github.com/GeoNode/geonode/issues/12326
        """

    def add_arguments(self, parser):
        parser.add_argument(
            '-n',
            '--no-input',
            dest='noinput',
            default=False,
            action='store_true',
            help='Does not ask for confirmation for the run'
        )
        parser.add_argument(
            '-d',
            '--dryrun',
            dest='dryrun',
            default=False,
            action='store_true',
            help='Perform a dryrun, will show the File to be moved, their new path and the file to be deleted'
        )

    def handle(self, **options):
        question = "By running this command you are going to move all the files of your Resources into the ASSETS_ROOT. Do you want to continue?"

        if not options.get('noinput'):
            result = confirm(question, resp=True)
            if not result:
                return

        dryrun = options.get('dryrun')

        handler = LocalAssetHandler()

        logger.info("Retrieving all assets with some files")

        for asset in LocalAsset.objects.iterator():
            logger.info(f"processing asset: {asset.title}")

            source = os.path.dirname(asset.location[0])

            if dryrun:
                logger.info(f"Files found: {asset.location}")
                continue

            if settings.ASSETS_ROOT in source:
                logger.info("The location is already the asset root, skipping...")
                continue

            if not os.path.exists(source):
                logger.warning("Source path of the file for Asset does not exists, skipping...")
                continue

            try:

                logger.info("Moving file to the asset folder")

                dest = shutil.move(source, handler._create_asset_dir())

                logger.info("Fixing perms")
                if settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS is not None:
                    os.chmod(os.path.dirname(dest), settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS)

                if settings.FILE_UPLOAD_PERMISSIONS is not None:
                    os.chmod(dest, settings.FILE_UPLOAD_PERMISSIONS)

            except Exception as e:
                logger.error(e)
                continue

            logger.info("Updating location field with new folder value")

            asset.location = [x.replace(source, dest) for x in asset.location]
            asset.save()

            logger.info("Checking if geoserver should be updated")
            asset_obj = asset.link_set.values_list('resource', flat=True).first()
            if not asset_obj:
                logger.warning("No resources connected to the asset, skipping resource update...")
                continue
            resource = ResourceBase.objects.get(pk=asset_obj)
            if resource.subtype == 'raster':
                logger.info("Updating GeoServer value")

                store_to_update = gs_catalog.get_layer(resource.get_real_instance().alternate)\
                    .resource\
                    .store

                raster_file = [x for x in asset.location if os.path.basename(x).split('.')[-1] in ["tiff", "tif", "geotiff", "geotif"]]
                store_to_update.url = f"file:{raster_file[0]}"
                try:
                    gs_catalog.save(store_to_update)
                except Exception:
                    logger.error(f"Error during GeoServer update for resource {resource}, please check GeoServer logs")
                logger.info("Geoserver Updated")

        logger.info("Migration completed")
