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
import logging
import sys
from unittest.mock import patch
from urllib.parse import urljoin

from django.urls import reverse
from rest_framework.test import APITestCase

from geonode.datasets.models import Dataset
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class LayersApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')

    def test_datasets(self):
        """
        Ensure we can access the Layers list.
        """
        url = reverse('datasets-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 8)

        # Pagination
        self.assertEqual(len(response.data['datasets']), 8)
        logger.debug(response.data)

        for _l in response.data['datasets']:
            self.assertTrue(_l['resource_type'], 'layer')
        # Test list response doesn't have attribute_set
        self.assertIsNone(response.data['datasets'][0].get('attribute_set'))
        # Test detail response has attribute_set
        url = urljoin(f"{reverse('datasets-list')}/", f"{Dataset.objects.first().pk}")
        response = self.client.get(url, format='json')
        self.assertIsNotNone(response.data['datasets'].get('attribute_set'))

    def test_raw_HTML_stripped_properties(self):
        """
        Ensure "raw_*" properties returns no HTML or carriage-return tag
        """
        dataset = Dataset.objects.first()
        dataset.abstract = "<p><em>No abstract provided</em>.</p>\r\n<p><img src=\"data:image/jpeg;base64,/9j/4AAQSkZJR/>"
        dataset.constraints_other = "<p><span style=\"text-decoration: underline;\">None</span></p>"
        dataset.supplemental_information = "<p>No information provided &iacute;</p> <p>&pound;682m</p>"
        dataset.data_quality_statement = "<p><strong>OK</strong></p>\r\n<table style=\"border-collapse: collapse; width:\
            85.2071%;\" border=\"1\">\r\n<tbody>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">1</td>\r\n<td style=\"width:\
            50%;\">2</td>\r\n</tr>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">a</td>\r\n<td style=\"width: 50%;\">b</td>\
            \r\n</tr>\r\n</tbody>\r\n</table>"
        dataset.save()

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        url = reverse('datasets-detail', kwargs={'pk': dataset.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['dataset']['pk']), int(dataset.pk))
        self.assertEqual(response.data['dataset']['raw_abstract'], "No abstract provided.")
        self.assertEqual(response.data['dataset']['raw_constraints_other'], "None")
        self.assertEqual(response.data['dataset']['raw_supplemental_information'], "No information provided í £682m")
        self.assertEqual(response.data['dataset']['raw_data_quality_statement'], "OK    1 2   a b")

    def test_datasets_set_thumbnail_from_bbox_from_Anonymous_user_raise_permission_error(self):
        """
        Given a request with Anonymous user, should raise an authentication error.
        """
        dataset_id = sys.maxsize
        url = reverse('datasets-set-thumb-from-bbox', args=[dataset_id])
        # Anonymous
        expected = {
            "detail": "Authentication credentials were not provided."
        }
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(expected, response.json())

    @patch("geonode.datasets.api.views.create_thumbnail")
    def test_datasets_set_thumbnail_from_bbox_from_logged_user_for_existing_dataset(self, mock_create_thumbnail):
        """
        Given a logged User and an existing dataset, should create the expected thumbnail url.
        """
        mock_create_thumbnail.return_value = "http://localhost:8000/mocked_url.jpg"
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Dataset.objects.first().resourcebase_ptr_id
        url = reverse('datasets-set-thumb-from-bbox', args=[dataset_id])
        payload = {
            "bbox": [
                -9072629.904175375,
                -9043966.018568434,
                1491839.8773032012,
                1507127.2829602365
            ],
            "srid": "EPSG:3857"
        }
        response = self.client.post(url, data=payload, format='json')

        expected = {
            "thumbnail_url": "http://localhost:8000/mocked_url.jpg"
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, response.json())

    def test_datasets_set_thumbnail_from_bbox_from_logged_user_for_not_existing_dataset(self):
        """
        Given a logged User and an not existing dataset, should raise a 404 error.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = sys.maxsize
        url = reverse('datasets-set-thumb-from-bbox', args=[dataset_id])
        payload = {
            "bbox": [
                -9072629.904175375,
                -9043966.018568434,
                1491839.8773032012,
                1507127.2829602365
            ],
            "srid": "EPSG:3857"
        }
        response = self.client.post(url, data=payload, format='json')

        expected = {
            "message": f"Dataset selected with id {dataset_id} does not exists"
        }
        self.assertEqual(response.status_code, 404)
        self.assertEqual(expected, response.json())
