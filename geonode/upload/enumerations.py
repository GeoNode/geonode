#########################################################################
#
# Copyright (C) 2026 OSGeo
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

# Extensions and magic signatures for the spatial upload pipeline used by
# ImporterViewSet (URL name "importer_upload" / permission base.add_resourcebase).
#
# The extension list is the union of the required/optional extensions declared
# by every handler in geonode.upload.settings.SYSTEM_HANDLERS
# (supported_file_extension_config) plus the ancillary side-car files the
# shapefile/vector pipelines accept (dbf, shx, prj, cpg, cst).
#
# Two complementary maps drive the validation:
# * SPATIAL_MAGIC_MIMETYPE_MAP   - extension -> set of acceptable libmagic MIME
#                                 strings (magic.from_buffer(sample, mime=True))
# * SPATIAL_MAGIC_DESCRIPTION_MAP - extension -> set of substrings that must
#                                   appear in the libmagic description
#                                   (magic.from_buffer(sample)). Used for
#                                   formats whose MIME is too generic to be
#                                   trusted on its own (e.g. Shapefile and
#                                   GeoPackage report application/octet-stream).


SPATIAL_MAGIC_MIMETYPE_MAP = {
    # GeoJSON / JSON
    "geojson": {"application/json", "text/plain", "text/json"},
    "json": {"application/json", "text/plain", "text/json"},
    # KML / KMZ
    "kml": {
        "application/xml",
        "text/xml",
        "application/vnd.google-earth.kml+xml",
        "text/plain",
    },
    "kmz": {"application/zip", "application/vnd.google-earth.kmz"},
    # CSV
    "csv": {"text/plain", "text/csv"},
    # GeoTIFF and variants
    "tiff": {"image/tiff"},
    "tif": {"image/tiff"},
    "geotiff": {"image/tiff"},
    "geotif": {"image/tiff"},
    # Excel (vector via xlsx handler)
    "xlsx": {
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    "xls": {
        "application/excel",
        "application/vnd.ms-excel",
        "application/x-ole-storage",
    },
    # 3D Tiles ship as a .zip
    "zip": {"application/zip"},
    # Sidecar / metadata formats
    "xml": {"application/xml", "text/xml"},
    "sld": {"text/plain", "application/xml", "text/xml"},
    # Shapefile side-cars that are text
    "prj": {"text/plain"},
    "cpg": {"text/plain"},
    "cst": {"text/plain"},
}


# Formats where libmagic's MIME is too generic (typically application/octet-stream)
# are identified by substrings in the description instead.
SPATIAL_MAGIC_DESCRIPTION_MAP = {
    "shp": {"ESRI Shapefile"},
    "shx": {"ESRI Shapefile"},
    "dbf": {"dBase", "FoxPro", "Xbase"},
    "gpkg": {"SQLite", "GeoPackage"},
}


SPATIAL_ALLOWED_EXTENSIONS = (
    set(SPATIAL_MAGIC_MIMETYPE_MAP.keys()) | set(SPATIAL_MAGIC_DESCRIPTION_MAP.keys())
)
