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

"""unit tests for geonode.upload.upload_preprocessing module"""

from geonode.tests.base import GeoNodeBaseTestSupport

try:
    import unittest.mock as mock
except ImportError:
    import mock
import os.path

from geonode.upload import files
from geonode.upload import upload_preprocessing
from geonode.upload.utils import get_kml_doc


class UploadPreprocessingTestCase(GeoNodeBaseTestSupport):

    MOCK_PREFIX = "geonode.upload.upload_preprocessing"

    @mock.patch(MOCK_PREFIX + ".convert_kml_ground_overlay_to_geotiff", autospec=True)
    def test_preprocess_files_kml_ground_overlay(self, mock_handler):
        dirname = "phony"
        kml_path = "fake_path.kml"
        image_path = "another_fake_path.png"
        data = [
            files.SpatialFile(
                base_file=kml_path,
                file_type=files.get_type("KML Ground Overlay"),
                auxillary_files=[image_path],
                sld_files=[],
                xml_files=[]
            )
        ]
        spatial_files = files.SpatialFiles(dirname, data)
        upload_preprocessing.preprocess_files(spatial_files)
        mock_handler.assert_called_with(kml_path, image_path)

    def test_extract_bbox_param(self):
        fake_north = "70.000"
        kml_bytes = """
            <?xml version="1.0" encoding="UTF-8"?>
            <kml xmlns="http://earth.google.com/kml/2.1">
            <Document>
              <GroundOverlay id="groundoverlay">
                <LatLonBox>
                  <north>{}</north>
                </LatLonBox>
              </GroundOverlay>
            </Document>
            </kml>
        """.format(fake_north).strip()
        kml_doc, ns = get_kml_doc(kml_bytes)
        result = upload_preprocessing._extract_bbox_param(
            kml_doc, ns, "north")
        self.assertEqual(result, fake_north)

    @mock.patch(MOCK_PREFIX + ".subprocess.check_output", autospec=True)
    @mock.patch(MOCK_PREFIX + ".get_kml_doc", autospec=True)
    @mock.patch(MOCK_PREFIX + "._extract_bbox_param", autospec=True)
    def test_convert_kml_ground_overlay_to_geotiff(self, mock_extract_param,
                                                   mock_get_kml_doc,
                                                   mock_subprocess):
        fake_other_file_path = "the_image.png"
        fake_kml_bytes = "nothing"
        mock_get_kml_doc.return_value = ("not_relevant", "for_this_test")
        fake_north = "1"
        fake_south = "2"
        fake_east = "3"
        fake_west = "4"
        mock_extract_param.side_effect = [fake_west, fake_north,
                                          fake_east, fake_south]
        mock_open = mock.mock_open(read_data=fake_kml_bytes)
        with mock.patch(self.MOCK_PREFIX + ".open", mock_open):
            upload_preprocessing.convert_kml_ground_overlay_to_geotiff(
                "fake_kml_path",
                fake_other_file_path
            )
            mock_subprocess.assert_called_with([
                "gdal_translate",
                "-of", "GTiff",
                "-a_srs", "EPSG:4326",
                "-a_ullr", fake_west, fake_north, fake_east, fake_south,
                fake_other_file_path,
                os.path.splitext(fake_other_file_path)[0] + ".tif"
            ])
