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

from geonode.tests.base import GeoNodeBaseTestSupport

from xml.etree import ElementTree
import os
import shutil

from geonode import qgis_server
from geonode.decorators import on_ogc_backend
from geonode.qgis_server.xml_utilities import (
    insert_xml_element, update_xml)


class XMLUtilitiesTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    """Test for xml utilities module."""

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_insert_xml_element(self):
        """Check we can't insert custom nested elements"""
        root = ElementTree.Element('root')
        b = ElementTree.SubElement(root, 'b')
        ElementTree.SubElement(b, 'c')

        new_element_path = 'd/e/f'
        expected_xml = '<root><b><c /></b><d><e><f>TESTtext</f></e></d></root>'

        element = insert_xml_element(root, new_element_path)
        element.text = 'TESTtext'
        result_xml = ElementTree.tostring(root)

        self.assertEqual(expected_xml, result_xml)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_update_xml(self):
        """Test inserting xml element."""
        file_path = os.path.realpath(__file__)
        test_dir = os.path.dirname(file_path)
        xml_file_path = os.path.join(test_dir, 'data', 'test.xml')

        # Creating temporary xml file
        temp_xml_file_path = os.path.join(test_dir, 'data', 'temp_test.xml')
        shutil.copy2(xml_file_path, temp_xml_file_path)

        # Check if the temp file is created
        self.assertTrue(os.path.exists(temp_xml_file_path))

        new_values = {
            'title': 'New Title',
        }

        # Make sure there is no new value in the xml
        with open(temp_xml_file_path, 'r') as temp_xml_file:
            temp_xml_content = temp_xml_file.read()

        self.assertNotIn(new_values['title'], temp_xml_content)

        # Updating the xml file
        update_xml(temp_xml_file_path, new_values)

        # Check if the new value has been added.
        with open(temp_xml_file_path, 'r') as temp_xml_file:
            temp_xml_content = temp_xml_file.read()
        self.assertIn(new_values['title'], temp_xml_content)

        # Remove temp file
        os.remove(temp_xml_file_path)
        self.assertFalse(os.path.exists(temp_xml_file_path))
