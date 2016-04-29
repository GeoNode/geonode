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

import os
import gisdata
from xml.dom import minidom

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django.contrib.sites.models import Site

from geonode.layers.utils import file_upload
from geonode.layers.models import Layer

from .populate_sites_data import create_sites
from .models import SiteResources


@override_settings(SITE_NAME='Slave')
@override_settings(SITE_ID=2)
class SiteGeoserverTests(TestCase):

    fixtures = ['bobby']

    def setUp(self):
        super(SiteGeoserverTests, self).setUp()

        call_command('loaddata', 'people_data', verbosity=0)
        create_sites()

        self.slave_site = Site.objects.get(name='Slave')
        self.getcaps_url = """/proxy/?url=http%3A%2F%2Flocalhost%3A8080%2Fgeoserver%2Fwms%3F
                              SERVICE%3DWMS%26REQUEST%3DGetCapabilities"""

    def test_getcapabilities_filters_by_site(self):
        thefile1 = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        thefile2 = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_administrative.shp')
        file_upload(thefile1, overwrite=True)
        file_upload(thefile2, overwrite=True)

        # remove one layer from the site resources
        SiteResources.objects.get(site=self.slave_site).resources.remove(Layer.objects.all()[0])

        self.assertEqual(SiteResources.objects.get(site=self.slave_site).resources.count(), 1)

        self.client.login(username='bobby', password='bob')
        resp = self.client.get(self.getcaps_url)
        xml = minidom.parseString(resp.content)
        getcaps_layer = xml.getElementsByTagName('Layer')[0]
        self.assertEqual(len(getcaps_layer.getElementsByTagName('Layer')), 1)
