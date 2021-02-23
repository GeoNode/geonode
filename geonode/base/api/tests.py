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
from PIL import Image
from io import BytesIO
from unittest.mock import patch
from urllib.parse import urljoin

import django
from django.urls import reverse
from django.core.files import File
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from rest_framework.test import APITestCase, URLPatternsTestCase

from guardian.shortcuts import get_anonymous_user

from geonode.api.urls import router
from geonode.base.models import ResourceBase
from geonode.base.models import CuratedThumbnail

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.services.views import services
from geonode.maps.views import map_embed
from geonode.layers.views import layer_embed
from geonode.geoapps.views import geoapp_edit
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)

test_image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))


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
        url(r"^account/", include("allauth.urls")),
        url(r'^people/', include('geonode.people.urls')),
        url(r'^api/v2/', include(router.urls)),
        url(r'^api/v2/', include('geonode.api.urls')),
        url(r'^api/v2/api-auth/', include('rest_framework.urls', namespace='geonode_rest_framework')),
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

    def test_gropus_list(self):
        """
        Ensure we can access the gropus list.
        """
        url = reverse('group-profiles-list')
        # Unauhtorized
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 403)

        # Auhtorized
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(len(response.data['group_profiles']), 2)

        url = reverse('group-profiles-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['group_profile']['title'], 'Registered Members')
        self.assertEqual(response.data['group_profile']['description'], 'Registered Members')
        self.assertEqual(response.data['group_profile']['access'], 'private')
        self.assertEqual(response.data['group_profile']['group']['name'], response.data['group_profile']['slug'])

    def test_users_list(self):
        """
        Ensure we can access the users list.
        """
        url = reverse('users-list')
        # Unauhtorized
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 403)

        # Auhtorized
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 10)
        self.assertEqual(len(response.data['users']), 10)

        url = reverse('users-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['user']['username'], 'admin')
        self.assertIsNotNone(response.data['user']['avatar'])

    def test_base_resources(self):
        """
        Ensure we can access the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Remove public permissions to Layers
        from geonode.layers.utils import set_layers_permissions
        set_layers_permissions(
            "read",  # permissions_name
            None,  # resources_names == None (all layers)
            [get_anonymous_user()],  # users_usernames
            None,  # groups_names
            True,   # delete_flag
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 18)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Bobby
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 20)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Norman
        self.assertTrue(self.client.login(username='norman', password='norman'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 19)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Pagination
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(f"{url}?page_size=17", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 17)

    def test_search_resources(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(
            f"{url}?search=ca&search_fields=title&search_fields=abstract", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['resources']), 1)

    def test_filter_resources(self):
        """
        Ensure we can filter across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        # Filter by owner == bobby
        response = self.client.get(f"{url}?filter{{owner.username}}=bobby", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 6)
        # Pagination
        self.assertEqual(len(response.data['resources']), 6)

        # Filter by resource_type == document
        response = self.client.get(f"{url}?filter{{resource_type}}=document", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 9)
        # Pagination
        self.assertEqual(len(response.data['resources']), 9)

        # Filter by resource_type == layer and title like 'common morx'
        response = self.client.get(
            f"{url}?filter{{resource_type}}=layer&filter{{title.icontains}}=common morx", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['resources']), 1)

        # Filter by Keywords
        response = self.client.get(
            f"{url}?filter{{keywords.name}}=here", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['resources']), 1)

        # Filter by Metadata Regions
        response = self.client.get(
            f"{url}?filter{{regions.name.icontains}}=Italy", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 0)
        # Pagination
        self.assertEqual(len(response.data['resources']), 0)

        # Filter by Metadata Categories
        response = self.client.get(
            f"{url}?filter{{category.identifier}}=elevation", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 9)
        # Pagination
        self.assertEqual(len(response.data['resources']), 9)

        # Extent Filter
        response = self.client.get(f"{url}?page_size=26&extent=-180,-90,180,90", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 26)

        response = self.client.get(f"{url}?page_size=26&extent=0,0,100,100", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 26)

        response = self.client.get(f"{url}?page_size=26&extent=-10,-10,-1,-1", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 12)
        # Pagination
        self.assertEqual(len(response.data['resources']), 12)

        # Extent Filter: Crossing Dateline
        extent = "-180.0000,56.9689,-162.5977,70.7435,155.9180,56.9689,180.0000,70.7435"
        response = self.client.get(
            f"{url}?page_size=26&extent={extent}", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 12)
        # Pagination
        self.assertEqual(len(response.data['resources']), 12)

    def test_sort_resources(self):
        """
        Ensure we can sort the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(
            f"{url}?sort[]=title", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)

        resource_titles = []
        for _r in response.data['resources']:
            resource_titles.append(_r['title'])
        sorted_resource_titles = sorted(resource_titles.copy())
        self.assertEqual(resource_titles, sorted_resource_titles)

        response = self.client.get(
            f"{url}?sort[]=-title", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)

        resource_titles = []
        for _r in response.data['resources']:
            resource_titles.append(_r['title'])

        reversed_resource_titles = sorted(resource_titles.copy())
        self.assertNotEqual(resource_titles, reversed_resource_titles)

    def test_perms_resources(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resource = ResourceBase.objects.filter(owner__username='bobby').first()

        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))

        url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'get_perms/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertTrue('bobby' in resource_perm_spec['users'])
        self.assertFalse('norman' in resource_perm_spec['users'])

        # Add perms to Norman
        url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'set_perms/')
        resource_perm_spec['users']['norman'] = resource_perm_spec['users']['bobby']
        response = self.client.put(url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 200)

        url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'get_perms/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertTrue('norman' in resource_perm_spec['users'])

        # Remove perms to Norman
        url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'set_perms/')
        resource_perm_spec['users']['norman'] = []
        response = self.client.put(url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 200)

        url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'get_perms/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertFalse('norman' in resource_perm_spec['users'])

    def test_featured_and_published_resources(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resources = ResourceBase.objects.filter(owner__username='bobby')

        url = urljoin(f"{reverse('base-resources-list')}/", 'featured/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 0)
        # Pagination
        self.assertEqual(len(response.data['resources']), 0)

        resources.filter(resource_type='map').update(featured=True)
        url = urljoin(f"{reverse('base-resources-list')}/", 'featured/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 2)
        # Pagination
        self.assertEqual(len(response.data['resources']), 2)

    def test_resource_types(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = urljoin(f"{reverse('base-resources-list')}/", 'resource_types/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('resource_types' in response.data)
        self.assertTrue('layer' in response.data['resource_types'])
        self.assertTrue('map' in response.data['resource_types'])
        self.assertTrue('document' in response.data['resource_types'])
        self.assertTrue('service' in response.data['resource_types'])

    @patch('PIL.Image.open', return_value=test_image)
    def test_thumbnail_urls(self, img):
        """
        Ensure the thumbnail url reflects the current active Thumb on the resource.
        """
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resource = ResourceBase.objects.filter(owner__username='bobby').first()
        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))
        thumbnail_url = response.data['resource']['thumbnail_url']
        self.assertIsNone(thumbnail_url)

        f = BytesIO(test_image.tobytes())
        f.name = 'test_image.jpeg'
        curated_thumbnail = CuratedThumbnail.objects.create(resource=resource, img=File(f))

        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))
        thumbnail_url = response.data['resource']['thumbnail_url']
        self.assertTrue(curated_thumbnail.thumbnail_url in thumbnail_url)

    def test_embed_urls(self):
        """
        Ensure the embed urls reflect the concrete instance ones.
        """
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resources = ResourceBase.objects.all()
        for resource in resources:
            url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))
            embed_url = response.data['resource']['embed_url']
            self.assertIsNotNone(embed_url)

            instance = resource.get_real_instance()
            if hasattr(instance, 'embed_url'):
                if instance.embed_url != NotImplemented:
                    self.assertEqual(instance.embed_url, embed_url)
                else:
                    self.assertEqual("", embed_url)
