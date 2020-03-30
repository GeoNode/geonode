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

from geonode.documents.models import Document
from geonode.people.models import Profile
from geonode.tests.base import GeoNodeBaseTestSupport
from django.conf import settings


class ResourceBaseSearchTest(GeoNodeBaseTestSupport):

    def setUp(self):
        self.p = Profile.objects.create(username='test')
        self.d1 = Document.objects.create(title='word', purpose='this is a test', abstract='a brief document about...',
                                          owner=self.p)
        self.d1 = Document.objects.create(title='a word', purpose='this is a test',
                                          abstract='a brief document about...',
                                          owner=self.p)

    def test_or_search(self):
        url = f'{settings.SITEURL}api/base/?title__icontains=word&abstract__icontains=word&\
        purpose__icontains=word&f_method=or'
        self.client.force_login(self.p)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json().get('objects')), 2)

    def test_and_search(self):
        url = f'{settings.SITEURL}api/base/?title__icontains=a&abstract__icontains=a&purpose__icontains=a'
        self.client.force_login(self.p)
        response = self.client.get(url)
        self.assertEqual(len(response.json().get('objects')), 1)

    def test_and_empty_search(self):
        url = f'{settings.SITEURL}api/base/?title__icontains=test&abstract__icontains=test&purpose__icontains=test'
        self.client.force_login(self.p)
        response = self.client.get(url)
        self.assertEqual(len(response.json().get('objects')), 0)

    def test_bad_filter(self):
        url = f'{settings.SITEURL}api/base/?edition__icontains=test&abstract__icontains=test&\
        purpose__icontains=test&f_method=or'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
