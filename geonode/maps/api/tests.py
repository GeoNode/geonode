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
from django.conf import settings

from django.urls import reverse
from django.conf.urls import url, include
from rest_framework.test import APITestCase, URLPatternsTestCase

from geonode.maps.models import Map

from geonode import geoserver
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models, create_single_map

logger = logging.getLogger(__name__)


class MapsApiTests(APITestCase, URLPatternsTestCase):

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

    if settings.GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == 'mapstore':
        from mapstore2_adapter.api.urls import router as mas2_api_router
        urlpatterns += [
            url(r'^', include('mapstore2_adapter.api.urls')),
            url(r'^mapstore/rest/', include(mas2_api_router.urls)),
        ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'layer')

    def test_maps(self):
        """
        Ensure we can access the Maps list.
        """
        url = reverse('maps-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 9)
        # Pagination
        self.assertEqual(len(response.data['maps']), 9)
        logger.debug(response.data)

        for _l in response.data['maps']:
            self.assertTrue(_l['resource_type'], 'map')

        # Get Layers List (backgrounds)
        resource = Map.objects.first()

        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", 'layers/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        # Get Local-Layers List (GeoNode)
        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", 'local_layers/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        if settings.GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == 'mapstore':
            url = reverse('resources-list')
            self.assertEqual(url, '/mapstore/rest/resources/')

            from mapstore2_adapter import fixup_map
            fixup_map(resource.id)
            # Anonymous
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            if response.data:
                self.assertEqual(len(response.data), 1)

                # Get Full MapStore layer configuration
                url = reverse('resources-detail', kwargs={'pk': resource.pk})
                response = self.client.get(f"{url}?full=true", format='json')
                self.assertEqual(response.status_code, 200)
                self.assertTrue(len(response.data) > 0)
                self.assertTrue('data' in response.data)
                self.assertTrue('attributes' in response.data)


class TestExtraMetadataMapsApi(GeoNodeBaseTestSupport):
    def setUp(self):
        self.map = create_single_map('single_map')
        self.metadata = {
            "name": "metadata-name",
            "slug": "metadata-slug",
            "help_text": "this is the help text",
            "field_type": "str",
            "value": "my value",
            "category": "cat1"
        }
        Map.objects.filter(id=self.map.id).update(extra_metadata=[self.metadata])
     
    def test_get_will_return_the_list_of_extra_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('maps-extra-metadata', args=[self.map.id])
        response = self.client.get(url, content_type='application/json')
        self.assertTrue(200, response.status_code)
        self.assertEqual([self.metadata], response.json())

    def test_put_will_update_the_whole_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('maps-extra-metadata', args=[self.map.id])
        input_metadata = {
            "name": "metadata-updated",
            "slug": "metadata-slug-updated",
            "help_text": "this is the help text-updated",
            "field_type": "str-updated",
            "value": "my value-updated",
            "category": "cat1-updated"
        }
        response = self.client.put(url, data=[input_metadata], content_type='application/json')
        self.assertTrue(200, response.status_code)
        self.assertEqual([input_metadata], response.json())

    def test_post_will_add_new_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('maps-extra-metadata', args=[self.map.id])
        input_metadata = {
            "name": "metadata-new",
            "slug": "metadata-slug-new",
            "help_text": "this is the help text-new",
            "field_type": "str-new",
            "value": "my value-new",
            "category": "cat1-new"
        }
        response = self.client.post(url, data=[input_metadata], content_type='application/json')
        self.assertTrue(201, response.status_code)
        self.assertEqual(2, len(response.json()))

    def test_delete_will_delete_single_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('maps-extra-metadata', args=[self.map.id])
        response = self.client.delete(url, data=[self.metadata], content_type='application/json')
        self.assertTrue(200, response.status_code)
        self.assertEqual([], response.json())
