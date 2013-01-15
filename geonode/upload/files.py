#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import zipfile
import os
import re


vector = FeatureType.resource_type
raster = Coverage.resource_type


xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")


class SpatialFile(object):

    is_compressed = False
    file_type = "unknown"
    layer_type = None
    base_file = None
    auxillary_files = None
    sld_files = None

    def __init__(self, **kwargs):
        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])
            else:
                raise ValueError("%s invalid arg" % k)


class FileType(object):
    
    name = None
    code = None
    auxillary_file_exts = None
    aliases = None
    layer_type = None

    def __init__(self, name, code, layer_type, aliases=None, auxillary_file_exts=None):
        self.name = name
        self.code = code
        self.layer_type = layer_type
        self.aliases = aliases or []
        self.auxillary_file_exts = auxillary_file_exts or []
            
    def matches(self, ext):
        return ext == self.code or ext in self.aliases
    
    def build_spatial_file(self, base, others, is_compressed):
        aux_files, slds = self.find_auxillary_files(base, others)
        return SpatialFile( is_compressed=is_compressed, file_type=self.code,
                            layer_type = self.layer_type, base_file=base,
                            auxillary_files = aux_files, sld_files = slds
        )
        
    def find_auxillary_files(self, base, others):
        base_name = os.path.splitext(base)[0]
        base_matches = filter( lambda f: os.path.splitext(f)[0] == base_name, others)
        slds = _find_sld_files(base_matches)
        aux_files = filter( lambda f: os.path.splitext(f)[1][1:].lower() in self.aux_files, others)
        return aux_files, slds

    def __repr__(self):
        return "%s - %s" % (self.__class__, self.code)


TYPE_UNKNOWN = FileType("unknown", None, None)

types = [
    FileType("Shapefile", "shp", vector, auxillary_file_exts=('dbf','shx','prj')),
    FileType("GeoTIFF", "tif", raster, aliases=('tiff','geotif','geotiff')),
    FileType("CSV", "csv", vector),
    FileType("KML", "kml", vector, aliases=('kmz',)),
]


def _contains_bad_names(file_names):
    '''return True if the list of names contains a bad one'''
    xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")
    return any([ xml_unsafe.search(f) for f in file_names ])


def _rename_files(file_names):
    renamed = []
    for f in file_names:
        dirname, base_name = os.path.split(f)
        safe = xml_unsafe.sub("_", base_name)
        if safe != base_name:
            safe = os.path.join(dirname, safe)
            os.rename(f, safe)
            renamed.append(safe)
    return renamed
            

def _find_sld_files(file_names):
    return filter( lambda f: f.lower().endswith('.sld'), file_names)


def scan_file(file_name):
    '''get a list of SpatialFiles for the provided file'''
    
    dirname = os.path.dirname(file_name)
    files = None
    is_compressed = False
    
    if zipfile.is_zipfile(file_name):
        zf = None
        try:
            zf = zipfile.ZipFile(file_name, 'r')
            files = zf.namelist()
            if _contains_bad_names(files):
                zf.extractall(dirname)
                files = None
            else:
                is_compressed = True
                for f in _find_sld_files(files):
                    zf.extract(f, dirname)
        except:
            raise Exception('Unable to read zip file')
        zf.close()
        
    if files is None:
        files = os.listdir(dirname)
        
    _rename_files(files)
    found = []
    
    for file_type in types:
        for f in files:
            name, ext = os.path.splitext(f)
            ext = ext[1:].lower()
            if file_type.matches(ext):
                found.append( file_type.build(f, files, is_compressed) )

    found.extend( [SpatialFile(f) for f in found] )
    
    # detect slds and assign iff a single upload is found
    sld_files = _find_sld_files(files)
    if sld_files:
        if len(found) == 1:
            found[0].sld_files = sld_files
        else:
            raise Exception("One or more SLD files was provided, but no " +
                            "matching files were found for them.")
                
    return found