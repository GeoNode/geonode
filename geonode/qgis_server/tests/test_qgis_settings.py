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

import requests
from unittest import TestCase
from django.conf import settings
from geonode.decorators import on_ogc_backend
from geonode import qgis_server


class QGISSettingsTest(TestCase):

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_settings(self):
        """Check that applied settings configured correctly."""

        # geonode.qgis_server must exists in INSTALLED_APPS and not geoserver
        self.assertIn('geonode.qgis_server', settings.INSTALLED_APPS)
        self.assertNotIn('geonode.geoserver', settings.INSTALLED_APPS)

        # LOCAL_GEOSERVER settings should not exists
        self.assertFalse(hasattr(settings, 'LOCAL_GEOSERVER'))

        # Should not include geoserver context_processor
        geoserver_context_processor = \
            'geonode.geoserver.context_processors.geoserver_urls'

        context_processors = settings.TEMPLATES[
            0]['OPTIONS']['context_processors']

        self.assertNotIn(geoserver_context_processor, context_processors)

        self.assertTrue(hasattr(settings, 'QGIS_SERVER_URL'))
        self.assertTrue(hasattr(settings, 'QGIS_SERVER_CONFIG'))

        # QGIS Server at the moment only works with leflet preview library
        self.assertTrue(settings.LAYER_PREVIEW_LIBRARY, 'leaflet')

        # Check OGC Server settings
        default_ogc_backend = settings.OGC_SERVER['default']
        self.assertTrue(
            default_ogc_backend['BACKEND'], qgis_server.BACKEND_PACKAGE)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_qgis_server_connection(self):
        """Test that QGIS Server url is reachable."""
        qgis_server_url = settings.QGIS_SERVER_URL
        response = requests.get(qgis_server_url)
        message = 'Cannot reach QGIS Server url at {url}'
        message = message.format(url=qgis_server_url)
        self.assertEqual(response.status_code, 200, message)
        self.assertIn(
            'Service unknown or unsupported', response.content, message)

        # Test if OTF-Plugin is installed
        url = qgis_server_url + '?SERVICE=MAPCOMPOSITION'
        response = requests.get(url)
        message = 'OTF-Project is not installed on QGIS-Server {url}'
        message = message.format(url=qgis_server_url)
        self.assertEqual(response.status_code, 200, message)
        self.assertIn(
            'PROJECT parameter is missing.', response.content, message)
