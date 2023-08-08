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

import os
import zipfile
import contextlib

from geonode.utils import mkdtemp


@contextlib.contextmanager
def create_files(names, zipped=False):
    tmpdir = mkdtemp()
    names = [os.path.join(tmpdir, f) for f in names]
    for f in names:
        # required for windows to read the shapefile in binary mode and the zip
        # in non-binary
        if zipped:
            open(f, "w").close()
        else:
            try:
                open(f, "wb").close()
            except OSError:
                # windows fails at writing special characters
                # need to do something better here
                print("Test does not work in Windows")
    if zipped:
        basefile = os.path.join(tmpdir, "files.zip")
        zf = zipfile.ZipFile(basefile, "w", allowZip64=True)
        with zf:
            for f in names:
                zf.write(f, os.path.basename(f))

        for f in names:
            os.unlink(f)
        names = [basefile]
    yield names
