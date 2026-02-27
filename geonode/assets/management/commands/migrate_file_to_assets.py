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

        # copied from LocalAssetHandler and fixed
        def is_file_managed(loc) -> bool:
            return loc.startswith(os.path.join(os.path.normpath(settings.ASSETS_ROOT), ""))

        # copied from LocalAssetHandler
        def are_files_managed(asset: LocalAsset) -> bool:
            """
            :param asset: asset pointing to the files to be checked
            :return: True if all files are managed, False is no file is managed
            :raise: ValueError if both managed and unmanaged files are in the list
            """
            managed = unmanaged = None
            for file in asset.location:
                if is_file_managed(file):
                    managed = True
                else:
                    unmanaged = True
                if managed and unmanaged:
                    logger.error(f"Both managed and unmanaged files are present on Asset {asset.pk}: {asset.location}")
                    raise ValueError("Both managed and unmanaged files are present")

            return bool(managed)

        dorun = not options.get('dryrun')

        if dorun and not options.get('noinput'):
            question = "By running this command you are going to move all the files of your Resources into the ASSETS_ROOT. Do you want to continue?"
            if not confirm(question, resp=True):
                return

        logger.info("Retrieving LocalAssets...")
        tot = LocalAsset.objects.count()
        cnt = 0

        for asset in LocalAsset.objects.iterator():
            cnt += 1

            logger.info(f'#### {cnt}/{tot} - Processing asset {asset.id}: "{asset.title}"')
            for loc in asset.location:
                logger.info(f"  - File: {loc}")

            try:
                if are_files_managed(asset):
                    logger.info("Asset is already managed, skipping...")
                    continue
            except ValueError as e:
                logger.error("Some files are in the assets dir, other are not. You may need to fix this by hand.")
                logger.exception(e)
                continue

            source = os.path.dirname(asset.location[0])
            if not os.path.exists(source):
                logger.error("Source path of the file for Asset does not exists, skipping...")
                continue

            try:
                handler = LocalAssetHandler()
                dest_dir = handler._create_asset_dir()
                dest = None

                logger.info(f"Moving data to the asset folder {dest_dir}")
                if len(asset.location) == 1:
                    # In older installations, all documents are stored in a single folder, e.g.
                    #    oldpath = {MEDIA_ROOT}/documents/document/file.extension
                    # Instead of moving the entire folder, we can simply move the individual document.
                    # This approach prevents the risk of breaking the other documents
                    # that are stored in the same folder

                    logger.info(f"Moving dir: {asset.location[0]} -> {dest_dir}")
                    if dorun:
                        dest = shutil.move(asset.location[0], dest_dir)
                    else:
                        # values only used in dryrun mode for logging
                        dest = f"[DRYRUN] {os.path.join(dest_dir, os.path.basename(asset.location[0]))}"
                    asset.location = [dest]
                else:
                    logger.info(f"Moving file {source} -> {dest_dir}")
                    if dorun:
                        dest = shutil.move(source, dest_dir)
                    else:
                        # values only used in dryrun mode for logging
                        dest = f"[DRYRUN] {os.path.join(dest_dir, os.path.basename(source))}"
                    asset.location = [x.replace(source, dest) for x in asset.location]

                logger.info(f"New location path: {dest}")
                logger.info("New asset.location:")
                for loc in asset.location:
                    logger.info(f"  - {loc}")

                if settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS is not None:
                    logger.info(f"Setting folder perms to {settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS}")
                    if dorun:
                        os.chmod(os.path.dirname(dest), settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS)

                if settings.FILE_UPLOAD_PERMISSIONS is not None:
                    logger.info(f"Setting file perms to {settings.FILE_UPLOAD_PERMISSIONS}")
                    if dorun:
                        os.chmod(dest, settings.FILE_UPLOAD_PERMISSIONS)

            except Exception as e:
                logger.error(e)
                continue

            if dorun:
                logger.info("Updating asset.location in database")
                asset.save()

            logger.info("Checking if geoserver should be updated")
            asset_obj = asset.link_set.values_list('resource', flat=True).first()
            if not asset_obj:
                logger.warning("No resources connected to the asset, skipping resource update...")
                continue
            resource = ResourceBase.objects.get(pk=asset_obj)
            logger.info(f'Related resource id: {resource.id} type: {resource.resource_type}/{resource.subtype} "{resource.title}"')

            if resource.subtype == 'raster':
                logger.info(f"Checking GeoServer layer {resource.get_real_instance().alternate}")

                # look for store
                gs_layer = gs_catalog.get_layer(resource.get_real_instance().alternate)
                if not gs_layer:
                    logger.info(f"Layer not found in GeoServer: {resource.get_real_instance().alternate}")
                    continue
                if not gs_layer.resource:
                    logger.info(f"Resource not attached to layer in GeoServer: {resource.get_real_instance().alternate}")
                    continue
                if not gs_layer.resource.store:
                    logger.info(f"Store not attached to resource in GeoServer: {resource.get_real_instance().alternate}")
                    continue
                store_to_update = gs_layer.resource.store

                # look for the file to set in geoserver
                new_url = None
                for loc in asset.location:
                    if not new_url and os.path.splitext(loc)[1] in [".tiff", ".tif", ".geotiff", ".geotif"]:
                        logger.info(f"  -> Using file  : {loc}")
                        new_url = loc
                    else:
                        logger.info(f"  - Skipping file: {loc}")

                # update store in geoserver
                if new_url:
                    store_to_update.url = f"file:{new_url}"
                    try:
                        logger.info(f"Updating GeoServer store {store_to_update.name}")
                        if dorun:
                            gs_catalog.save(store_to_update)
                    except Exception:
                        logger.error(f"Error during GeoServer update for resource {resource}, please check GeoServer logs")
                    logger.info("Geoserver Updated")
                else:
                    logger.warning(f"No valid file found to set in GeoServer in {asset.location}")

        logger.info(f"Migration completed{'' if dorun else ' -- DRYRUN'}")
