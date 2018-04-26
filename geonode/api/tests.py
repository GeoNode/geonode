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
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from tastypie.test import ResourceTestCaseMixin
from django.contrib.auth.models import Group
from geonode.groups.models import GroupProfile

from guardian.shortcuts import get_anonymous_user

from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.base.populate_test_data import all_public
from geonode.layers.models import Layer


class PermissionsApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    def setUp(self):
        super(PermissionsApiTests, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.perm_spec = {"users": {}, "groups": {}}

    def test_layer_get_list_unauth_all_public(self):
        """
        Test that the correct number of layers are returned when the
        client is not logged in and all are public
        """

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layers_get_list_unauth_some_public(self):
        """
        Test that if a layer is not public then not all are returned when the
        client is not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

    def test_layers_get_list_auth_some_public(self):
        """
        Test that if a layer is not public then all are returned if the
        client is not logged in
        """
        self.api_client.client.login(username=self.user, password=self.passwd)
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_list_layer_private_to_one_user(self):
        """
        Test that if a layer is only visible by admin, then does not appear
        in the unauthenticated list nor in the list when logged is as bobby
        """
        perm_spec = {"users": {"admin": ['view_resourcebase']}, "groups": {}}
        layer = Layer.objects.all()[0]
        layer.set_permissions(perm_spec)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        self.api_client.client.login(username='bobby', password='bob')
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

        layer.is_published = False
        layer.save()

        # with resource publishing
        with self.settings(RESOURCE_PUBLISHING=True):
            resp = self.api_client.get(self.list_url)
            self.assertEquals(len(self.deserialize(resp)['objects']), 8)

            self.api_client.client.login(username='bobby', password='bob')
            resp = self.api_client.get(self.list_url)
            self.assertEquals(len(self.deserialize(resp)['objects']), 8)

            self.api_client.client.login(username=self.user, password=self.passwd)
            resp = self.api_client.get(self.list_url)
            self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_detail_unauth_layer_not_public(self):
        """
        Test that layer detail gives 401 when not public and not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)
        self.assertHttpUnauthorized(self.api_client.get(
            self.list_url + str(layer.id) + '/'))

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url + str(layer.id) + '/')
        self.assertValidJSONResponse(resp)

    def test_new_user_has_access_to_old_layers(self):
        """Test that a new user can access the public available layers"""
        from geonode.people.models import Profile
        Profile.objects.create(username='imnew',
                               password='pbkdf2_sha256$12000$UE4gAxckVj4Z$N\
            6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=')
        self.api_client.client.login(username='imnew', password='thepwd')
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)


class SearchApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    """Test the search"""

    def setUp(self):
        super(SearchApiTests, self).setUp()

        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.norman = get_user_model().objects.get(username="norman")
        self.norman.groups.add(Group.objects.get(name='anonymous'))
        self.test_user = get_user_model().objects.get(username='test_user')
        self.test_user.groups.add(Group.objects.get(name='anonymous'))
        self.bar = GroupProfile.objects.get(slug='bar')
        self.anonymous_user = get_anonymous_user()
        self.profiles_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'profiles'})
        self.groups_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'groups'})

    def test_profiles_filters(self):
        """Test profiles filtering"""

        filter_url = self.profiles_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 9)

        filter_url = self.profiles_list_url + '?name__icontains=norm'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.profiles_list_url + '?name__icontains=NoRmAN'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.profiles_list_url + '?name__icontains=bar'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 0)

    def test_groups_filters(self):
        """Test groups filtering"""

        filter_url = self.groups_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.groups_list_url + '?name__icontains=bar'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.groups_list_url + '?name__icontains=BaR'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.groups_list_url + '?name__icontains=foo'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 0)

    def test_category_filters(self):
        """Test category filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = self.list_url + '?category__identifier=location'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        filter_url = self.list_url + \
            '?category__identifier__in=location&category__identifier__in=biota'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 5)

    def test_tag_filters(self):
        """Test keywords filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different keywords
        filter_url = self.list_url + '?keywords__slug=layertagunique'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + \
            '?keywords__slug__in=layertagunique&keywords__slug__in=populartag'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_owner_filters(self):
        """Test owner filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different owners
        filter_url = self.list_url + '?owner__username=user1'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + \
            '?owner__username__in=user1&owner__username__in=foo'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 2)

    def test_title_filter(self):
        """Test title filtering"""

        # check we get the correct layers number returnered filtering on the
        # title
        filter_url = self.list_url + '?title=layer2'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

    def test_date_filter(self):
        """Test date filtering"""

        # check we get the correct layers number returnered filtering on the
        # dates
        step = timedelta(days=60)
        now = datetime.now()
        fstring = '%Y-%m-%d'

        def to_date(val):
            return val.date().strftime(fstring)

        d1 = to_date(now - step)
        filter_url = self.list_url + '?date__exact={}'.format(d1)

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 0)

        d3 = to_date(now - (3 * step))
        filter_url = self.list_url + '?date__gte={}'.format(d3)

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        d4 = to_date(now - (4 * step))
        filter_url = self.list_url + '?date__range={},{}'.format(d4, to_date(now))

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 4)
