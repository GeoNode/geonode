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

from django.urls import reverse
from django.conf.urls import url
from rest_framework.test import APITestCase, URLPatternsTestCase

from geonode import geoserver
from geonode.layers.models import Layer
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class LayersApiTests(APITestCase, URLPatternsTestCase):

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

    def test_layers(self):
        """
        Ensure we can access the Layers list.
        """
        url = reverse('layers-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 8)
        # Pagination
        self.assertEqual(len(response.data['layers']), 8)
        logger.debug(response.data)

        for _l in response.data['layers']:
            self.assertTrue(_l['resource_type'], 'layer')

    def test_raw_HTML_stripped_properties(self):
        """
        Ensure "raw_*" properties returns no HTML or carriage-return tag
        """
        layer = Layer.objects.first()
        layer.abstract = "<p><em>No abstract provided</em>.</p>\r\n<p><img src=\"data:image/jpeg;base64,/9j/4AAQSkZJR/>"
        layer.constraints_other = "<p><span style=\"text-decoration: underline;\">None</span></p>"
        layer.supplemental_information = "<p>No information provided &iacute;</p> <p>&pound;682m</p>"
        layer.data_quality_statement = "<p><strong>OK</strong></p>\r\n<table style=\"border-collapse: collapse; width:\
            85.2071%;\" border=\"1\">\r\n<tbody>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">1</td>\r\n<td style=\"width:\
            50%;\">2</td>\r\n</tr>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">a</td>\r\n<td style=\"width: 50%;\">b</td>\
            \r\n</tr>\r\n</tbody>\r\n</table>"
        layer.save()

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        url = reverse('layers-detail', kwargs={'pk': layer.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['layer']['pk']), int(layer.pk))
        self.assertEqual(response.data['layer']['raw_abstract'], "No abstract provided.")
        self.assertEqual(response.data['layer']['raw_constraints_other'], "None")
        self.assertEqual(response.data['layer']['raw_supplemental_information'], "No information provided í £682m")
        self.assertEqual(response.data['layer']['raw_data_quality_statement'], "OK    1 2   a b")
