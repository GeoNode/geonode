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

import requests
from django.test import LiveServerTestCase
from django.conf import settings
from geonode.decorators import on_ogc_backend
from geonode import qgis_server
from geonode.qgis_server.helpers import validate_django_settings
from geonode.qgis_server.helpers import ogc_server_settings


class QGISSettingsTest(GeoNodeBaseTestSupport):

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_settings(self):
        """Check that applied settings configured correctly."""
        self.assertTrue(validate_django_settings())

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_qgis_server_connection(self):
        """Test that QGIS Server url is reachable."""
        qgis_server_url = settings.QGIS_SERVER_URL
        response = requests.get(qgis_server_url)
        message = 'Cannot reach QGIS Server url at {url}'
        message = message.format(url=qgis_server_url)
        self.assertTrue(response.ok, message)
        self.assertIn(
            'Service unknown or unsupported', response.content, message)

        # Test if OTF-Plugin is installed
        url = f"{qgis_server_url}?SERVICE=MAPCOMPOSITION"
        response = requests.get(url)
        message = 'OTF-Project is not installed on QGIS-Server {url}'
        message = message.format(url=url)
        self.assertTrue(response.ok, message)
        self.assertIn(
            'PROJECT parameter is missing.', response.content, message)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_siteurl_connection(self):
        """Test that SITEURL is properly configured and reachable."""
        siteurl = settings.SITEURL
        response = self.client.get(siteurl)
        message = 'SITEURL were not properly configured: {url}'
        message = message.format(url=siteurl)

        self.assertEqual(response.status_code, 200, message)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_ogc_server_wrapper(self):
        """Test that OGC_Server settings were properly wrapped."""
        self.assertTrue(ogc_server_settings.PUBLIC_LOCATION)
        self.assertTrue(ogc_server_settings.LOCATION)
