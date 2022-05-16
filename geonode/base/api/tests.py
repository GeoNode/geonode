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
import logging

from PIL import Image
from io import BytesIO
from uuid import uuid4
from unittest.mock import patch
from urllib.parse import urljoin

from django.urls import reverse
from django.core.files import File
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from guardian.shortcuts import get_anonymous_user

from geonode import geoserver
from geonode.layers.models import Layer
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.utils import check_ogc_backend, set_resource_default_links
from geonode.favorite.models import Favorite
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.utils import build_absolute_uri
from geonode.thumbs.exceptions import ThumbnailError
from geonode.base.populate_test_data import create_models, create_single_layer
from geonode.security.utils import get_resources_with_perms

from geonode.base.models import (
    CuratedThumbnail,
    ExtraMetadata,
    HierarchicalKeyword,
    Region,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
)

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
        create_models(b'layer')

    def test_groups_list(self):
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
            self.assertEqual(response.data['total'], 7)
            self.assertEqual(len(response.data['group_profiles']), 7)

            # Bobby can access public groups and the ones he is member of
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            priv_1.join(get_user_model().objects.get(username='bobby'))
            url = reverse('group-profiles-list')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data['total'], 6)
            self.assertEqual(len(response.data['group_profiles']), 6)
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

    def test_create_group(self):
        """
        Ensure only Admins can create groups.
        """
        data = {
            "title": "group title",
            "group": 1,
            "slug": "group_title",
            "description": "test",
            "access": "private",
            "categories": []
        }
        try:
            # Anonymous
            url = reverse('group-profiles-list')
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)

            # Group manager
            group = GroupProfile.objects.create(slug="test_group_manager", title="test_group_manager")
            group.join(get_user_model().objects.get(username='norman'), role='manager')
            self.assertTrue(self.client.login(username='norman', password='norman'))
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)

            # Admin
            self.assertTrue(self.client.login(username='admin', password='admin'))
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()['group_profile']['title'], 'group title')
        finally:
            GroupProfile.objects.get(slug='group_title').delete()
            group.delete()

    def test_edit_group(self):
        """
        Ensure only admins and group managers can edit a group.
        """
        group = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        data = {'title': 'new_title'}
        try:
            # Anonymous
            url = f"{reverse('group-profiles-list')}/{group.id}/"
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)

            # Group manager
            group.join(get_user_model().objects.get(username='bobby'), role='manager')
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(GroupProfile.objects.get(id=group.id).title, data['title'])

            # Admin
            self.assertTrue(self.client.login(username='admin', password='admin'))
            response = self.client.patch(url, data={'title': 'admin_title'}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(GroupProfile.objects.get(id=group.id).title, 'admin_title')
        finally:
            group.delete()

    def test_delete_group(self):
        """
        Ensure only admins can delete a group.
        """
        group = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        try:
            # Anonymous
            url = f"{reverse('group-profiles-list')}/{group.id}/"
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 403)

            # Group manager
            group.join(get_user_model().objects.get(username='bobby'), role='manager')
            response = self.client.delete(f"{reverse('group-profiles-list')}/{group.id}/", format='json')
            self.assertEqual(response.status_code, 403)

            # Admin can delete a group
            self.assertTrue(self.client.login(username='admin', password='admin'))
            response = self.client.delete(f"{reverse('group-profiles-list')}/{group.id}/", format='json')
            self.assertEqual(response.status_code, 204)
        finally:
            group.delete()

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
        # Anonymous
        self.assertIsNone(self.client.logout())
        response = self.client.post(url, data={'username': 'new_user_1'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_update_user_profile(self):
        """
        Ensure users cannot update others.
        """
        try:
            user = get_user_model().objects.create_user(
                username='user_test_delete',
                email="user_test_delete@geonode.org",
                password='user')
            url = reverse('users-detail', kwargs={'pk': user.pk})
            data = {'first_name': 'user'}
            # Anonymous
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)
            # Another registered user
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)
            # User self profile
            self.assertTrue(self.client.login(username="user_test_delete", password="user"))
            response = self.client.patch(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)
            # Group manager
            group = GroupProfile.objects.create(slug="test_group_manager", title="test_group_manager")
            group.join(user)
            group.join(get_user_model().objects.get(username='norman'), role='manager')
            self.assertTrue(self.client.login(username='norman', password='norman'))
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(response.status_code, 403)
            # Admin can edit user
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.patch(url, data={'first_name': 'user_admin'}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(get_user_model().objects.get(username='user_test_delete').first_name, 'user_admin')
        finally:
            user.delete()
            group.delete()

    def test_delete_user_profile(self):
        """
        Ensure only admins can delete profiles.
        """
        try:
            user = get_user_model().objects.create_user(
                username='user_test_delete',
                email="user_test_delete@geonode.org",
                password='user')
            url = reverse('users-detail', kwargs={'pk': user.pk})
            # Anonymous can read
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            # Anonymous can't delete user
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 403)
            # Bob can't delete user
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 403)
            # User can not delete self profile
            self.assertTrue(self.client.login(username="user_test_delete", password="user"))
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 403)
            # Admin can delete user
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.delete(url, format='json')
            self.assertEqual(response.status_code, 204)
        finally:
            user.delete()

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
        self.assertEqual(resource.owner.username, 'bobby')
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

    def test_write_resources(self):
        """
        Ensure we can perform write oprtation afainst the Resource Bases.
        """
        url = reverse('base-resources-list')
        # Check user permissions
        for resource_type in ['layer', 'document', 'map']:
            resource = ResourceBase.objects.filter(owner__username='bobby', resource_type=resource_type).first()
            self.assertEqual(resource.owner.username, 'bobby')
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.get(f"{url}/{resource.id}/", format='json')
            self.assertTrue('change_resourcebase' in list(response.data['resource']['perms']))
            self.assertEqual(True, response.data['resource']['is_published'], response.data['resource']['is_published'])
            data = {
                "title": "Foo Title",
                "abstract": "Foo Abstract",
                "attribution": "Foo Attribution",
                "doi": "321-12345-987654321",
                "is_published": False
            }
            response = self.client.patch(f"{url}/{resource.id}/", data=data, format='json')
            self.assertEqual(response.status_code, 200, response.status_code)
            response = self.client.get(f"{url}/{resource.id}/", format='json')
            self.assertEqual('Foo Title', response.data['resource']['title'], response.data['resource']['title'])
            self.assertEqual('Foo Abstract', response.data['resource']['abstract'], response.data['resource']['abstract'])
            self.assertEqual('Foo Attribution', response.data['resource']['attribution'], response.data['resource']['attribution'])
            self.assertEqual('321-12345-987654321', response.data['resource']['doi'], response.data['resource']['doi'])
            self.assertEqual(False, response.data['resource']['is_published'], response.data['resource']['is_published'])

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

        resource = ResourceBase.objects.filter(owner__username='bobby', resource_type='layer').first()
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'set_perms/')
        get_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'get_perms/')

        url = reverse('base-resources-detail', kwargs={'pk': resource.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['resource']['pk']), int(resource.pk))

        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertTrue('bobby' in resource_perm_spec['users'], resource_perm_spec)
        self.assertFalse('norman' in resource_perm_spec['users'], resource_perm_spec)

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
        r_types = [item for item in response.data['resource_types']]
        r_type_names = [r_type['name'] for r_type in r_types]
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
        self.assertEqual(response.data['total'], len(HierarchicalKeyword.resource_keywords_tree(None)))

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        admin = get_user_model().objects.get(username='admin')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], len(HierarchicalKeyword.resource_keywords_tree(admin)))
        # response has link to the response
        if response.data['total'] > 0:
            self.assertTrue('link' in response.data['keywords'][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        bobby = get_user_model().objects.get(username='bobby')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], len(HierarchicalKeyword.resource_keywords_tree(bobby)))

        # Keywords Filtering
        response = self.client.get(f"{url}?filter{{name.icontains}}=Africa", format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

        # Testing Hierarchical Keywords tree
        try:
            HierarchicalKeyword.objects.filter(slug__in=['a', 'a1', 'a2', 'b', 'b1']).delete()
            HierarchicalKeyword.add_root(name='a')
            HierarchicalKeyword.add_root(name='b')
            a = HierarchicalKeyword.objects.get(slug='a')
            b = HierarchicalKeyword.objects.get(slug='b')
            a.add_child(name='a1')
            a.add_child(name='a2')
            b.add_child(name='b1')
            resources = ResourceBase.objects.filter(owner__username='bobby')
            res1 = resources.first()
            res2 = resources.last()
            self.assertNotEqual(res1, res2)
            res1.keywords.add(HierarchicalKeyword.objects.get(slug='a1'))
            res1.keywords.add(HierarchicalKeyword.objects.get(slug='a2'))
            res2.keywords.add(HierarchicalKeyword.objects.get(slug='b1'))
            resource_keywords = HierarchicalKeyword.resource_keywords_tree(bobby)
            logger.error(resource_keywords)

            """
            Final api outcome will be something like
            [
                {
                    'id': 116,
                    'text': 'a',
                    'href': 'a',
                    'tags': [],
                    'nodes': [
                        {
                            'id': 118,
                            'text': 'a1',
                            'href': 'a1',
                            'tags': [1]
                        },
                        {
                            'id': 119,
                            'text': 'a2',
                            'href': 'a2',
                            'tags': [1]
                        }
                    ]
                },
                {
                    'id': 117,
                    'text': 'b',
                    'href': 'b',
                    'tags': [],
                    'nodes': [
                        {
                            'id': 120,
                            'text': 'b1',
                            'href': 'b1',
                            'tags': [1]
                        }
                    ]
                },
                ...
            ]
            """
            url = reverse('keywords-list')
            # Authenticated user
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            for _kw in response.data["keywords"]:
                if _kw.get('href') in ['a', 'b']:
                    self.assertListEqual(_kw.get('tags'), [], _kw.get('tags'))
                    self.assertEqual(len(_kw.get('nodes')), 2)
                    for _kw_child in _kw.get('nodes'):
                        self.assertEqual(_kw_child.get('tags')[0], 1)
        finally:
            HierarchicalKeyword.objects.filter(slug__in=['a', 'a1', 'a2', 'b', 'b1']).delete()

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
        self.assertTrue(self.client.login(username='admin', password='admin'))
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


class TestExtraMetadataBaseApi(GeoNodeBaseTestSupport):
    def setUp(self):
        self.layer = create_single_layer('single_layer')
        self.metadata = {
            "filter_header": "Foo Filter header",
            "field_name": "metadata-name",
            "field_label": "this is the help text",
            "field_value": "foo"
        }
        m = ExtraMetadata.objects.create(
            resource=self.layer,
            metadata=self.metadata
        )
        self.layer.metadata.add(m)
        self.mdata = ExtraMetadata.objects.first()

    def test_get_will_return_the_list_of_extra_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        response = self.client.get(url, content_type='application/json')
        self.assertTrue(200, response.status_code)
        expected = [
            {**{"id": self.mdata.id}, **self.metadata}
        ]
        self.assertEqual(expected, response.json())

    def test_put_will_update_the_whole_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        input_metadata = {
            "id": self.mdata.id,
            "filter_header": "Foo Filter header",
            "field_name": "metadata-updated",
            "field_label": "this is the help text",
            "field_value": "foo"
        }
        response = self.client.put(url, data=[input_metadata], content_type='application/json')
        self.assertTrue(200, response.status_code)
        self.assertEqual([input_metadata], response.json())

    def test_post_will_add_new_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        input_metadata = {
            "filter_header": "Foo Filter header",
            "field_name": "metadata-updated",
            "field_label": "this is the help text",
            "field_value": "foo"
        }
        response = self.client.post(url, data=[input_metadata], content_type='application/json')
        self.assertTrue(201, response.status_code)
        self.assertEqual(2, len(response.json()))

    def test_delete_will_delete_single_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        response = self.client.delete(url, data=[self.mdata.id], content_type='application/json')
        self.assertTrue(200, response.status_code)
        self.assertEqual([], response.json())
