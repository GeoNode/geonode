#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse


class CommandViewTests(APITestCase):
    """
    - Test the Permissions vs Response Status
    - Test the Validations done inside the POST
    """
    def setUp(self):
        self.url = "geonode.commands:enque"
        self.standard_user = get_user_model().objects.create(
            username="test", email="test@test.com"
        )
        self.admin_user, _ = get_user_model().objects.get_or_create(
            username="super", is_staff=True, is_superuser=True
        )


    def test_permissions(self):
        cases = (
            {"user": None, "status": status.HTTP_401_UNAUTHORIZED},
            {"user": self.standard_user, "status": status.HTTP_403_FORBIDDEN},
            {"user": self.admin_user, "status": status.HTTP_200_OK},
        )

        for case in cases:
            with self.subTest(case=case):
                if case.get("user"):
                    self.client.force_authenticate(user=case["user"])
                response = self.client.get(reverse(self.url))
                self.assertEqual(case["status"], response.status_code)
