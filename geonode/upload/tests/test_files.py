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

"""unit tests for geonode.upload.files module"""

from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.upload import files


class FilesTestCase(GeoNodeBaseTestSupport):

    def test_scan_hint_kml_ground_overlay(self):
        result = files.get_scan_hint(["kml", "other"])
        kml_file_type = files.get_type("KML Ground Overlay")
        self.assertEqual(result, kml_file_type.code)

    def test_scan_hint_kmz_ground_overlay(self):
        result = files.get_scan_hint(["kmz", "other"])
        self.assertEqual(result, "kmz")

    def test_get_type_non_existing_type(self):
        self.assertIsNone(files.get_type("fake"))

    def test_get_type_kml_ground_overlay(self):
        file_type = files.get_type("KML Ground Overlay")
        self.assertEqual(file_type.code, "kml-overlay")
        self.assertIn("kmz", file_type.aliases)
