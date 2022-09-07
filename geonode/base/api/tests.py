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

import os
import re
import sys
import json
import logging
import gisdata

from PIL import Image
from io import BytesIO
from time import sleep
from uuid import uuid4
from unittest.mock import patch
from urllib.parse import urljoin

from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from guardian.shortcuts import get_anonymous_user
from geonode.maps.models import Map
from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.base import enumerations
from geonode.groups.models import GroupProfile
from geonode.thumbs.exceptions import ThumbnailError
from geonode.layers.utils import get_files
from geonode.base.models import (
    HierarchicalKeyword,
    Region,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
    ExtraMetadata
)

from geonode.layers.models import Dataset
from geonode.favorite.models import Favorite
from geonode.documents.models import Document
from geonode.geoapps.models import GeoApp
from geonode.utils import build_absolute_uri
from geonode.resource.api.tasks import ExecutionRequest
from geonode.base.populate_test_data import create_models, create_single_dataset
from geonode.resource.api.tasks import resouce_service_dispatcher

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
        self.assertEqual(response.status_code, 403)
        # Authorized
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data['total'], 9)
        self.assertEqual(len(response.data['users']), 9)
        # response has link to the response
        self.assertTrue('link' in response.data['users'][0].keys())

        url = reverse('users-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data['user']['username'], 'admin')
        self.assertIsNotNone(response.data['user']['avatar'])

        # anonymous users are not in contributors group
        self.assertNotIn('add_resource', get_user_model().objects.get(id=-1).perms)

        try:
            # Bobby
            group_user = get_user_model().objects.create(username='group_user')
            bobby = get_user_model().objects.filter(username='bobby').get()
            groupx = GroupProfile.objects.create(slug="groupx", title="groupx", access="private")
            groupx.join(bobby)
            groupx.join(group_user)
            self.assertTrue(self.client.login(username='bobby', password='bob'))
            url = reverse('users-detail', kwargs={'pk': group_user.id})
            # Bobby can access other users details from same group
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)

            # Bobby can see himself in the list
            url = reverse('users-list')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertIn('"username": "bobby"', json.dumps(response.data['users']))

            # Bobby can access its own details
            url = reverse('users-detail', kwargs={'pk': bobby.id})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['user']['username'], 'bobby')
            self.assertIsNotNone(response.data['user']['avatar'])
            # default contributor group_perm is returned in perms
            self.assertIn('add_resource', response.data['user']['perms'])

            # Bobby can't access other users perms list
            url = reverse('users-detail', kwargs={'pk': group_user.id})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['user']['username'], 'group_user')
            self.assertIsNotNone(response.data['user']['avatar'])
            # default contributor group_perm is returned in perms
            self.assertNotIn('perms', response.data['user'])
        finally:
            group_user.delete()
            groupx.delete()

    def test_get_self_user_details_outside_registered_member(self):
        try:
            user = get_user_model().objects.create_user(
                username='non_registered_member',
                email="non_registered_member@geonode.org",
                password='password')
            # remove user from registered members group
            reg_mem_group = Group.objects.get(name='registered-members')
            reg_mem_group.user_set.remove(user)

            url = reverse('users-detail', kwargs={'pk': user.pk})

            self.assertTrue(self.client.login(username="non_registered_member", password="password"))
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
        finally:
            user.delete()

    def test_get_self_user_details_with_no_group(self):
        try:
            user = get_user_model().objects.create_user(
                username='no_group_member',
                email="no_group_member@geonode.org",
                password='password')
            # remove user from all groups
            user.groups.clear()

            url = reverse('users-detail', kwargs={'pk': user.pk})

            self.assertTrue(self.client.login(username="no_group_member", password="password"))
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
        finally:
            user.delete()

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
            # Anonymous can't read
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 403)
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
        response.data['resources'][0].get('executions')
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
        self.assertEqual(resource.owner.username, 'bobby')
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
        # Check executions are returned when deffered
        # all resources
        response = self.client.get(f'{url}?include[]=executions', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['resources'][0].get('executions'))
        # specific resource
        exec_req = ExecutionRequest.objects.create(
            user=resource.owner,
            func_name='test',
            geonode_resource=resource,
            input_params={
                "uuid": resource.uuid,
                "owner": resource.owner.username,
                "resource_type": resource.resource_type,
                "defaults": f"{{\"owner\":\"{resource.owner.username}\"}}"
            }
        )
        expected_executions_results = [{
            'exec_id': exec_req.exec_id,
            'user': exec_req.user.username,
            'status': exec_req.status,
            'func_name': exec_req.func_name,
            'created': exec_req.created,
            'finished': exec_req.finished,
            'last_updated': exec_req.last_updated,
            'input_params': exec_req.input_params,
            'output_params': exec_req.output_params,
            'status_url':
                urljoin(
                    settings.SITEURL,
                    reverse('rs-execution-status', kwargs={'execution_id': exec_req.exec_id})
                )
        }]
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(f'{url}/{resource.id}?include[]=executions', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['resource'].get('executions'))
        self.assertEqual(response.data['resource'].get('executions'), expected_executions_results)

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
        for resource_type in ['dataset', 'document', 'map']:
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
                "is_published": False  # this is a read-only field so should not updated
            }
            response = self.client.patch(f"{url}/{resource.id}/", data=data, format='json')
            self.assertEqual(response.status_code, 200, response.status_code)
            response = self.client.get(f"{url}/{resource.id}/", format='json')
            self.assertEqual('Foo Title', response.data['resource']['title'], response.data['resource']['title'])
            self.assertEqual('Foo Abstract', response.data['resource']['abstract'], response.data['resource']['abstract'])
            self.assertEqual('Foo Attribution', response.data['resource']['attribution'], response.data['resource']['attribution'])
            self.assertEqual('321-12345-987654321', response.data['resource']['doi'], response.data['resource']['doi'])
            self.assertEqual(True, response.data['resource']['is_published'], response.data['resource']['is_published'])

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
            "uuid": resource.uuid,
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
        response = self.client.patch(set_perms_url, data=resource_perm_spec_patch, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        resp_js = json.loads(response.content.decode('utf-8'))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode('utf-8'))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
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
            "uuid": resource.uuid,
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

        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        resp_js = json.loads(response.content.decode('utf-8'))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode('utf-8'))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
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
        resource_perm_spec['uuid'] = resource.uuid
        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
        self.assertEqual(response.status_code, 403)
        # login resourse owner
        # get perms
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(get_perms_url, format='json')
        self.assertEqual(response.status_code, 200)
        # set perms
        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
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
        _pp_e = {
            "perms": {
                "anonymous": [
                    "view_resourcebase",
                    "download_resourcebase"
                ],
                "default": [
                    "delete_resourcebase",
                    "view_resourcebase",
                    "change_resourcebase_metadata",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_dataset_data",
                    "change_dataset_style"
                ],
                "registered-members": [
                    "delete_resourcebase",
                    "view_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_dataset_data",
                    "change_dataset_style"
                ]
            },
            "compact": {
                "anonymous": [
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View"
                    },
                    {
                        "name": "download",
                        "label": "Download"
                    }
                ],
                "default": [
                    {
                        "name": "view",
                        "label": "View"
                    },
                    {
                        "name": "download",
                        "label": "Download"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    }
                ],
                "registered-members": [
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View"
                    },
                    {
                        "name": "download",
                        "label": "Download"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    }
                ]
            }
        }
        self.assertListEqual(
            list(r_type_perms['dataset'].keys()),
            list(_pp_e.keys()),
            f"dataset : {list(r_type_perms['dataset'].keys())}")
        for _key in r_type_perms['dataset']['perms'].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms['dataset']['perms'].get(_key)))),
                sorted(list(set(_pp_e['perms'].get(_key)))),
                f"{_key} : {list(set(r_type_perms['dataset']['perms'].get(_key)))}")
        for _key in r_type_perms['dataset']['compact'].keys():
            self.assertListEqual(
                r_type_perms['dataset']['compact'].get(_key),
                _pp_e['compact'].get(_key),
                f"{_key} : {r_type_perms['dataset']['compact'].get(_key)}")

        _pp_e = {
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
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View Metadata"
                    },
                    {
                        "name": "download",
                        "label": "View and Download"
                    }
                ],
                "default": [
                    {
                        "name": "view",
                        "label": "View Metadata"
                    },
                    {
                        "name": "download",
                        "label": "View and Download"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    }
                ],
                "registered-members": [
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View Metadata"
                    },
                    {
                        "name": "download",
                        "label": "View and Download"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    }
                ]
            }
        }
        self.assertListEqual(
            list(r_type_perms['document'].keys()),
            list(_pp_e.keys()),
            f"document : {list(r_type_perms['document'].keys())}")
        for _key in r_type_perms['document']['perms'].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms['document']['perms'].get(_key)))),
                sorted(list(set(_pp_e['perms'].get(_key)))),
                f"{_key} : {list(set(r_type_perms['document']['perms'].get(_key)))}")
        for _key in r_type_perms['document']['compact'].keys():
            self.assertListEqual(
                r_type_perms['document']['compact'].get(_key),
                _pp_e['compact'].get(_key),
                f"{_key} : {r_type_perms['document']['compact'].get(_key)}")

        _pp_e = {
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
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View"
                    }
                ],
                "default": [
                    {
                        "name": "view",
                        "label": "View"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    },
                    {
                        "name": "owner",
                        "label": "Owner"
                    }
                ],
                "registered-members": [
                    {
                        "name": "none",
                        "label": "None"
                    },
                    {
                        "name": "view",
                        "label": "View"
                    },
                    {
                        "name": "edit",
                        "label": "Edit"
                    },
                    {
                        "name": "manage",
                        "label": "Manage"
                    }
                ]
            }
        }
        self.assertListEqual(
            list(r_type_perms['map'].keys()),
            list(_pp_e.keys()),
            f"map : {list(r_type_perms['map'].keys())}")
        for _key in r_type_perms['map']['perms'].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms['map']['perms'].get(_key)))),
                sorted(list(set(_pp_e['perms'].get(_key)))),
                f"{_key} : {list(set(r_type_perms['map']['perms'].get(_key)))}")
        for _key in r_type_perms['map']['compact'].keys():
            self.assertListEqual(
                r_type_perms['map']['compact'].get(_key),
                _pp_e['compact'].get(_key),
                f"{_key} : {r_type_perms['map']['compact'].get(_key)}")

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

    def test_get_favorites_is_returned_in_the_base_endpoint_per_user(self):
        """
        Ensure we get user's favorite resources.
        """
        dataset = Dataset.objects.order_by('-last_updated').first()
        url = reverse('base-resources-list')
        bobby = get_user_model().objects.get(username='bobby')

        self.client.login(username='bobby', password='bob')

        favorite = Favorite.objects.create_favorite(dataset, bobby)

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        resource_have_tag = [r.get('favorite', False) for r in response.json().get("resources", {})]

        # check that there is at last 1 favorite for the user
        self.assertTrue(any(resource_have_tag))
        # clean up
        favorite.delete()

        self.client.login(username='admin', password='admin')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        resource_have_tag = [r.get('favorite', False) for r in response.json().get("resources", {})]
        # the admin should not have any favorite assigned to him
        self.assertFalse(all(resource_have_tag))

    def test_get_favorites_is_returned_in_the_base_endpoint(self):
        """
        Ensure we get user's favorite resources.
        """
        url = reverse('base-resources-list')

        self.assertTrue(self.client.login(username='bobby', password='bob'))
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        resource_have_tag = ['favorite' in r.keys() for r in response.json().get("resources", {})]
        self.assertTrue(all(resource_have_tag))

    def test_create_and_delete_favorites(self):
        """
        Ensure we can add and remove resources to user's favorite.
        """
        bobby = get_user_model().objects.get(username='bobby')
        dataset = create_single_dataset(name="test_dataset_for_fav", owner=bobby)
        dataset.set_permissions(
            {'users': {
                "bobby": ['base.add_resourcebase']
            }
            }
        )
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
        dataset.delete()

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

    def test_search_resources_with_favorite_true_with_geoapps_icluded(self):
        url = reverse('base-resources-list')
        # Admin
        admin = get_user_model().objects.get(username='admin')
        try:
            geo_app = GeoApp.objects.create(
                title="Test GeoApp Favorite",
                owner=admin,
                resource_type="geostory"
            )
            Favorite.objects.create_favorite(geo_app, admin)

            self.assertTrue(self.client.login(username='admin', password='admin'))

            response = self.client.get(
                f"{url}?favorite=true", format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['total'], 1)
            self.assertEqual(len(response.data['resources']), 1)
        finally:
            geo_app.delete()

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

    def test_regions_with_resources(self):
        """
        Ensure we can access the list of regions.
        """
        self.assertTrue(self.client.login(username='admin', password='admin'))
        url = reverse('regions-list')
        response = self.client.get(f"{url}?with_resources=True", format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)

        self.assertTrue(self.client.login(username='admin', password='admin'))
        url = reverse('regions-list')
        response = self.client.get(f"{url}?with_resources=False", format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], Region.objects.count())

        self.assertTrue(self.client.login(username='admin', password='admin'))
        url = reverse('regions-list')
        response = self.client.get(f"{url}", format='json')

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

    def test_rating_resource(self):
        resource = Dataset.objects.first()
        url = reverse('base-resources-ratings', args=[resource.pk])
        resource.set_permissions(
            {'users': {
                get_anonymous_user().username: ['base.view_resourcebase'],
                "bobby": ['base.add_resourcebase']
            }
            }
        )
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

    def test_set_resource_thumbnail(self):
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
        expected = {
            'success': False,
            'errors': ['file is either a file upload, ASCII byte string or a valid image url string'],
            'code': 'invalid'
        }
        self.assertEqual(response.json(), expected)
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
            "success": False,
            "errors": ["Authentication credentials were not provided."],
            "code": "not_authenticated",
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
        from geonode.maps.models import Map
        _map = Map.objects.filter(uuid__isnull=False, owner__username='admin').first()
        if not len(_map.uuid):
            _map.uuid = str(uuid4())
            _map.save()
        resource = ResourceBase.objects.filter(uuid=_map.uuid).first()
        bobby = get_user_model().objects.get(username='bobby')

        # Add perms to Bobby
        resource_perm_spec_patch = {
            'uuid': resource.uuid,
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
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'permissions')
        response = self.client.patch(set_perms_url, data=resource_perm_spec_patch, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('status'))
        self.assertIsNotNone(response.data.get('status_url'))
        status = response.data.get('status')
        resp_js = json.loads(response.content.decode('utf-8'))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode('utf-8'))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        # Test "bobby" can access the "permissions" endpoint
        resource_service_permissions_url = reverse('base-resources-perms-spec', kwargs={'pk': resource.pk})
        response = self.client.get(resource_service_permissions_url, format='json')
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
                        'is_superuser': False,
                        'is_staff': False
                    },
                    {
                        'id': 1,
                        'username': 'admin',
                        'first_name': 'admin',
                        'last_name': '',
                        'avatar': 'https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240',
                        'permissions': 'owner',
                        'is_superuser': True,
                        'is_staff': True
                    }
                ],
                'organizations': [],
                'groups': [
                    {
                        'id': 3,
                        'title': 'anonymous',
                        'name': 'anonymous',
                        'permissions': 'view'},
                    {
                        'id': 2,
                        'title': 'Registered Members',
                        'name': 'registered-members',
                        'permissions': 'none'
                    }
                ]
            },
            resource_perm_spec
        )

        # Test "bobby" can manage the resource permissions
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
            },
            resource_perm_spec
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
            },
            resource_perm_spec
        )

    def test_resource_service_copy(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        files_as_dict, _ = get_files(files)
        resource = Dataset.objects.create(
            owner=get_user_model().objects.get(username='admin'),
            name='test_copy',
            store='geonode_data',
            subtype="vector",
            alternate="geonode:test_copy",
            uuid=str(uuid4()),
            files=list(files_as_dict.values())
        )
        bobby = get_user_model().objects.get(username='bobby')
        copy_url = reverse('base-resources-resource-service-copy', kwargs={'pk': resource.pk})
        response = self.client.put(copy_url, data={'title': 'cloned_resource'})
        self.assertEqual(response.status_code, 403)
        # set perms to enable user clone resource
        self.assertTrue(self.client.login(username="admin", password="admin"))
        perm_spec = {
            "uuid": resource.uuid,
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
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", 'permissions')

        response = self.client.patch(set_perms_url, data=perm_spec, format="json")
        self.assertEqual(response.status_code, 200)
        # clone resource
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.put(copy_url)
        self.assertEqual(response.status_code, 200)
        cloned_resource = Dataset.objects.last()
        self.assertEqual(cloned_resource.owner.username, 'admin')
        # clone dataset with invalid file
        resource.files = ['/path/invalid_file.wrong']
        resource.save()
        response = self.client.put(copy_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Resource can not be cloned.')
        # clone dataset with no files
        resource.files = []
        resource.save()
        response = self.client.put(copy_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Resource can not be cloned.')
        # clean
        resource.delete()

    def test_resource_service_copy_with_perms_dataset(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        files_as_dict, _ = get_files(files)
        resource = Dataset.objects.create(
            owner=get_user_model().objects.get(username='admin'),
            name='test_copy',
            store='geonode_data',
            subtype="vector",
            alternate="geonode:test_copy",
            resource_type="dataset",
            uuid=str(uuid4()),
            files=list(files_as_dict.values())
        )
        self._assertCloningWithPerms(resource)

    def test_resource_service_copy_with_perms_doc(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        files_as_dict, _ = get_files(files)
        resource = Document.objects.create(
            owner=get_user_model().objects.get(username='admin'),
            subtype="vector",
            alternate="geonode:test_copy",
            resource_type="document",
            uuid=str(uuid4()),
            files=list(files_as_dict.values())
        )

        self._assertCloningWithPerms(resource)

    def test_resource_service_copy_with_perms_map(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        files_as_dict, _ = get_files(files)
        resource = Document.objects.create(
            owner=get_user_model().objects.get(username='admin'),
            alternate="geonode:test_copy",
            resource_type="map",
            uuid=str(uuid4()),
            files=list(files_as_dict.values())
        )

        self._assertCloningWithPerms(resource)

    def _assertCloningWithPerms(self, resource):
        # login as bobby
        self.assertTrue(self.client.login(username="bobby", password="bob"))

        # bobby cannot copy the resource since he doesnt have all the perms needed
        _perms = {
            'users': {
                "bobby": ['base.add_resourcebase']
            },
            "groups": {
                "anonymous": []
            }
        }
        resource.set_permissions(_perms)
        copy_url = reverse('base-resources-resource-service-copy', kwargs={'pk': resource.pk})
        response = self.client.put(copy_url, data={'title': 'cloned_resource'})
        self.assertEqual(response.status_code, 403)
        # set perms to enable user clone resource
        # bobby can copy the resource since he has all the perms needed
        _perms = {
            'users': {
                "bobby": ['base.add_resourcebase', 'base.download_resourcebase']
            },
            "groups": {
                "anonymous": ["base.view_resourcebase", "base.download_resourcebae"]
            }
        }
        resource.set_permissions(_perms)
        copy_url = reverse('base-resources-resource-service-copy', kwargs={'pk': resource.pk})
        response = self.client.put(copy_url, data={'title': 'cloned_resource'})
        self.assertEqual(response.status_code, 200)
        resource.delete()

    def test_base_resources_return_download_link_if_document(self):
        """
        Ensure we can access the Resource Base list.
        """
        doc = Document.objects.first()

        # From resource base API
        url = reverse('base-resources-detail', args=[doc.id])
        response = self.client.get(url, format='json')
        download_url = response.json().get('resource').get('download_url')
        self.assertEqual(build_absolute_uri(doc.download_url), download_url)

        # from documents api
        url = reverse('documents-detail', args=[doc.id])
        download_url = response.json().get('resource').get('download_url')
        self.assertEqual(build_absolute_uri(doc.download_url), download_url)

    def test_base_resources_return_download_link_if_dataset(self):
        """
        Ensure we can access the Resource Base list.
        """
        _dataset = Dataset.objects.first()

        # From resource base API
        url = reverse('base-resources-detail', args=[_dataset.id])
        response = self.client.get(url, format='json')
        download_url = response.json().get('resource').get('download_url')
        self.assertEqual(_dataset.download_url, download_url)

        # from dataset api
        url = reverse('datasets-detail', args=[_dataset.id])
        download_url = response.json().get('resource').get('download_url')
        self.assertEqual(_dataset.download_url, download_url)

    def test_base_resources_dont_return_download_link_if_map(self):
        """
        Ensure we can access the Resource Base list.
        """
        _map = Map.objects.first()
        # From resource base API
        url = reverse('base-resources-detail', args=[_map.id])
        response = self.client.get(url, format='json')
        download_url = response.json().get('resource').get('download_url', None)
        self.assertIsNone(download_url)

        # from maps api
        url = reverse('maps-detail', args=[_map.id])
        download_url = response.json().get('resource').get('download_url')
        self.assertIsNone(download_url)


class TestExtraMetadataBaseApi(GeoNodeBaseTestSupport):
    def setUp(self):
        self.layer = create_single_dataset('single_layer')
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

    def test_user_without_view_perms_cannot_see_the_endpoint(self):
        from geonode.resource.manager import resource_manager

        self.client.login(username='bobby', password='bob')
        resource_manager.remove_permissions(self.layer.uuid, instance=self.layer.get_self_resource())
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        response = self.client.get(url, content_type='application/json')
        self.assertTrue(403, response.status_code)

        perm_spec = {"users": {"bobby": ['view_resourcebase']}, "groups": {}}
        self.layer.set_permissions(perm_spec)
        url = reverse('base-resources-extra-metadata', args=[self.layer.id])
        response = self.client.get(url, content_type='application/json')
        self.assertTrue(200, response.status_code)
