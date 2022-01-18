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
import sys
import json
import logging
import re

from PIL import Image
from io import BytesIO
from time import sleep
from uuid import uuid1, uuid4
from unittest.mock import patch
from urllib.parse import urljoin

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from guardian.shortcuts import get_anonymous_user

from geonode.base import enumerations
from geonode.groups.models import GroupProfile
from geonode.thumbs.exceptions import ThumbnailError
from geonode.base.models import (
    HierarchicalKeyword,
    Region,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
)

from geonode.layers.models import Dataset
from geonode.favorite.models import Favorite
from geonode.documents.models import Document
from geonode.utils import build_absolute_uri
from geonode.resource.api.tasks import ExecutionRequest
from geonode.base.populate_test_data import create_models
from geonode.security.utils import get_resources_with_perms

logger = logging.getLogger(__name__)

test_image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))


class BaseApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json',
        "test_thesaurus.json"
    ]

    def setUp(self):
        self.maxDiff = None
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')

    def test_gropus_list(self):
        """
        Ensure we can access the gropus list.
        """
        pub_1 = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        priv_1 = GroupProfile.objects.create(slug="priv_1", title="priv_1", access="private")
        priv_2 = GroupProfile.objects.create(slug="priv_2", title="priv_2", access="private")
        pub_invite_1 = GroupProfile.objects.create(slug="pub_invite_1", title="pub_invite_1", access="public-invite")
        pub_invite_2 = GroupProfile.objects.create(slug="pub_invite_2", title="pub_invite_2", access="public-invite")
        try:
            # Anonymous can access only public groups
            url = reverse('group-profiles-list')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data['total'], 4)
            self.assertEqual(len(response.data['group_profiles']), 4)
            self.assertTrue(all([_g['access'] != 'private' for _g in response.data['group_profiles']]))

            # Admin can access all groups
            self.assertTrue(self.client.login(username='admin', password='admin'))
            url = reverse('group-profiles-list')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data['total'], 6)
            self.assertEqual(len(response.data['group_profiles']), 6)

            # Bobby can access public groups and the ones he is member of
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            priv_1.join(get_user_model().objects.get(username='bobby'))
            url = reverse('group-profiles-list')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data['total'], 5)
            self.assertEqual(len(response.data['group_profiles']), 5)
            self.assertTrue(any([_g['slug'] == 'priv_1' for _g in response.data['group_profiles']]))

            url = reverse('group-profiles-detail', kwargs={'pk': priv_1.pk})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
        finally:
            pub_1.delete()
            priv_1.delete()
            priv_2.delete()
            pub_invite_1.delete()
            pub_invite_2.delete()

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
        self.assertEqual(response.data['total'], 10)
        self.assertEqual(len(response.data['users']), 10)

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
        # Bobby can access other users' details
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        # Bobby can see himself in the list
        url = reverse('users-list')
        self.assertEqual(len(response.data), 1)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 10)
        self.assertEqual(len(response.data['users']), 10)

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

        # Bobby can't access other users perms list
        norman = get_user_model().objects.filter(username='norman').get()
        url = reverse('users-detail', kwargs={'pk': norman.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['user']['username'], 'norman')
        self.assertIsNotNone(response.data['user']['avatar'])
        # default contributor group_perm is returned in perms
        self.assertNotIn('perms', response.data['user'])

    def test_register_users(self):
        """
        Ensure users are created with default groups.
        """
        url = reverse('users-list')
        user_data = {
            'username': 'new_user',
        }
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(url, data=user_data, format='json')
        self.assertEqual(response.status_code, 201)
        # default contributor group_perm is returned in perms
        self.assertIn('add_resource', response.data['user']['perms'])

    def test_delete_users(self):
        """
        Ensure users cannot delete others.
        """
        norman = get_user_model().objects.get(username='norman')
        url = reverse('users-detail', kwargs={'pk': norman.pk})
        # Anonymous can read
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        # Anonymous can't write
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, 403)
        # Bob can't delete Norman
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, 403)

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
        from geonode.layers.utils import set_datasets_permissions
        set_datasets_permissions(
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
        self.assertEqual(response.data['resource']['state'], enumerations.STATE_PROCESSED)
        self.assertEqual(response.data['resource']['sourcetype'], enumerations.SOURCE_TYPE_LOCAL)
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
        Dataset(
            title='Test Remove User',
            abstract='abstract',
            name='Test Remove User',
            alternate='Test Remove User',
            uuid=str(uuid4()),
            owner=owner,
            subtype='raster',
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
            f"{url}?filter{{resource_type}}=dataset&filter{{title.icontains}}=common morx", format='json')
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
        self.assertEqual(response.data['total'], 6)
        # Pagination
        self.assertEqual(len(response.data['resources']), 6)

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
        bobby = get_user_model().objects.get(username='bobby')
        norman = get_user_model().objects.get(username='norman')
        anonymous_group = Group.objects.get(name='anonymous')
        contributors_group = Group.objects.get(name='registered-members')

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        resource = ResourceBase.objects.filter(owner__username='bobby').first()
        if not resource.uuid:
            resource.uuid = str(uuid1())
            resource.save()
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'permissions')
        get_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'permissions')

        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                'users': [
                    {
                        'id': bobby.id,
                        'username': bobby.username,
                        'first_name': bobby.first_name,
                        'last_name': bobby.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'owner',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'manage',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': anonymous_group.id,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'download'
                    },
                    {
                        'id': contributors_group.id,
                        'title': 'Registered Members',
                        'name': contributors_group.name,
                        'permissions': 'none'
                    }
                ]
            },
            resource_perm_spec
        )

        # Add perms to Norman
        resource_perm_spec_patch = {
            'users': [
                {
                    'id': norman.id,
                    'username': norman.username,
                    'first_name': norman.first_name,
                    'last_name': norman.last_name,
                    'avatar': '',
                    'permissions': 'edit',
                    'is_staff': False,
                    'is_superuser': False,
                }
            ]
        }
        data = f"uuid={resource.uuid}&permissions={json.dumps(resource_perm_spec_patch)}"
        response = self.client.patch(set_perms_url, data=data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        status_url = response.data.get('status_url')
        _counter = 0
        while _counter < 100 and status != ExecutionRequest.STATUS_FINISHED and status != ExecutionRequest.STATUS_FAILED:
            response = self.client.get(status_url)
            status = response.data.get('status')
            sleep(3.0)
            _counter += 1
            logger.error(f"[{_counter}] GET {status_url} ----> {response.data}")
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                'users': [
                    {
                        'id': bobby.id,
                        'username': bobby.username,
                        'first_name': bobby.first_name,
                        'last_name': bobby.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'owner',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'id': norman.id,
                        'username': norman.username,
                        'first_name': norman.first_name,
                        'last_name': norman.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'edit',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'manage',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': anonymous_group.id,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'download'
                    },
                    {
                        'id': contributors_group.id,
                        'title': 'Registered Members',
                        'name': contributors_group.name,
                        'permissions': 'none'
                    }
                ]
            },
            resource_perm_spec
        )

        # Remove perms to Norman
        resource_perm_spec = {
            'users': [
                {
                    'id': bobby.id,
                    'username': bobby.username,
                    'first_name': bobby.first_name,
                    'last_name': bobby.last_name,
                    'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                    'permissions': 'owner',
                    'is_staff': False,
                    'is_superuser': False,
                },
                {
                    'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                    'first_name': 'admin',
                    'id': 1,
                    'last_name': '',
                    'permissions': 'manage',
                    'username': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                }
            ],
            'organizations': [],
            'groups': [
                {
                    'id': anonymous_group.id,
                    'title': 'anonymous',
                    'name': 'anonymous',
                    'permissions': 'view'
                },
                {
                    'id': contributors_group.id,
                    'title': 'Registered Members',
                    'name': contributors_group.name,
                    'permissions': 'none'
                }
            ]
        }
        data = f"uuid={resource.uuid}&permissions={json.dumps(resource_perm_spec)}"
        response = self.client.put(set_perms_url, data=data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        status_url = response.data.get('status_url')
        _counter = 0
        while _counter < 100 and status != ExecutionRequest.STATUS_FINISHED and status != ExecutionRequest.STATUS_FAILED:
            response = self.client.get(status_url)
            status = response.data.get('status')
            sleep(3.0)
            _counter += 1
            logger.error(f"[{_counter}] GET {status_url} ----> {response.data}")
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                'users': [
                    {
                        'id': bobby.id,
                        'username': bobby.username,
                        'first_name': bobby.first_name,
                        'last_name': bobby.last_name,
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'owner',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'first_name': 'admin',
                        'id': 1,
                        'last_name': '',
                        'permissions': 'manage',
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': anonymous_group.id,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'view'
                    },
                    {
                        'id': contributors_group.id,
                        'title': 'Registered Members',
                        'name': contributors_group.name,
                        'permissions': 'none'
                    }
                ]
            },
            resource_perm_spec
        )

        # Ensure get_perms and set_perms are done by users with correct permissions.
        # logout admin user
        self.assertIsNone(self.client.logout())
        # get perms
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 403)
        # set perms
        data = f"uuid={resource.uuid}&permissions={json.dumps(resource_perm_spec)}"
        response = self.client.put(set_perms_url, data=data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 403)
        # login resourse owner
        # get perms
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        # set perms
        data = f"uuid={resource.uuid}&permissions={json.dumps(resource_perm_spec)}"
        response = self.client.put(set_perms_url, data=data, content_type='application/x-www-form-urlencoded')
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
        r_types = [item for item in response.data['resource_types']]
        r_type_names = [r_type['name'] for r_type in r_types]
        self.assertEqual(response.status_code, 200)
        self.assertTrue('resource_types' in response.data)
        self.assertTrue('dataset' in r_type_names)
        self.assertTrue('map' in r_type_names)
        self.assertTrue('document' in r_type_names)
        self.assertFalse('service' in r_type_names)

        r_type_perms = {r_type['name']: r_type['allowed_perms'] for r_type in r_types}
        self.assertDictEqual(
            r_type_perms['dataset'],
            {
                "perms": {
                    "anonymous": [
                        "view_resourcebase",
                        "download_resourcebase"
                    ],
                    "default": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase",
                        "download_resourcebase",
                        "change_dataset_data",
                        "change_dataset_style"
                    ],
                    "registered-members": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase",
                        "download_resourcebase",
                        "change_dataset_data",
                        "change_dataset_style"
                    ]
                },
                "compact": {
                    "anonymous": [
                        "none",
                        "view",
                        "download"
                    ],
                    "default": [
                        "view",
                        "download",
                        "edit",
                        "manage",
                        "owner"
                    ],
                    "registered-members": [
                        "none",
                        "view",
                        "download",
                        "edit",
                        "manage"
                    ]
                }
            }
        )
        self.assertDictEqual(
            r_type_perms['document'],
            {
                "perms": {
                    "anonymous": [
                        "view_resourcebase",
                        "download_resourcebase"
                    ],
                    "default": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase",
                        "download_resourcebase"
                    ],
                    "registered-members": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase",
                        "download_resourcebase"
                    ]
                },
                "compact": {
                    "anonymous": [
                        "none",
                        "view",
                        "download"
                    ],
                    "default": [
                        "view",
                        "download",
                        "edit",
                        "manage",
                        "owner"
                    ],
                    "registered-members": [
                        "none",
                        "view",
                        "download",
                        "edit",
                        "manage"
                    ]
                }
            }
        )
        self.assertDictEqual(
            r_type_perms['map'],
            {
                "perms": {
                    "anonymous": [
                        "view_resourcebase",
                    ],
                    "default": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase"
                    ],
                    "registered-members": [
                        "change_resourcebase_metadata",
                        "delete_resourcebase",
                        "change_resourcebase_permissions",
                        "publish_resourcebase",
                        "change_resourcebase",
                        "view_resourcebase"
                    ]
                },
                "compact": {
                    "anonymous": [
                        "none",
                        "view",
                    ],
                    "default": [
                        "view",
                        "edit",
                        "manage",
                        "owner"
                    ],
                    "registered-members": [
                        "none",
                        "view",
                        "edit",
                        "manage"
                    ]
                }
            }
        )

    def test_get_favorites(self):
        """
        Ensure we get user's favorite resources.
        """
        dataset = Dataset.objects.first()
        url = urljoin(f"{reverse('base-resources-list')}/", 'favorites/')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 403)
        # Authenticated user
        bobby = get_user_model().objects.get(username='bobby')
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        favorite = Favorite.objects.create_favorite(dataset, bobby)
        response = self.client.get(url, format='json')
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.status_code, 200)
        # clean up
        favorite.delete()

    def test_create_and_delete_favorites(self):
        """
        Ensure we can add and remove resources to user's favorite.
        """
        dataset = get_resources_with_perms(get_user_model().objects.get(pk=-1)).first()
        url = urljoin(f"{reverse('base-resources-list')}/", f"{dataset.pk}/favorite/")
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
        dataset = Dataset.objects.first()
        Favorite.objects.create_favorite(dataset, admin)

        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get(
            f"{url}?favorite=true", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        # 1 favorite is saved, so the total should be 1
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(len(response.data['resources']), 1)

    def test_thumbnail_urls(self):
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
        response = self.client.get(f"{url}?type=dataset&title__icontains=CA", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        # response has link to the response
        self.assertTrue('link' in response.data['owners'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 8)

        # Owners Filtering
        response = self.client.get(f"{url}?filter{{username.icontains}}=bobby", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)

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

        # Categories Filtering
        response = self.client.get(f"{url}?filter{{identifier.icontains}}=biota", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)

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

        # Regions Filtering
        response = self.client.get(f"{url}?filter{{name.icontains}}=Africa", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 8)

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

        # Keywords Filtering
        response = self.client.get(f"{url}?filter{{name.icontains}}=Africa", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

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

    def test_rating_resource(self):
        resource = Dataset.objects.first()
        url = reverse('base-resources-ratings', args=[resource.pk])
        data = {
            "rating": 3
        }
        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.json()['rating'], 0)
        self.assertEqual(response.json()['overall_rating'], 0)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

        # Authenticated user
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url)
        self.assertEqual(response.json()['rating'], 0)
        self.assertEqual(response.json()['overall_rating'], 0)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data=data)
        self.assertEqual(response.json()['rating'], 3)
        self.assertEqual(response.json()['overall_rating'], 3.0)
        self.assertEqual(response.status_code, 200)

        # Authenticated user2
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url)
        self.assertEqual(response.json()['rating'], 0)
        self.assertEqual(response.json()['overall_rating'], 3.0)
        self.assertEqual(response.status_code, 200)

        data['rating'] = 1
        response = self.client.post(url, data=data)
        self.assertEqual(response.json()['rating'], 1)
        self.assertEqual(response.json()['overall_rating'], 2.0)
        self.assertEqual(response.status_code, 200)

    def test_set_resource_thumbanil(self):
        re_uuid = "[0-F]{8}-([0-F]{4}-){3}[0-F]{12}"
        resource = Dataset.objects.first()
        url = reverse('base-resources-set_thumbnail', args=[resource.pk])
        data = {"file": "http://localhost:8000/thumb.png"}

        # Anonymous user
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 403)

        # Authenticated user
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['thumbnail_url'], data['file'])
        self.assertEqual(Dataset.objects.get(pk=resource.pk).thumbnail_url, data['file'])
        # set with invalid image url
        data = {"file": "invali url"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ['file is either a file upload, ASCII byte string or a valid image url string'])
        # Test with non image url
        data = {"file": "http://localhost:8000/thumb.txt"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'The url must be of an image with format (png, jpeg or jpg)')

        # using Base64 data as an ASCII byte string
        data['file'] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAABHNCSVQICAgI\
        fAhkiAAAABl0RVh0U29mdHdhcmUAZ25vbWUtc2NyZWVuc2hvdO8Dvz4AAAANSURBVAiZYzAxMfkPAALYAZzx61+bAAAAAElFTkSuQmCC"
        with patch("geonode.base.models.is_monochromatic_image") as _mck:
            _mck.return_value = False
            response = self.client.put(url, data=data, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(re.search(f"dataset-{re_uuid}-thumb-{re_uuid}.png", Dataset.objects.get(pk=resource.pk).thumbnail_url, re.I))
            # File upload
            with patch('PIL.Image.open') as _mck:
                _mck.return_value = test_image
                # rest thumbnail_url to None
                resource.thumbnail_url = None
                resource.save()
                self.assertEqual(Dataset.objects.get(pk=resource.pk).thumbnail_url, None)
                f = SimpleUploadedFile('test_image.png', BytesIO(test_image.tobytes()).read(), 'image/png')
                response = self.client.put(url, data={"file": f})
                self.assertIsNotNone(re.search(f"dataset-{re_uuid}-thumb-{re_uuid}.png", Dataset.objects.get(pk=resource.pk).thumbnail_url, re.I))
                self.assertEqual(response.status_code, 200)

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
        dataset_id = Dataset.objects.first().resourcebase_ptr_id
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
        self.assertTrue(self.client.login(username='admin', password='admin'))
        dataset_id = Dataset.objects.first().resourcebase_ptr_id
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

    def test_manager_can_edit_map(self):
        """
        REST API must not forbid saving maps and apps to non-admin and non-owners.
        """
        from uuid import uuid1
        from geonode.maps.models import Map
        _map = Map.objects.filter(uuid__isnull=False, owner__username='admin').first()
        if not len(_map.uuid):
            _map.uuid = str(uuid1)
            _map.save()
        resource = ResourceBase.objects.filter(uuid=_map.uuid).first()
        bobby = get_user_model().objects.get(username='bobby')

        # Add perms to Bobby
        resource_perm_spec_patch = {
            'users': [
                {
                    'id': bobby.id,
                    'username': bobby.username,
                    'first_name': bobby.first_name,
                    'last_name': bobby.last_name,
                    'avatar': '',
                    'permissions': 'manage'
                }
            ]
        }

        # Patch the resource perms
        self.assertTrue(self.client.login(username='admin', password='admin'))
        data = f"uuid={resource.uuid}&permissions={json.dumps(resource_perm_spec_patch)}"
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'permissions')
        response = self.client.patch(set_perms_url, data=data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        status_url = response.data.get('status_url')
        _counter = 0
        while _counter < 100 and status != ExecutionRequest.STATUS_FINISHED and status != ExecutionRequest.STATUS_FAILED:
            response = self.client.get(status_url)
            status = response.data.get('status')
            sleep(3.0)
            _counter += 1
            logger.error(f"[{_counter}] GET {status_url} ----> {response.data}")
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        get_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': _map.get_self_resource().pk})}/", 'permissions')
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertEqual(
            resource_perm_spec,
            {
                'users': [
                    {
                        'id': bobby.id,
                        'username': 'bobby',
                        'first_name': 'bobby',
                        'last_name': '',
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'manage',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    {
                        'id': 1,
                        'username': 'admin',
                        'first_name': 'admin',
                        'last_name': '',
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'permissions': 'owner',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'view'
                    },
                    {
                        'id': 2,
                        'title': 'Registered Members',
                        'name': 'registered-members',
                        'permissions': 'none'
                    }
                ]
            }
        )

        # Fetch the map perms as user "bobby"
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertEqual(
            resource_perm_spec,
            {
                'users': [
                    {
                        'id': 1,
                        'username': 'admin',
                        'first_name': 'admin',
                        'last_name': '',
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'permissions': 'owner',
                        'is_staff': True,
                        'is_superuser': True,
                    },
                    {
                        'id': bobby.id,
                        'username': 'bobby',
                        'first_name': 'bobby',
                        'last_name': '',
                        'avatar': 'https://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e/?s=240',
                        'permissions': 'manage',
                        'is_staff': False,
                        'is_superuser': False,
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'view'
                    },
                    {
                        'id': 2,
                        'title': 'Registered Members',
                        'name': 'registered-members',
                        'permissions': 'none'
                    }
                ]
            }
        )
