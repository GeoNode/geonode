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
import json
import django
import logging

from django.urls import reverse
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.views.i18n import JavaScriptCatalog
from rest_framework.test import APITestCase, URLPatternsTestCase

from geonode.api.urls import router
from geonode.services.views import services
from geonode.maps.views import map_embed
from geonode.geoapps.views import geoapp_edit
from geonode.layers.views import layer_upload, layer_embed
from geonode.geoapps.models import GeoApp, GeoAppData

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class BaseApiTests(APITestCase, URLPatternsTestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    urlpatterns = [
        url(r'^home/$',
            TemplateView.as_view(template_name='index.html'),
            name='home'),
        url(r'^help/$',
            TemplateView.as_view(template_name='help.html'),
            name='help'),
        url(r'^developer/$',
            TemplateView.as_view(
                template_name='developer.html'),
            name='developer'),
        url(r'^about/$',
            TemplateView.as_view(template_name='about.html'),
            name='about'),
        url(r'^privacy_cookies/$',
            TemplateView.as_view(template_name='privacy-cookies.html'),
            name='privacy-cookies'),
        url(r"^account/", include("allauth.urls")),
        url(r'^people/', include('geonode.people.urls')),
        url(r'^api/v2/', include(router.urls)),
        url(r'^api/v2/', include('geonode.api.urls')),
        url(r'^api/v2/api-auth/', include('rest_framework.urls', namespace='geonode_rest_framework')),
        url(r'^upload$', layer_upload, name='layer_upload'),
        url(r'^$',
            TemplateView.as_view(template_name='layers/layer_list.html'),
            {'facet_type': 'layers', 'is_layer': True},
            name='layer_browse'),
        url(r'^$',
            TemplateView.as_view(template_name='maps/map_list.html'),
            {'facet_type': 'maps', 'is_map': True},
            name='maps_browse'),
        url(r'^$',
            TemplateView.as_view(template_name='documents/document_list.html'),
            {'facet_type': 'documents', 'is_document': True},
            name='document_browse'),
        url(r'^$',
            TemplateView.as_view(template_name='groups/group_list.html'),
            name='group_list'),
        url(r'^search/$',
            TemplateView.as_view(template_name='search/search.html'),
            name='search'),
        url(r'^$', services, name='services'),
        url(r'^invitations/', include(
            'geonode.invitations.urls', namespace='geonode.invitations')),
        url(r'^i18n/', include(django.conf.urls.i18n), name="i18n"),
        url(r'^jsi18n/$', JavaScriptCatalog.as_view(), {}, name='javascript-catalog'),
        url(r'^(?P<mapid>[^/]+)/embed$', map_embed, name='map_embed'),
        url(r'^(?P<layername>[^/]+)/embed$', layer_embed, name='layer_embed'),
        url(r'^(?P<geoappid>[^/]+)/embed$', geoapp_edit, {'template': 'apps/app_embed.html'}, name='geoapp_embed'),
    ]

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
        self.admin = get_user_model().objects.get(username='admin')
        self.bobby = get_user_model().objects.get(username='bobby')
        self.norman = get_user_model().objects.get(username='norman')
        self.gep_app = GeoApp.objects.create(
            title="Test GeoApp",
            owner=self.bobby
        )
        self.gep_app_data = GeoAppData.objects.create(
            blob='{"test_data": {"test": ["test_1","test_2","test_3"]}}',
            resource=self.gep_app
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
            response.data['geoapps'][0]['data'],
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
        url = reverse('geoapps-list')
        data = {
            "geoapp": {
                "name": "Test Create",
                "title": "Test Create",
                "owner": "bobby"
            }
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
        response = self.client.patch(url, data=json.dumps(data), format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"{url}?include[]=data", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        # Pagination
        self.assertTrue('data' in response.data['geoapp'])
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
        self.assertEqual(response.status_code, 204)  # 204 - No Content

        response = self.client.get(
            f"{url}?include[]=data", format='json')
        self.assertEqual(response.status_code, 404)  # 404 - Not Found
