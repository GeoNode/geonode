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
import json
import logging

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from geonode.geoapps.models import GeoApp
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class GeoAppsApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')
        self.admin = get_user_model().objects.get(username='admin')
        self.bobby = get_user_model().objects.get(username='bobby')
        self.norman = get_user_model().objects.get(username='norman')
        self.gep_app = GeoApp.objects.create(
            title="Test GeoApp",
            owner=self.bobby,
            resource_type="geostory",
            blob='{"test_data": {"test": ["test_1","test_2","test_3"]}}'
        )
        self.gep_app.set_default_permissions()

    def test_geoapps_list(self):
        """
        Ensure we can access the GeoApps list.
        """
        url = reverse('geoapps-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['geoapps']), 1)
        self.assertTrue('data' not in response.data['geoapps'][0])

        response = self.client.get(
            f"{url}?include[]=data", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['geoapps']), 1)
        self.assertTrue('data' in response.data['geoapps'][0])
        self.assertEqual(
            json.loads(response.data['geoapps'][0]['data']),
            {
                "test_data": {
                    "test": [
                        'test_1',
                        'test_2',
                        'test_3'
                    ]
                }
            }
        )

    def test_geoapps_crud(self):
        """
        Ensure we can create/update GeoApps.
        """
        # Bobby
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        # Create
        url = f"{reverse('geoapps-list')}?include[]=data"
        data = {
            "name": "Test Create",
            "title": "Test Create",
            "resource_type": "geostory",
            "owner": "bobby"
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, 201)  # 201 - Created

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 2)
        # Pagination
        self.assertEqual(len(response.data['geoapps']), 2)

        # Update: PATCH
        url = reverse('geoapps-detail', kwargs={'pk': self.gep_app.pk})
        data = {
            "blob": {
                "test_data": {
                    "test": [
                        'test_4',
                        'test_5',
                        'test_6'
                    ]
                }
            }
        }
        response = self.client.patch(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"{url}?include[]=data", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        # Pagination
        self.assertTrue('data' in response.data['geoapp'])
        self.assertEqual(
            response.data['geoapp']['resource_type'],
            'geostory'
        )
        self.assertEqual(
            response.data['geoapp']['data'],
            {
                "test_data": {
                    "test": [
                        'test_4',
                        'test_5',
                        'test_6'
                    ]
                }
            }
        )

        # Update: POST
        data = {
            "test_data": {
                "test": [
                    'test_1',
                    'test_2',
                    'test_3'
                ]
            }
        }
        response = self.client.post(url, data=json.dumps(data), format='json')
        self.assertEqual(response.status_code, 405)  # 405 – Method not allowed

        # Delete
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, 405)  # 405 - Method Not Allowed

        response = self.client.get(
            f"{url}?include[]=data", format='json')
        self.assertEqual(response.status_code, 200)
