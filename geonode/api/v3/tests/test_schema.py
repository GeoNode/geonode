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
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from rest_framework.test import APIClient

from geonode.api.v3.schema import V3AutoSchema, exclude_non_v3_endpoints
from geonode.api.v3.urls import router
from geonode.api.v3.viewsets import V3ModelViewSet


def generate():
    return SchemaGenerator().get_schema(request=None, public=True)


class SchemaScopingTest(SimpleTestCase):
    """Guards the exact failure that caused #14202."""

    def test_no_global_default_schema_class(self):
        """Setting it globally is what dragged v2's dynamic-rest views into generation."""
        from django.conf import settings

        self.assertNotIn("DEFAULT_SCHEMA_CLASS", settings.REST_FRAMEWORK)

    def test_v3_viewsets_carry_the_spectacular_autoschema(self):
        for _prefix, viewset, _basename in router.registry:
            self.assertTrue(issubclass(viewset, V3ModelViewSet), f"{viewset.__name__} is not a V3ModelViewSet")
        self.assertIsInstance(V3ModelViewSet.schema, AutoSchema)
        self.assertIsInstance(V3ModelViewSet.schema, V3AutoSchema)

    def test_preprocessing_hook_drops_non_v3_paths(self):
        endpoints = [
            ("/api/v3/groups/", None, "GET", object()),
            ("/api/v2/resources/", None, "GET", object()),
            ("/api/base/", None, "GET", object()),
        ]
        kept = [path for path, *_ in exclude_non_v3_endpoints(endpoints)]
        self.assertEqual(kept, ["/api/v3/groups/"])

    def test_preprocessing_hook_drops_the_schema_views(self):
        """SpectacularAPIView is under /api/v3/ but has no spectacular AutoSchema."""
        endpoints = [
            ("/api/v3/groups/", None, "GET", object()),
            ("/api/v3/schema/", None, "GET", object()),
        ]
        kept = [path for path, *_ in exclude_non_v3_endpoints(endpoints)]
        self.assertEqual(kept, ["/api/v3/groups/"])


class SchemaGenerationTest(SimpleTestCase):
    """Resource-specific assertions (paths, field types, ...) belong with the
    issue that registers the first resource viewset -- there is none here yet.
    """

    def test_metadata_reflects_the_v3_conventions(self):
        schema = generate()
        self.assertEqual(schema["info"]["title"], "GeoNode API v3")
        self.assertEqual(schema["info"]["version"], "3.0.0")
        # trailing slash is part of the contract, vacuously true with no paths yet
        self.assertTrue(all(p.endswith("/") for p in schema["paths"]))


class SchemaEndpointTest(TestCase):
    def test_schema_endpoint_serves(self):
        response = APIClient().get(reverse("api_v3:schema"))
        self.assertEqual(response.status_code, 200)

    def test_swagger_and_redoc_render(self):
        """#14201 was reported as 'redoc is broken'; keep both reachable."""
        for name in ("api_v3:swagger-ui", "api_v3:redoc"):
            with self.subTest(view=name):
                self.assertEqual(APIClient().get(reverse(name)).status_code, 200)
