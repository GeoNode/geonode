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

from django.core.management.base import BaseCommand
from django.core.files.storage import FileSystemStorage

storage = FileSystemStorage()
allowed_extensions = ('.tif', '.tiff', '.geotif', '.geotiff')
gs_data_dir = {_s.split("=")[0]:_s.split("=")[1] for _s in os.environ.get("GEOSERVER_JAVA_OPTS").split(" ") if '=' in _s}.get('-DGEOSERVER_DATA_DIR', os.environ.get("GEOSERVER_DATA_DIR", '/geoserver_data/data'))


class Command(BaseCommand):

    help = 'Performs a scan of all the raster Layers and does a merge and clean of the GeoServer Store with the GeoNode Uploaded one.'

    def handle(self, **options):
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
                                if os.path.exists(geoserver_layer_path):
                                    # The GeoServer Importer file exists, so let's make a copy to the GeoNode "upload" folder and "lock" it
                                    print(f"[{_cnt}] {geonode_layer_path} != {geoserver_layer_path}*")
                                    chmod_tree(os.path.dirname(geonode_layer_path))
                                    os.makedirs(os.path.dirname(geonode_layer_path), exist_ok=True)
                                    _geoserver_locking_file = os.path.join(os.path.dirname(geonode_layer_path), '.locking')
                                    if not os.path.exists(_geoserver_locking_file):
                                        open(_geoserver_locking_file, 'w').close()
                                    shutil.copy(geoserver_layer_path, geonode_layer_path)
                                elif storage.exists(str(_lyr_f.file)):
                                    # The GeoServer Importer file does not exist, so let's restore it from the GeoNode "upload" folder and "lock" it
                                    print(f"[{_cnt}] {geonode_layer_path}* != {geoserver_layer_path}")
                                    chmod_tree(os.path.dirname(geonode_layer_path))
                                    chmod_tree(os.path.dirname(geoserver_layer_path))
                                    os.makedirs(os.path.dirname(geoserver_layer_path), exist_ok=True)
                                    _geoserver_locking_file = os.path.join(os.path.dirname(geoserver_layer_path), '.locking')
                                    if not os.path.exists(_geoserver_locking_file):
                                        open(_geoserver_locking_file, 'w').close()
                                    _geoserver_locking_file = os.path.join(os.path.dirname(geonode_layer_path), '.locking')
                                    if not os.path.exists(_geoserver_locking_file):
                                        open(_geoserver_locking_file, 'w').close()
                                    shutil.copy(geonode_layer_path, geoserver_layer_path)
                                # At this point we need to update the GeoServer store in order to point to the GeoNode "upload" folder...
                                _geoserver_layer_store.url = f"file:{geonode_layer_path}"
                                gs_catalog.save(_geoserver_layer_store)
                                # Removing old GeoServer Importer directory
                                shutil.rmtree(os.path.dirname(geoserver_layer_path), ignore_errors=True)
                                _cnt += 1
        # Let's reload the GeoServer catalog in order to refresh the readers
        gs_catalog.reload()
