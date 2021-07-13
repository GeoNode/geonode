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
import logging

from urllib.parse import urljoin

from django.urls import reverse
from django.conf.urls import url
from rest_framework.test import APITestCase, URLPatternsTestCase

from geonode.documents.models import Document

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class DocumentsApiTests(APITestCase, URLPatternsTestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    from geonode.urls import urlpatterns

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.views import layer_acls, resolve_user
        urlpatterns += [
            url(r'^acls/?$', layer_acls, name='layer_acls'),
            url(r'^acls_dep/?$', layer_acls, name='layer_acls_dep'),
            url(r'^resolve_user/?$', resolve_user, name='layer_resolve_user'),
            url(r'^resolve_user_dep/?$', resolve_user, name='layer_resolve_user_dep'),
        ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'layer')

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

        # Test embed_url is provided
        self.assertIn('link', response.data['documents'][0]['embed_url'])

        # Pagination
        self.assertEqual(len(response.data['documents']), 9)
        logger.debug(response.data)

        for _l in response.data['documents']:
            self.assertTrue(_l['resource_type'], 'document')

        # Get Linked Resources List
        resource = Document.objects.first()

        url = urljoin(f"{reverse('documents-detail', kwargs={'pk': resource.pk})}/", 'linked_resources/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        # import json
        # logger.error(f"{json.dumps(layers_data)}")
