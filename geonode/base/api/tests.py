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
from geonode.thumbs.exceptions import ThumbnailError
import logging
import sys
from uuid import uuid4
from PIL import Image
from io import BytesIO
from unittest.mock import patch
from urllib.parse import urljoin

from django.urls import reverse
from django.core.files import File
from django.conf.urls import url
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, URLPatternsTestCase

from guardian.shortcuts import get_anonymous_user

from geonode.base.models import (
    CuratedThumbnail,
    HierarchicalKeyword,
    Region,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
)

from geonode import geoserver
from geonode.favorite.models import Favorite
from geonode.utils import check_ogc_backend, set_resource_default_links
from geonode.layers.models import Layer
from geonode.base.utils import build_absolute_uri
from geonode.base.populate_test_data import create_models
from geonode.security.utils import get_resources_with_perms
from geonode.documents.models import Document
logger = logging.getLogger(__name__)

test_image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))


class BaseApiTests(APITestCase, URLPatternsTestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json',
        "test_thesaurus.json"
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
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(len(response.data['users']), 0)

        # Auhtorized
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 10)
        self.assertEqual(len(response.data['users']), 10)
        # response has link to the response
        self.assertTrue('link' in response.data['users'][0].keys())

        url = reverse('users-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['user']['username'], 'admin')
        self.assertIsNotNone(response.data['user']['avatar'])

        # anonymous users are not in contributors group
        url = reverse('users-detail', kwargs={'pk': -1})
        response = self.client.get(url, format='json')
        self.assertNotIn('add_resource', response.data['user']['perms'])

        # Bobby
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        # Bobby cannot access other users' details
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 404)

        # Bobby can see himself in the list
        url = reverse('users-list')
        self.assertEqual(len(response.data), 1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(len(response.data['users']), 1)

        # Bobby can access its own details
        bobby = get_user_model().objects.filter(username='bobby').get()
        url = reverse('users-detail', kwargs={'pk': bobby.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['user']['username'], 'bobby')
        self.assertIsNotNone(response.data['user']['avatar'])
        # default contributor group_perm is returned in perms
        self.assertIn('add_resource', response.data['user']['perms'])

    def test_register_users(self):
        """
        Ensure users are created with default groups.
        """
        url = reverse('users-list')
        user_data = {
            'username': 'new_user',
        }
        response = self.client.post(url, data=user_data, format='json')
        self.assertEqual(response.status_code, 201)
        # default contributor group_perm is returned in perms
        self.assertIn('add_resource', response.data['user']['perms'])

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
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # response has link to the response
        self.assertTrue('link' in response.data['resources'][0].keys())
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Bobby
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
        # Pagination
        self.assertEqual(len(response.data['resources']), 10)
        logger.debug(response.data)

        # Norman
        self.assertTrue(self.client.login(username='norman', password='norman'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 26)
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

        # Check user permissions
        resource = ResourceBase.objects.filter(owner__username='bobby').first()
        # Admin
        response = self.client.get(f"{url}/{resource.id}/", format='json')
        self.assertTrue('change_resourcebase' in list(response.data['resource']['perms']))
        # Annonymous
        self.assertIsNone(self.client.logout())
        response = self.client.get(f"{url}/{resource.id}/", format='json')
        self.assertFalse('change_resourcebase' in list(response.data['resource']['perms']))
        # user owner
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(f"{url}/{resource.id}/", format='json')
        self.assertTrue('change_resourcebase' in list(response.data['resource']['perms']))
        # user not owner and not assigned
        self.assertTrue(self.client.login(username='norman', password='norman'))
        response = self.client.get(f"{url}/{resource.id}/", format='json')
        self.assertFalse('change_resourcebase' in list(response.data['resource']['perms']))
        # response has links property
        # create link
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            layer = Layer.objects.first()
            set_resource_default_links(layer, layer)
            response = self.client.get(f"{url}/{layer.id}/", format='json')
            self.assertTrue('links' in response.data['resource'].keys())

        # test 'tkeywords'
        try:
            for _tkw in ThesaurusKeyword.objects.filter(pk__gte=34):
                resource.tkeywords.add(_tkw)
            self.assertEqual(6, resource.tkeywords.count())
            # Admin
            self.assertTrue(self.client.login(username='admin', password='admin'))
            response = self.client.get(f"{url}/{resource.id}/", format='json')
            self.assertIsNotNone(response.data['resource']['tkeywords'])
            self.assertEqual(6, len(response.data['resource']['tkeywords']))
            self.assertListEqual(
                [
                    {
                        'name': '',
                        'slug': 'http-inspire-ec-europa-eu-theme-37',
                        'uri': 'http://inspire.ec.europa.eu/theme#37',
                        'thesaurus': {
                            'name': 'GEMET - INSPIRE themes, version 1.0',
                            'slug': 'inspire-theme',
                            'uri': 'http://inspire.ec.europa.eu/theme'
                        },
                        'i18n': {}
                    },
                    {
                        'name': '',
                        'slug': 'http-localhost-8001-thesaurus-no-about-thesauro-38',
                        'uri': 'http://localhost:8001//thesaurus/no-about-thesauro#38',
                        'thesaurus': {
                            'name': 'Thesauro without the about',
                            'slug': 'no-about-thesauro',
                            'uri': ''
                        },
                        'i18n': {}
                    },
                    {
                        'name': 'bar_keyword',
                        'slug': 'http-localhost-8001-thesaurus-no-about-thesauro-bar-keyword',
                        'uri': 'http://localhost:8001//thesaurus/no-about-thesauro#bar_keyword',
                        'thesaurus': {
                            'name': 'Thesauro without the about',
                            'slug': 'no-about-thesauro', 'uri': ''
                        },
                        'i18n': {}
                    },
                    {
                        'name': 'foo_keyword',
                        'slug': 'http-inspire-ec-europa-eu-theme-foo-keyword',
                        'uri': 'http://inspire.ec.europa.eu/theme#foo_keyword',
                        'thesaurus': {
                            'name': 'GEMET - INSPIRE themes, version 1.0',
                            'slug': 'inspire-theme',
                            'uri': 'http://inspire.ec.europa.eu/theme'
                        },
                        'i18n': {}
                    },
                    {
                        'name': 'mf',
                        'slug': 'http-inspire-ec-europa-eu-theme-mf',
                        'uri': 'http://inspire.ec.europa.eu/theme/mf',
                        'thesaurus': {
                            'name': 'GEMET - INSPIRE themes, version 1.0',
                            'slug': 'inspire-theme',
                            'uri': 'http://inspire.ec.europa.eu/theme'
                        },
                        'i18n': {
                            'en': 'Meteorological geographical features'
                        }
                    },
                    {
                        'name': 'us',
                        'slug': 'http-inspire-ec-europa-eu-theme-us',
                        'uri': 'http://inspire.ec.europa.eu/theme/us',
                        'thesaurus': {
                            'name': 'GEMET - INSPIRE themes, version 1.0',
                            'slug': 'inspire-theme',
                            'uri': 'http://inspire.ec.europa.eu/theme'
                        },
                        'i18n': {
                            'en': 'Utility and governmental services'
                        }
                    }
                ],
                response.data['resource']['tkeywords']
            )
        finally:
            resource.tkeywords.set(ThesaurusKeyword.objects.none())
            self.assertEqual(0, resource.tkeywords.count())

    def test_delete_user_with_resource(self):
        owner, created = get_user_model().objects.get_or_create(username='delet-owner')
        Layer(
            title='Test Remove User',
            abstract='abstract',
            name='Test Remove User',
            alternate='Test Remove User',
            uuid=str(uuid4()),
            owner=owner,
            storeType='coverageStore',
            category=TopicCategory.objects.get(identifier='elevation')
        ).save()
        # Delete user and check if default user is updated
        owner.delete()
        self.assertEqual(
            ResourceBase.objects.get(title='Test Remove User').owner,
            get_user_model().objects.get(username='admin')
        )

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
        self.assertEqual(response.data['total'], 3)
        # Pagination
        self.assertEqual(len(response.data['resources']), 3)

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
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'set_perms/')
        get_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'get_perms/')

        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertTrue('bobby' in resource_perm_spec['users'])
        self.assertFalse('norman' in resource_perm_spec['users'])

        # Add perms to Norman
        resource_perm_spec['users']['norman'] = resource_perm_spec['users']['bobby']
        response = self.client.put(set_perms_url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertTrue('norman' in resource_perm_spec['users'])

        # Remove perms to Norman
        resource_perm_spec['users']['norman'] = []
        response = self.client.put(set_perms_url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertFalse('norman' in resource_perm_spec['users'])

        # Ensure get_perms and set_perms are done by users with correct permissions.
        # logout admin user
        self.assertIsNone(self.client.logout())
        # get perms
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 403)
        # set perms
        response = self.client.put(set_perms_url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 403)
        # login resourse owner
        # get perms
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        # set perms
        response = self.client.put(set_perms_url, data=resource_perm_spec, format='json')
        self.assertEqual(response.status_code, 200)

    def test_featured_and_published_resources(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resources = ResourceBase.objects.filter(owner__username='bobby', metadata_only=False)

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
        self.assertEqual(response.data['total'], resources.filter(resource_type='map').count())
        # Pagination
        self.assertEqual(len(response.data['resources']), resources.filter(resource_type='map').count())

    def test_resource_types(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = urljoin(f"{reverse('base-resources-list')}/", 'resource_types/')
        response = self.client.get(url, format='json')
        r_type_names = [item['name'] for item in response.data['resource_types']]
        self.assertEqual(response.status_code, 200)
        self.assertTrue('resource_types' in response.data)
        self.assertTrue('layer' in r_type_names)
        self.assertTrue('map' in r_type_names)
        self.assertTrue('document' in r_type_names)
        self.assertFalse('service' in r_type_names)

    def test_get_favorites(self):
        """
        Ensure we get user's favorite resources.
        """
        layer = Layer.objects.first()
        url = urljoin(f"{reverse('base-resources-list')}/", 'favorites/')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 403)
        # Authenticated user
        bobby = get_user_model().objects.get(username='bobby')
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        favorite = Favorite.objects.create_favorite(layer, bobby)
        response = self.client.get(url, format='json')
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.status_code, 200)
        # clean up
        favorite.delete()

    def test_create_and_delete_favorites(self):
        """
        Ensure we can add and remove resources to user's favorite.
        """
        layer = get_resources_with_perms(get_user_model().objects.get(pk=-1)).first()
        url = urljoin(f"{reverse('base-resources-list')}/", f"{layer.pk}/favorite/")
        # Anonymous
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, 403)
        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.post(url, format="json")
        self.assertEqual(response.data["message"], "Successfuly added resource to favorites")
        self.assertEqual(response.status_code, 201)
        # add resource to favorite again
        response = self.client.post(url, format="json")
        self.assertEqual(response.data["message"], "Resource is already in favorites")
        self.assertEqual(response.status_code, 400)
        # remove resource from favorites
        response = self.client.delete(url, format="json")
        self.assertEqual(response.data["message"], "Successfuly removed resource from favorites")
        self.assertEqual(response.status_code, 200)
        # remove resource to favorite again
        response = self.client.delete(url, format="json")
        self.assertEqual(response.data["message"], "Resource not in favorites")
        self.assertEqual(response.status_code, 404)

    def test_search_resources_with_favorite_true_and_no_favorite_should_return_0(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(
            f"{url}?favorite=true", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        # No favorite are saved, so the total should be 0
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(len(response.data['resources']), 0)

    def test_search_resources_with_favorite_true_and_favorite_should_return_1(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse('base-resources-list')
        # Admin
        admin = get_user_model().objects.get(username='admin')
        layer = Layer.objects.first()
        Favorite.objects.create_favorite(layer, admin)

        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(
            f"{url}?favorite=true", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        # 1 favorite is saved, so the total should be 1
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(len(response.data['resources']), 1)

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
            if resource.title.endswith('metadata true'):
                self.assertEqual(response.status_code, 404)
            else:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))
                embed_url = response.data['resource']['embed_url']
                self.assertIsNotNone(embed_url)

                instance = resource.get_real_instance()
                if hasattr(instance, 'embed_url'):
                    if instance.embed_url != NotImplemented:
                        self.assertEqual(build_absolute_uri(instance.embed_url), embed_url)
                    else:
                        self.assertEqual("", embed_url)

    def test_owners_list(self):
        """
        Ensure we can access the list of owners.
        """
        url = reverse('owners-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 8)

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 8)
        response = self.client.get(f"{url}?type=geoapp", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        response = self.client.get(f"{url}?type=layer&title__icontains=CA", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        # response has link to the response
        self.assertTrue('link' in response.data['owners'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 8)

    def test_categories_list(self):
        """
        Ensure we can access the list of categories.
        """
        url = reverse('categories-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], TopicCategory.objects.count())

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], TopicCategory.objects.count())
        # response has link to the response
        self.assertTrue('link' in response.data['categories'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], TopicCategory.objects.count())

    def test_regions_list(self):
        """
        Ensure we can access the list of regions.
        """
        url = reverse('regions-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], Region.objects.count())

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], Region.objects.count())
        # response has link to the response
        self.assertTrue('link' in response.data['regions'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], Region.objects.count())

    def test_keywords_list(self):
        """
        Ensure we can access the list of keywords.
        """
        url = reverse('keywords-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], HierarchicalKeyword.objects.count())

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], HierarchicalKeyword.objects.count())
        # response has link to the response
        self.assertTrue('link' in response.data['keywords'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], HierarchicalKeyword.objects.count())

    def test_tkeywords_list(self):
        """
        Ensure we can access the list of thasaurus keywords.
        """
        url = reverse('tkeywords-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], ThesaurusKeyword.objects.count())

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], ThesaurusKeyword.objects.count())
        # response has uri to the response
        self.assertTrue('uri' in response.data['tkeywords'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], ThesaurusKeyword.objects.count())

    def test_set_thumbnail_from_bbox_from_Anonymous_user_raise_permission_error(self):
        """
        Given a request with Anonymous user, should raise an authentication error.
        """
        dataset_id = sys.maxsize
        url = reverse('base-resources-set-thumb-from-bbox', args=[dataset_id])
        # Anonymous
        expected = {
            "detail": "Authentication credentials were not provided."
        }
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(expected, response.json())

    @patch("geonode.base.api.views.create_thumbnail")
    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_dataset(self, mock_create_thumbnail):
        """
        Given a logged User and an existing dataset, should create the expected thumbnail url.
        """
        mock_create_thumbnail.return_value = "http://localhost:8000/mocked_url.jpg"
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Layer.objects.first().resourcebase_ptr_id
        url = reverse('base-resources-set-thumb-from-bbox', args=[dataset_id])
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
            'message': 'Thumbnail correctly created.',
            'success': True,
            'thumbnail_url': 'http://localhost:8000/mocked_url.jpg'
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, response.json())

    def test_set_thumbnail_from_bbox_from_logged_user_for_not_existing_dataset(self):
        """
        Given a logged User and an not existing dataset, should raise a 404 error.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = sys.maxsize
        url = reverse('base-resources-set-thumb-from-bbox', args=[dataset_id])
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
            'message': f'Resource selected with id {dataset_id} does not exists',
            'success': False
        }
        self.assertEqual(response.status_code, 404)
        self.assertEqual(expected, response.json())

    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_doc(self):
        """
        Given a logged User and an existing doc, should raise a NotImplemented.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Document.objects.first().resourcebase_ptr_id
        url = reverse('base-resources-set-thumb-from-bbox', args=[dataset_id])
        payload = {
            "bbox": [],
            "srid": "EPSG:3857"
        }
        response = self.client.post(url, data=payload, format='json')

        expected = {
            'message': 'Not implemented: Endpoint available only for Dataset and Maps',
            'success': False
        }
        self.assertEqual(response.status_code, 405)
        self.assertEqual(expected, response.json())

    @patch("geonode.base.api.views.create_thumbnail", side_effect=ThumbnailError('Some exception during thumb creation'))
    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_dataset_raise_exp(self, mock_exp):
        """
        Given a logged User and an existing dataset, should raise a ThumbnailException.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Layer.objects.first().resourcebase_ptr_id
        url = reverse('base-resources-set-thumb-from-bbox', args=[dataset_id])
        payload = {
            "bbox": [],
            "srid": "EPSG:3857"
        }
        response = self.client.post(url, data=payload, format='json')

        expected = {
            'message': 'Some exception during thumb creation',
            'success': False
        }
        self.assertEqual(response.status_code, 500)
        self.assertEqual(expected, response.json())
