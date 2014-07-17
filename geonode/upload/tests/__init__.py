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
import contextlib
import os
import shutil
import tempfile
import zipfile
import geonode.upload.files as files
from django.test import TestCase
from geonode.upload.utils import rename_and_prepare
from geonode.upload.files import SpatialFiles, scan_file


@contextlib.contextmanager
def create_files(names, zipped=False):
    tmpdir = tempfile.mkdtemp()
    names = [os.path.join(tmpdir, f) for f in names]
    for f in names:
        # required for windows to read the shapefile in binary mode and the zip
        # in non-binary
        if zipped:
            open(f, 'w').close()
        else:
            try:
                open(f, 'wb').close()
            except IOError:
                # windows fails at writing special characters
                # need to do something better here
                print "Test does not work in Windows"
    if zipped:
        basefile = os.path.join(tmpdir, 'files.zip')
        zf = zipfile.ZipFile(basefile, 'w')
        for f in names:
            zf.write(f, os.path.basename(f))
        zf.close()
        for f in names:
            os.unlink(f)
        names = [basefile]
    yield names
    shutil.rmtree(tmpdir)


class FilesTests(TestCase):

    def test_types(self):
        for t in files.types:
            self.assertTrue(t.code is not None)
            self.assertTrue(t.name is not None)
            self.assertTrue(t.layer_type is not None)

    def test_rename_files(self):
        with create_files(['junk<y>', 'notjunky']) as tests:
            try:
                renamed = files._rename_files(tests)
                self.assertTrue(renamed[0].endswith("junk_y_"))
            except WindowsError:
                pass

    def test_rename_and_prepare(self):
        with create_files(['109029_23.tiff', 'notjunk<y>']) as tests:
            tests = map(rename_and_prepare, tests)
            self.assertTrue(tests[0].endswith("_109029_23.tiff"))
            self.assertTrue(tests[1].endswith("junk_y_"))

        with create_files(['109029_23.shp', '109029_23.shx', '109029_23.dbf', '109029_23.prj'], zipped=True) as tests:
            tests = rename_and_prepare(tests[0])
            path = os.path.dirname(tests)
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        path,
                        '_109029_23.shp')))
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        path,
                        '_109029_23.shx')))
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        path,
                        '_109029_23.dbf')))
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        path,
                        '_109029_23.prj')))

    def test_scan_file(self):
        """
        Tests the scan_file function.
        """
        exts = ('.shp', '.shx', '.sld', '.xml', '.prj', '.dbf')

        with create_files(map(lambda s: 'san_andres_y_providencia_location{0}'.format(s), exts)) as tests:
            shp = filter(lambda s: s.endswith('.shp'), tests)[0]
            spatial_files = scan_file(shp)
            self.assertTrue(isinstance(spatial_files, SpatialFiles))

            spatial_file = spatial_files[0]
            self.assertEqual(shp, spatial_file.base_file)
            self.assertTrue(spatial_file.file_type.matches('shp'))
            self.assertEqual(len(spatial_file.auxillary_files), 3)
            self.assertEqual(len(spatial_file.xml_files), 1)
            self.assertTrue(
                all(map(lambda s: s.endswith('xml'), spatial_file.xml_files)))
            self.assertEqual(len(spatial_file.sld_files), 1)
            self.assertTrue(
                all(map(lambda s: s.endswith('sld'), spatial_file.sld_files)))

        # Test the scan_file function with a zipped spatial file that needs to
        # be renamed.
        with create_files(['109029_23.shp', '109029_23.shx', '109029_23.dbf',
                           '109029_23.prj', '109029_23.xml'], zipped=True) as tests:
            spatial_files = scan_file(tests[0])
            self.assertTrue(isinstance(spatial_files, SpatialFiles))

            spatial_file = spatial_files[0]
            self.assertTrue(spatial_file.file_type.matches('shp'))
            self.assertEqual(len(spatial_file.auxillary_files), 3)
            self.assertEqual(len(spatial_file.xml_files), 1)
            self.assertEqual(len(spatial_file.sld_files), 0)
            self.assertTrue(
                all(map(lambda s: s.endswith('xml'), spatial_file.xml_files)))
