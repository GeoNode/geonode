# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

'''An incomplete replacement for the various file support functions currently
scattered over the codebase

@todo complete and use
'''

import os.path

from geonode.utils import fixup_shp_columnnames
from geoserver.resource import FeatureType, Coverage
from django.utils.translation import ugettext as _

from collections import UserList
import zipfile
import os
import re
import logging


logger = logging.getLogger(__name__)
vector = FeatureType.resource_type
raster = Coverage.resource_type


xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")


class SpatialFiles(UserList):

    def __init__(self, dirname, data, archive=None):
        self.dirname = dirname
        self.data = data
        self.archive = archive

    def all_files(self):
        if self.archive:
            return [self.archive]
        all = []
        for f in self.data:
            all.extend(f.all_files())
        return all


class SpatialFile(object):

    def __init__(self, base_file, file_type, auxillary_files,
                 sld_files, xml_files):
        self.base_file = base_file
        self.file_type = file_type
        self.auxillary_files = auxillary_files
        self.sld_files = sld_files
        self.xml_files = xml_files

    def all_files(self):
        return [self.base_file] + self.auxillary_files

    def __repr__(self):
        return (f"<SpatialFile base_file={self.base_file} file_type={self.file_type} "
                f"aux={self.auxillary_files} sld={self.sld_files} xml={self.xml_files}>")


class FileType(object):

    def __init__(self, name, code, layer_type, aliases=None,
                 auxillary_file_exts=None):
        self.name = name
        self.code = code
        self.layer_type = layer_type
        self.aliases = list(aliases) if aliases is not None else []
        self.auxillary_file_exts = list(
            auxillary_file_exts) if auxillary_file_exts is not None else []

    def matches(self, ext):
        ext = ext.lower()
        return ext == self.code or ext in self.aliases

    def build_spatial_file(self, base, others):
        aux_files, slds, xmls = self.find_auxillary_files(base, others)

        return SpatialFile(file_type=self,
                           base_file=base,
                           auxillary_files=aux_files,
                           sld_files=slds,
                           xml_files=xmls)

    def find_auxillary_files(self, base, others):
        base_name = os.path.splitext(base)[0]
        base_matches = [
            f for f in others if os.path.splitext(f)[0] == base_name]
        slds = _find_file_type(base_matches, extension='.sld')
        aux_files = [f for f in others if os.path.splitext(f)[1][1:].lower()
                     in self.auxillary_file_exts]
        xmls = _find_file_type(base_matches, extension='.xml')
        return aux_files, slds, xmls

    def __repr__(self):
        return f"<FileType {self.code}>"


TYPE_UNKNOWN = FileType("unknown", None, None)

_keep_original_data = ('kmz', 'zip-mosaic')
_tif_extensions = ("tif", "tiff", "geotif", "geotiff")
_mosaics_extensions = ("properties", "shp", "aux")

types = [
    FileType("Shapefile", "shp", vector,
             auxillary_file_exts=('dbf', 'shx', 'prj',)),
    FileType("GeoTIFF", _tif_extensions[0], raster,
             aliases=_tif_extensions[1:]),
    FileType(
        "ImageMosaic", "zip-mosaic", raster,
        aliases=_tif_extensions,
        auxillary_file_exts=_mosaics_extensions + _tif_extensions
    ),
    FileType("ASCII Text File", "asc", raster,
             auxillary_file_exts=('prj',)),
    # requires geoserver importer extension
    FileType("PNG", "png", raster,
             auxillary_file_exts=('prj',)),
    FileType("JPG", "jpg", raster,
             auxillary_file_exts=('prj',)),
    FileType("CSV", "csv", vector),
    FileType("GeoJSON", "geojson", vector),
    FileType("KML", "kml", vector),
    FileType(
        "KML Ground Overlay", "kml-overlay", raster,
        aliases=("kmz", "kml",),
        auxillary_file_exts=("png", "gif", "jpg",) + _tif_extensions
    ),
    # requires geoserver gdal extension
    FileType("ERDASImg", "img", raster),
    FileType("NITF", "ntf", raster,
             aliases=('nitf')),
    FileType("CIB1", "i41", raster,
             aliases=('i42', 'i43', 'i44', 'i45', 'i46', 'i47', 'i48', 'i49')),
    FileType("CIB5", "i21", raster,
             aliases=('i22', 'i23', 'i24', 'i25', 'i26', 'i27', 'i28', 'i29')),
    FileType("CIB10", "i11", raster,
             aliases=('i12', 'i13', 'i14', 'i15', 'i16', 'i17', 'i18', 'i19')),
    FileType("GNC", "gn1", raster,
             aliases=('gn2', 'gn3', 'gn4', 'gn5', 'gn6', 'gn7', 'gn8', 'gn9')),
    FileType("JNC", "jn1", raster,
             aliases=('jn2', 'jn3', 'jn4', 'jn5', 'jn6', 'jn7', 'jn8', 'jn9')),
    FileType("ONC", "on1", raster,
             aliases=('on2', 'on3', 'on4', 'on5', 'on6', 'on7', 'on8', 'on9')),
    FileType("TPC", "tp1", raster,
             aliases=('tp2', 'tp3', 'tp4', 'tp5', 'tp6', 'tp7', 'tp8', 'tp9')),
    FileType("JOG", "ja1", raster,
             aliases=('ja2', 'ja3', 'ja4', 'ja5', 'ja6', 'ja7', 'ja8', 'ja9')),
    FileType("TLM100", "tc1", raster,
             aliases=('tc2', 'tc3', 'tc4', 'tc5', 'tc6', 'tc7', 'tc8', 'tc9')),
    FileType("TLM50", "tl1", raster,
             aliases=('tl2', 'tl3', 'tl4', 'tl5', 'tl6', 'tl7', 'tl8', 'tl9')),
    # requires gdal plugin for mrsid and jp2
    FileType("MrSID", "sid", raster,
             auxillary_file_exts=('sdw',)),
    FileType("JP2", "jp2", raster)
]


def get_type(name):
    try:
        file_type = [t for t in types if t.name == name][0]
    except IndexError:
        file_type = None
    return file_type


def _contains_bad_names(file_names):
    '''return True if the list of names contains a bad one'''
    return any([xml_unsafe.search(f) for f in file_names])


def _clean_string(
        str,
        regex=r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)",
        replace="_"):
    """
    Replaces a string that matches the regex with the replacement.
    """
    regex = re.compile(regex)

    if str[0].isdigit():
        str = replace + str

    return regex.sub(replace, str)


def _rename_files(file_names):
    files = []
    for f in file_names:
        dirname, base_name = os.path.split(f)
        safe = _clean_string(base_name)
        if safe != base_name:
            safe = os.path.join(dirname, safe)
            os.rename(f, safe)
            files.append(safe)
        else:
            files.append(f)
    return files


def _find_file_type(file_names, extension):
    """
    Returns files that end with the given extension from a list of file names.
    """
    return [f for f in file_names if f.lower().endswith(extension)]


def clean_macosx_dir(file_names):
    """
    Returns the files sans anything in a __MACOSX directory
    """
    return [f for f in file_names if '__MACOSX' not in f]


def get_scan_hint(valid_extensions):
    """Provide hint on the type of file being handled in the upload session.

    This function is useful mainly for those file types that can carry
    either vector or raster formats, like the KML type.
    """
    if "kml" in valid_extensions:
        if len(valid_extensions) == 2 and valid_extensions[1] == 'sld':
            result = "kml"
        else:
            result = "kml-overlay"
    elif "kmz" in valid_extensions:
        result = "kmz"
    elif "zip-mosaic" in valid_extensions:
        result = "zip-mosaic"
    else:
        result = None
    return result


def scan_file(file_name, scan_hint=None, charset=None):
    '''get a list of SpatialFiles for the provided file'''
    if not os.path.exists(file_name):
        raise Exception(_("Could not access to uploaded data."))

    dirname = os.path.dirname(file_name)
    if zipfile.is_zipfile(file_name):
        paths, kept_zip = _process_zip(
            file_name,
            dirname,
            scan_hint=scan_hint,
            charset=charset)
        archive = file_name if kept_zip else None
    else:
        paths = []
        for p in os.listdir(dirname):
            _f = os.path.join(dirname, p)
            fixup_shp_columnnames(_f, charset)
            paths.append(_f)
        archive = None
    if paths is not None:
        safe_paths = _rename_files(paths)
    else:
        safe_paths = []

    found = []
    for file_type in types:
        for path in safe_paths:
            path_extension = os.path.splitext(path)[-1][1:]
            hint_ok = (scan_hint is None or file_type.code == scan_hint or
                       scan_hint in file_type.aliases)
            if file_type.matches(path_extension) and hint_ok:
                _f = file_type.build_spatial_file(path, safe_paths)
                found_paths = [f.base_file for f in found]
                if path not in found_paths:
                    found.append(_f)

    # detect xmls and assign if a single upload is found
    xml_files = _find_file_type(safe_paths, extension='.xml')
    if xml_files:
        if len(found) == 1:
            found[0].xml_files = xml_files
        else:
            raise Exception(_("One or more XML files was provided, but no matching files were found for them."))

    # detect slds and assign if a single upload is found
    sld_files = _find_file_type(safe_paths, extension='.sld')
    if sld_files:
        if len(found) == 1:
            found[0].sld_files = sld_files
        else:
            raise Exception(_("One or more SLD files was provided, but no matching files were found for them."))
    return SpatialFiles(dirname, found, archive=archive)


def _process_zip(zip_path, destination_dir, scan_hint=None, charset=None):
    """Perform sanity checks on uploaded zip file

    This function will check if the zip file's contents have legal names.
    If they do the zipfile remains compressed. Otherwise, it is extracted and
    the files are renamed.

    It will also check if an .sld file exists inside the zip and extract it

    """
    safe_zip_path = _rename_files([zip_path])[0]
    with zipfile.ZipFile(safe_zip_path, "r", allowZip64=True) as zip_handler:
        if scan_hint in _keep_original_data:
            extracted_paths = _extract_zip(zip_handler, destination_dir, charset)
        else:
            extracted_paths = _sanitize_zip_contents(
                zip_handler, destination_dir, charset)
        if extracted_paths is not None:
            all_paths = extracted_paths
            kept_zip = False
        else:
            kept_zip = True
            all_paths = [zip_path]
            sld_paths = _probe_zip_for_sld(zip_handler, destination_dir)
            all_paths.extend(sld_paths)
    return all_paths, kept_zip


def _sanitize_zip_contents(zip_handler, destination_dir, charset):
    clean_macosx_dir(zip_handler.namelist())
    result = _extract_zip(zip_handler, destination_dir, charset)
    return result


def _extract_zip(zip_handler, destination, charset):
    file_names = zip_handler.namelist()
    zip_handler.extractall(destination)
    paths = []
    for p in file_names:
        _f = os.path.join(destination, p)
        fixup_shp_columnnames(_f, charset)
        paths.append(_f)
    return paths


def _probe_zip_for_sld(zip_handler, destination_dir):
    file_names = clean_macosx_dir(zip_handler.namelist())
    result = []
    for f in _find_file_type(file_names, extension='.sld'):
        zip_handler.extract(f, destination_dir)
        result.append(os.path.join(destination_dir, f))
    return result
