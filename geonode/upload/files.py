# -*- coding: utf-8 -*-
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

'''An incomplete replacement for the various file support functions currently
scattered over the codebase

@todo complete and use
'''

import os.path
from geoserver.resource import FeatureType
from geoserver.resource import Coverage

from UserList import UserList
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
        return "<SpatialFile base_file=%s file_type=%s aux=%s sld=%s xml=%s>" % (
            self.base_file, self.file_type, self.auxillary_files, self.sld_files, self.xml_files)


class FileType(object):

    def __init__(
            self,
            name,
            code,
            layer_type,
            aliases=None,
            auxillary_file_exts=None):
        self.name = name
        self.code = code
        self.layer_type = layer_type
        self.auxillary_file_exts = auxillary_file_exts or []
        self.aliases = aliases or []

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
        return "<FileType %s>" % self.code


TYPE_UNKNOWN = FileType("unknown", None, None)

types = [
    FileType("Shapefile", "shp", vector,
             auxillary_file_exts=('dbf', 'shx', 'prj')),
    FileType("GeoTIFF", "tif", raster,
             aliases=('tiff', 'geotif', 'geotiff')),
    # requires geoserver importer extension
    FileType("PNG", "png", raster,
             auxillary_file_exts=('prj')),
    FileType("JPG", "jpg", raster,
             auxillary_file_exts=('prj')),
    FileType("CSV", "csv", vector),
    FileType("GeoJSON", "geojson", vector),
    FileType("KML", "kml", vector,
             aliases=('kmz')),
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
             auxillary_file_exts=('sdw')),
    FileType("JP2", "jp2", raster)
]


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
    return filter(lambda f: f.lower().endswith(extension), file_names)


def scan_file(file_name):
    '''get a list of SpatialFiles for the provided file'''

    dirname = os.path.dirname(file_name)
    files = None

    archive = None

    if zipfile.is_zipfile(file_name):
        # rename this now
        logger.debug('{} is a zip.'.format(file_name))
        file_name = _rename_files([file_name])[0]
        zf = None
        try:
            zf = zipfile.ZipFile(file_name, 'r')
            files = zf.namelist()
            if _contains_bad_names(files):
                zf.extractall(dirname)
                files = None
            else:
                archive = os.path.abspath(file_name)
                for f in _find_file_type(files, extension='.sld'):
                    zf.extract(f, dirname)
        except:
            raise Exception('Unable to read zip file')
        zf.close()

    def dir_files():
        def abs(*p):
            return os.path.abspath(os.path.join(*p))
        return [abs(dirname, f) for f in os.listdir(dirname)]

    if files is None:
        # not a zip, list the files
        files = dir_files()

    else:
        # is a zip, add other files (sld if any)
        files.extend(dir_files())

    logger.debug('Found the following files: {0}'.format(files))
    files = _rename_files(files)
    logger.debug('Cleaned file names: {0}'.format(files))

    found = []

    for file_type in types:
        for f in files:
            name, ext = os.path.splitext(f)
            if file_type.matches(ext[1:]):
                found.append(file_type.build_spatial_file(f, files))

    # detect slds and assign iff a single upload is found
    sld_files = _find_file_type(files, extension='.sld')
    if sld_files:
        if len(found) == 1:
            found[0].sld_files = sld_files
        else:
            raise Exception("One or more SLD files was provided, but no " +
                            "matching files were found for them.")

    return SpatialFiles(dirname, found, archive)
