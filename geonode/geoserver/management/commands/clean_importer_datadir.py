# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import re
import shutil
from geonode.utils import chmod_tree
from geonode.geoserver.helpers import gs_catalog
from geonode.layers.models import Layer, LayerFile
from geonode.br.management.commands.utils.utils import confirm

from django.core.management.base import BaseCommand
from django.core.files.storage import FileSystemStorage

_remove_message = "Remove the path"
storage = FileSystemStorage()
allowed_extensions = ('.tif', '.tiff', '.geotif', '.geotiff')
gs_data_dir = {_s.split("=")[0]: _s.split("=")[1] for _s in os.environ.get("GEOSERVER_JAVA_OPTS").split(
    " ") if '=' in _s}.get('-DGEOSERVER_DATA_DIR', os.environ.get("GEOSERVER_DATA_DIR", '/geoserver_data/data'))


class Command(BaseCommand):

    help = 'Performs a scan of all the raster Layers and does a merge and clean of the GeoServer Store with the GeoNode Uploaded one.'

    def add_arguments(self, parser):

        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the execution without asking for confirmation.')

    def handle(self, **options):
        __force_exec = options.get('force_exec')
        _cnt = 1
        for _lyr in Layer.objects.filter(storeType="coverageStore"):
            # Scan all the "raster" layers on GeoNode
            upload_session = _lyr.get_upload_session()
            if upload_session:
                # The ones with an "upload_session" are the ones with the "Original Layers" link too
                layer_files = [item for idx, item in enumerate(LayerFile.objects.filter(upload_session=upload_session))]
                if layer_files:
                    for _lyr_f in layer_files:
                        geonode_layer_path = storage.path(str(_lyr_f.file))

                        # We are looking for the source files only; we don't care about the auxiliary ones
                        if os.path.splitext(geonode_layer_path)[1].lower() in allowed_extensions:

                            # Let's get the "store" path from GeoServer
                            _geoserver_layer_store = gs_catalog.get_layer(_lyr.alternate).resource.store
                            _file_url = _geoserver_layer_store.url

                            # Let's convert the "file:..." url to an absolute path on the server
                            geoserver_layer_path = os.path.join(gs_data_dir, re.search(r"^(?:file:)?(.*?)$", _file_url).group(1))
                            if geonode_layer_path != geoserver_layer_path:

                                # Seems like the GeoNode and GeoServer paths do not match...
                                print(f"[{_cnt}] {geonode_layer_path} != {geoserver_layer_path}*")
                                if __force_exec or confirm(prompt="Do you want to proceed?", resp=False):
                                    # Let's make sure we can "rw" on the GeoServer paths
                                    chmod_tree(os.path.dirname(geonode_layer_path))

                                    # Create the destination GeoNode Uploaded folder structure
                                    os.makedirs(os.path.dirname(geonode_layer_path), exist_ok=True)

                                    # Create the GeoServer Importer .locking file
                                    _geoserver_locking_file = os.path.join(os.path.dirname(geonode_layer_path), '.locking')
                                    if not os.path.exists(_geoserver_locking_file):
                                        open(_geoserver_locking_file, 'w').close()

                                    # Remove any already existing file on GeoNode Upload folder
                                    geonode_dst_layer_path = os.path.join(os.path.dirname(geonode_layer_path), shutil._basename(geoserver_layer_path))

                                    # Move the Importer file to the GeoNode Uploaded folder
                                    if os.path.exists(geoserver_layer_path):

                                        # Removing old GeoNode Uploaded files
                                        if os.path.exists(geonode_layer_path):
                                            if __force_exec or confirm(prompt=f"{_remove_message}: {geonode_layer_path}", resp=False):
                                                os.remove(geonode_layer_path)

                                        # Move the Importer file to the GeoNode Uploaded folder
                                        if os.path.exists(geonode_dst_layer_path):
                                            if __force_exec or confirm(prompt=f"{_remove_message}: {geonode_dst_layer_path}", resp=False):
                                                os.remove(geonode_dst_layer_path)
                                        shutil.move(geoserver_layer_path, geonode_dst_layer_path)

                                    elif storage.exists(str(_lyr_f.file)):

                                        # Move the GeoNode Uploaded folder to the new Importer destination
                                        if os.path.exists(geonode_dst_layer_path):
                                            if __force_exec or confirm(prompt=f"{_remove_message}: {geonode_dst_layer_path}", resp=False):
                                                os.remove(geonode_dst_layer_path)
                                        shutil.move(geonode_layer_path, geonode_dst_layer_path)

                                    # Removing old GeoServer Importer directory
                                    if __force_exec or confirm(prompt=f"{_remove_message} completely*: {os.path.dirname(geoserver_layer_path)}", resp=False):
                                        shutil.rmtree(os.path.dirname(geoserver_layer_path), ignore_errors=True)

                                    # Update the GeoNode Uploade path
                                    geonode_layer_path = geonode_dst_layer_path
                                    LayerFile.objects.filter(id=_lyr_f.id).update(file=geonode_dst_layer_path)

                                    # At this point we need to update the GeoServer store in order to point to the GeoNode "upload" folder...
                                    _geoserver_layer_store.url = f"file:{geonode_layer_path}"
                                    gs_catalog.save(_geoserver_layer_store)
                                elif confirm(prompt="Do you want to stop the process here?", resp=True):
                                    _cnt = -1
                                    break
                                _cnt += 1
            if _cnt < 0:
                break
        # Let's reload the GeoServer catalog in order to refresh the readers
        gs_catalog.reload()
