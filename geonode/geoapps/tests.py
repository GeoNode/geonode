# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode.geoapps.models import GeoApp
from geonode.tests.base import GeoNodeBaseTestSupport


class TestGeoAppViews(GeoNodeBaseTestSupport):

    def test_update_geoapp_metadata(self):
        bobby = get_user_model().objects.get(username='bobby')
        gep_app = GeoApp.objects.create(
            title="App",
            thumbnail_url='initial',
            owner=bobby
        )
        gep_app.set_default_permissions()
        url = reverse('geoapp_metadata', args=(gep_app.id,))
        data = {
            'resource-title': 'New title',
            'resource-owner': bobby.id,
            'resource-date': '2021-10-27 05:59 am',
            "resource-date_type": 'publication',
            'resource-language': gep_app.language
        }
        self.client.login(username=bobby.username, password='bob')
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(gep_app.thumbnail_url, GeoApp.objects.get(id=gep_app.id).thumbnail_url)
        self.assertEqual(GeoApp.objects.get(id=gep_app.id).title, 'New title')
        #   Check uuid is populate
        self.assertTrue(GeoApp.objects.get(id=gep_app.id).uuid)
