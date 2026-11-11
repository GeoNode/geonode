#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory

from geonode.api.v3.exceptions import Conflict, problem_details_handler
from geonode.api.v3.tests.utils import GROUP_PREFIX, GroupViewSet, ReadOnlyGroupViewSet


class ProblemDetailsHandlerTest(SimpleTestCase):
    def test_api_exceptions_should_become_problem_details(self):
        response = problem_details_handler(Conflict("The thing is in use."), {})
        expected = {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "The thing is in use."}
        self.assertDictEqual({**expected, "code": "conflict"}, response.data)

    def test_errors_raised_outside_drf_should_be_left_to_django(self):
        self.assertIsNone(problem_details_handler(ValueError("boom"), {}))


class ProblemDetailsViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def tearDown(self):
        Group.objects.filter(name__startswith=GROUP_PREFIX).delete()

    def test_validation_errors_should_be_kept_by_field(self):
        response = GroupViewSet.as_view({"get": "list"})(self.factory.get("/?fields=foo")).render()
        expected = {
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": "Invalid input.",
            "code": "invalid",
            "errors": {"fields": ["Unknown field(s): foo. Available: id, name, user_count."]},
        }
        self.assertDictEqual(expected, response.data)
        self.assertEqual("application/problem+json", response["Content-Type"])

    def test_authentication_errors_should_be_problem_details(self):
        response = ReadOnlyGroupViewSet.as_view({"get": "list"})(self.factory.get("/")).render()
        expected = {
            "type": "about:blank",
            "title": "Unauthorized",
            "status": 401,
            "detail": "Authentication credentials were not provided.",
            "code": "not_authenticated",
        }
        self.assertDictEqual(expected, response.data)
        # as in v2, so an expired session never pops the browser login dialog
        self.assertEqual(401, response.status_code)
        self.assertNotIn("WWW-Authenticate", response)

    def test_not_found_should_be_problem_details(self):
        response = GroupViewSet.as_view({"get": "retrieve"})(self.factory.get("/"), pk=0).render()
        self.assertEqual(404, response.status_code)
        expected = {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Not found."}
        self.assertDictEqual({**expected, "code": "not_found"}, response.data)

    def test_browsable_api_should_keep_its_html(self):
        request = self.factory.get("/?fields=foo", HTTP_ACCEPT="text/html")
        response = GroupViewSet.as_view({"get": "list"})(request).render()
        self.assertEqual(400, response.status_code)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
