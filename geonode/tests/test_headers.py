#########################################################################
#
# Copyright (C) 2022 OSGeo
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

from django.shortcuts import reverse
from geonode.tests.base import GeoNodeBaseTestSupport

from corsheaders.middleware import ACCESS_CONTROL_ALLOW_ORIGIN


class TestHeaders(GeoNodeBaseTestSupport):

    def test_cors_headers(self):
        categories_url = reverse('categories-list')
        headers = {
                    'HTTP_ORIGIN': "http://127.0.0.1"
                }
        with self.settings(CORS_ALLOW_ALL_ORIGINS=True, CORS_ALLOW_CREDENTIALS=False):
            response = self.client.get(
                categories_url,
                **headers
            )
            self.assertEqual(response[ACCESS_CONTROL_ALLOW_ORIGIN], '*')

        with self.settings(CORS_ALLOW_ALL_ORIGINS=False):
            response = self.client.get(
                categories_url,
                **headers
            )
            self.assertIsNone(getattr(response, 'ACCESS_CONTROL_ALLOW_ORIGIN', None))
