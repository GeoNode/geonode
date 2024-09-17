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

"""
main settings to handle the celery rate
"""
IMPORTER_GLOBAL_RATE_LIMIT = os.getenv("IMPORTER_GLOBAL_RATE_LIMIT", 5)
IMPORTER_PUBLISHING_RATE_LIMIT = os.getenv("IMPORTER_PUBLISHING_RATE_LIMIT", 5)
IMPORTER_RESOURCE_CREATION_RATE_LIMIT = os.getenv("IMPORTER_RESOURCE_CREATION_RATE_LIMIT", 10)
IMPORTER_RESOURCE_COPY_RATE_LIMIT = os.getenv("IMPORTER_RESOURCE_COPY_RATE_LIMIT", 10)

SYSTEM_HANDLERS = [
    "geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
    "geonode.upload.handlers.geojson.handler.GeoJsonFileHandler",
    "geonode.upload.handlers.shapefile.handler.ShapeFileHandler",
    "geonode.upload.handlers.kml.handler.KMLFileHandler",
    "geonode.upload.handlers.csv.handler.CSVFileHandler",
    "geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler",
    "geonode.upload.handlers.xml.handler.XMLFileHandler",
    "geonode.upload.handlers.sld.handler.SLDFileHandler",
    "geonode.upload.handlers.tiles3d.handler.Tiles3DFileHandler",
    "geonode.upload.handlers.remote.tiles3d.RemoteTiles3DResourceHandler",
    "geonode.upload.handlers.remote.wms.RemoteWMSResourceHandler",
]
