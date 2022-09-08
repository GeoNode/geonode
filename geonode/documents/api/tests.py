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

from urllib.parse import urljoin

from django.urls import reverse
from rest_framework.test import APITestCase

from guardian.shortcuts import assign_perm, get_anonymous_user
from geonode.documents.models import Document
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class DocumentsApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')

    def test_documents(self):
        """
        Ensure we can access the Documents list.
        """
        url = reverse('documents-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 9)
        # Pagination
        self.assertEqual(len(response.data['documents']), 9)
        logger.debug(response.data)

        for _l in response.data['documents']:
            self.assertTrue(_l['resource_type'], 'document')

        # Get Linked Resources List
        resource = Document.objects.first()

        url = urljoin(f"{reverse('documents-detail', kwargs={'pk': resource.pk})}/", 'linked_resources/')
        assign_perm("base.view_resourcebase", get_anonymous_user(), resource.get_self_resource())
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        # import json
        # logger.error(f"{json.dumps(layers_data)}")
