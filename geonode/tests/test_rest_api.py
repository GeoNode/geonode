#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser, Group

from geonode.api.authorization import GroupAuthorization, GroupProfileAuthorization
from geonode.groups.models import GroupProfile
from geonode.people.models import Profile
from geonode.tests.base import GeoNodeBaseTestSupport


class TestGroupResAuthorization(GeoNodeBaseTestSupport):
    # Group fixture is loaded in base class

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list',
           return_value=Group.objects.exclude(name='anonymous'))
    def test_super_admin_user(self, super_mock):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test', is_staff=True, is_superuser=True)
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupAuthorization().read_list([], mock_bundle)
        self.assertEqual(Group.objects.exclude(name='anonymous').count(), groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list',
           return_value=Group.objects.exclude(name='anonymous'))
    @patch('geonode.people.models.Profile.group_list_all', return_value=[2])
    def test_regular_user_hide_private(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test')
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(2, groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list',
           return_value=Group.objects.exclude(name='anonymous'))
    @patch('geonode.people.models.Profile.group_list_all', return_value=[1])
    def test_regular_user(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test')
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(3, groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list',
           return_value=Group.objects.exclude(name='anonymous'))
    @patch('geonode.people.models.Profile.group_list_all', return_value=[1])
    def test_anonymous_user(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': AnonymousUser()
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(2, groups.count())


class TestGroupProfileResAuthorization(GeoNodeBaseTestSupport):
    # Group fixture is loaded in base class

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list', return_value=GroupProfile.objects.all())
    def test_super_admin_user(self, super_mock):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test', is_staff=True, is_superuser=True)
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupProfileAuthorization().read_list([], mock_bundle)
        self.assertEqual(GroupProfile.objects.all().count(), groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list', return_value=GroupProfile.objects.all())
    @patch('geonode.people.models.Profile.group_list_all', return_value=[2])
    def test_regular_user_hide_private(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test')
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupProfileAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(1, groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list', return_value=GroupProfile.objects.all())
    @patch('geonode.people.models.Profile.group_list_all', return_value=[1])
    def test_regular_user(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': Profile(username='test')
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupProfileAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(2, groups.count())

    @patch('geonode.api.authorization.ApiLockdownAuthorization.read_list', return_value=GroupProfile.objects.all())
    @patch('geonode.people.models.Profile.group_list_all', return_value=[1])
    def test_anonymous_user(self, super_mock, mocked_profile):
        mock_bundle = MagicMock()
        request_mock = MagicMock()
        r_attr = {
            'user': AnonymousUser()
        }
        attrs = {
            'request': request_mock
        }
        request_mock.configure_mock(**r_attr)
        mock_bundle.configure_mock(**attrs)

        groups = GroupProfileAuthorization().read_list(['not_empty_but_fake'], mock_bundle)
        self.assertEqual(1, groups.count())
