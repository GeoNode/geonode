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

import contextlib
import os
import shutil
import tempfile
import zipfile
import geonode.upload.files as files
from unittest import TestCase
from geonode.upload.files import SpatialFiles, scan_file
from geonode.upload.files import _rename_files, _contains_bad_names


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

    def test_contains_bad_names(self):
        self.assertTrue(_contains_bad_names(['1', 'a']))
        self.assertTrue(_contains_bad_names(['a', 'foo-bar']))

    def test_rename_files(self):
        with create_files(['junk<y>', 'notjunky']) as tests:
            try:
                renamed = files._rename_files(tests)
                self.assertTrue(renamed[0].endswith("junk_y_"))
            except WindowsError:
                pass

    def test_rename_and_prepare(self):
        with create_files(['109029_23.tiff', 'notjunk<y>']) as tests:
            tests = _rename_files(tests)
            self.assertTrue(tests[0].endswith("_109029_23.tiff"))
            self.assertTrue(tests[1].endswith("junk_y_"))

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
        file_names = ['109029_23.shp', '109029_23.shx', '109029_23.dbf',
                      '109029_23.prj', '109029_23.xml', '109029_23.sld']
        with create_files(file_names, zipped=True) as tests:
            spatial_files = scan_file(tests[0])
            self.assertTrue(isinstance(spatial_files, SpatialFiles))

            spatial_file = spatial_files[0]
            self.assertTrue(spatial_file.file_type.matches('shp'))
            self.assertEqual(len(spatial_file.auxillary_files), 3)
            self.assertEqual(len(spatial_file.xml_files), 1)
            self.assertEqual(len(spatial_file.sld_files), 1)
            self.assertTrue(
                all(map(lambda s: s.endswith('xml'), spatial_file.xml_files)))

            basedir = os.path.dirname(spatial_file.base_file)
            for f in file_names:
                path = os.path.join(basedir, '_%s' % f)
                self.assertTrue(os.path.exists(path))


class TimeFormFormTest(TestCase):

    def _form(self, data):
        # prevent circular deps error - not sure why this module was getting
        # imported during normal runserver execution but it was...
        from geonode.upload.forms import TimeForm
        return TimeForm(
            data,
            time_names=['start_date', 'end_date'],
            text_names=['start_text', 'end_text'],
            year_names=['start_year', 'end_year']
        )

    def assert_start_end(self, data, start, end=None):
        form = self._form(data)
        self.assertTrue(form.is_valid())
        if start:
            self.assertEqual(start, form.cleaned_data['start_attribute'])
        if end:
            self.assertEqual(end, form.cleaned_data['end_attribute'])

    def test_invalid_form(self):
        form = self._form(dict(time_attribute='start_date', text_attribute='start_text'))
        self.assertTrue(not form.is_valid())

    def test_start_end_attribute_and_type(self):
        self.assert_start_end(
            dict(time_attribute='start_date'),
            ('start_date', 'Date')
        )
        self.assert_start_end(
            dict(text_attribute='start_text', end_year_attribute='end_year'),
            ('start_text', 'Text'),
            ('end_year', 'Number')
        )
        self.assert_start_end(
            dict(year_attribute='start_year', end_time_attribute='end_date'),
            ('start_year', 'Number'),
            ('end_date', 'Date')
        )
