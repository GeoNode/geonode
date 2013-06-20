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
import files

import contextlib
import os
import shutil
import tempfile
import unittest
import zipfile

@contextlib.contextmanager
def create_files(names, zipped=False):
    tmpdir = tempfile.mkdtemp()
    names = [ os.path.join(tmpdir, f) for f in names ]
    for f in names:
        open(f, 'w').close()
    if zipped:
        basefile = os.path.join(tmpdir,'files.zip')
        zf = zipfile.ZipFile(basefile,'w')
        for f in names:
            zf.write(f)
        zf.close()
        for f in names:
            os.unlink(f)
        names = [basefile]
    yield names
    shutil.rmtree(tmpdir)

class FilesTests(unittest.TestCase):

    def test_types(self):
        for t in files.types:
            self.assertTrue(t.code is not None)
            self.assertTrue(t.name is not None)
            self.assertTrue(t.layer_type is not None)

    def test_rename_files(self):
        with create_files(['junk<y>','notjunky']) as tests:
            renamed = files._rename_files(tests)
            self.assertTrue(renamed[0].endswith("junk_y_"))