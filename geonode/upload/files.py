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

"""An incomplete replacement for the various file support functions currently
scattered over the codebase

@todo complete and use
"""
import re
import logging

from collections import UserList
from geoserver.resource import FeatureType, Coverage


logger = logging.getLogger("importer")

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


class SpatialFile:
    def __init__(self, base_file, file_type, auxillary_files, sld_files, xml_files):
        self.base_file = base_file
        self.file_type = file_type
        self.auxillary_files = auxillary_files
        self.sld_files = sld_files
        self.xml_files = xml_files

    def all_files(self):
        return [self.base_file] + self.auxillary_files

    def __repr__(self):
        return f"<SpatialFile base_file={self.base_file} file_type={self.file_type} \
aux={self.auxillary_files} sld={self.sld_files} xml={self.xml_files}>"
