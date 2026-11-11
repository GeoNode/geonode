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
import os
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import path, reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from geonode.api.v3.schema import V3AutoSchema, exclude_non_v3_endpoints
from drf_spectacular.views import SpectacularAPIView
from rest_framework.decorators import action
from rest_framework.views import APIView

from geonode.api.v3.schema import extend_v3_schema
from geonode.api.v3.tests.utils import CountingGroupSerializer, GroupViewSet
from geonode.api.v3.urls import router
from geonode.api.v3.viewsets import V3GenericViewSet


class PlainView(APIView):
    def get(self, request):
        pass


class _ActionGroupViewSet(GroupViewSet):
    @extend_v3_schema(responses=CountingGroupSerializer(many=True))
    @action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        pass


def generate(patterns=None):
    return SchemaGenerator(patterns=patterns).get_schema(request=None, public=True)


class SchemaScopingTest(SimpleTestCase):
    """Guards the exact failure that caused #14202"""

    def test_default_schema_class_should_not_be_global(self):
        """Setting it globally is what dragged v2's dynamic-rest views into generation"""
        self.assertNotIn("DEFAULT_SCHEMA_CLASS", settings.REST_FRAMEWORK)

    def test_v3_viewsets_should_carry_the_v3_autoschema(self):
        for _prefix, viewset, _basename in router.registry:
            self.assertTrue(issubclass(viewset, V3GenericViewSet), f"{viewset.__name__} is not a V3GenericViewSet")
        self.assertIsInstance(V3GenericViewSet.schema, V3AutoSchema)

    def test_preprocessing_hook_should_drop_non_v3_paths(self):
        _view = GroupViewSet.as_view({"get": "list"})
        endpoints = [
            ("/api/v3/groups/", None, "GET", _view),
            ("/api/v2/resources/", None, "GET", _view),
            ("/api/base/", None, "GET", _view),
        ]
        self.assertListEqual(["/api/v3/groups/"], [_path for _path, *_ in exclude_non_v3_endpoints(endpoints)])

    def test_preprocessing_hook_should_drop_the_schema_views(self):
        """SpectacularAPIView is under /api/v3/ but has no spectacular AutoSchema"""
        endpoints = [
            ("/api/v3/groups/", None, "GET", GroupViewSet.as_view({"get": "list"})),
            ("/api/v3/schema/", None, "GET", SpectacularAPIView.as_view()),
        ]
        self.assertListEqual(["/api/v3/groups/"], [_path for _path, *_ in exclude_non_v3_endpoints(endpoints)])

    def test_preprocessing_hook_should_drop_the_views_without_the_v3_autoschema(self):
        """A plugin view that is not a V3GenericViewSet would break the generation"""
        endpoints = [
            ("/api/v3/groups/", None, "GET", GroupViewSet.as_view({"get": "list"})),
            ("/api/v3/plain/", None, "GET", PlainView.as_view()),
        ]
        with self.assertLogs("geonode.api.v3.schema", level="WARNING") as _log:
            kept = [_path for _path, *_ in exclude_non_v3_endpoints(endpoints)]
        self.assertListEqual(["/api/v3/groups/"], kept)
        self.assertIn("/api/v3/plain/", _log.output[0])

    def test_preprocessing_hook_should_keep_the_actions_documented_with_extend_v3_schema(self):
        _view = _ActionGroupViewSet.as_view({"get": "related"}, **_ActionGroupViewSet.related.kwargs)
        kept = exclude_non_v3_endpoints([("/api/v3/groups/1/related/", None, "GET", _view)])
        self.assertEqual(1, len(kept))


class SchemaGenerationTest(SimpleTestCase):
    def test_metadata_should_reflect_the_v3_conventions(self):
        schema = generate()
        self.assertEqual("GeoNode API v3", schema["info"]["title"])
        self.assertEqual("3.0.0", schema["info"]["version"])
        self.assertTrue(all(_path.endswith("/") for _path in schema["paths"]))

    def test_fields_parameter_should_list_the_available_fields(self):
        schema = generate([path("api/v3/groups/", GroupViewSet.as_view({"get": "list", "post": "create"}))])
        _operation = schema["paths"]["/api/v3/groups/"]
        _fields = next(_param for _param in _operation["get"]["parameters"] if _param["name"] == "fields")
        expected = {
            "in": "query",
            "name": "fields",
            "schema": {"type": "array", "items": {"type": "string", "enum": ["id", "name", "user_count"]}},
            "description": "Subset of the fields to return, unknown names are rejected with 400. Default: id, user_count.",
            "explode": False,
            "style": "form",
        }
        self.assertDictEqual(expected, _fields)
        self.assertNotIn("fields", [_param["name"] for _param in _operation["post"].get("parameters", [])])

    def test_operations_should_carry_their_stability(self):
        schema = generate([path("api/v3/groups/", GroupViewSet.as_view({"get": "list"}))])
        _operation = schema["paths"]["/api/v3/groups/"]["get"]
        self.assertEqual("experimental", _operation["x-stability"])
        self.assertIn("Stability: experimental.", _operation["description"])

    def test_extend_v3_schema_should_document_an_action_as_a_page(self):
        """Plain extend_schema builds on the unset DEFAULT_SCHEMA_CLASS and breaks the generation"""
        schema = generate([path("api/v3/groups/<int:pk>/related/", _ActionGroupViewSet.as_view({"get": "related"}))])
        _operation = schema["paths"]["/api/v3/groups/{id}/related/"]["get"]
        self.assertSetEqual(
            {"fields", "id", "page", "page_size"}, {_param["name"] for _param in _operation["parameters"]}
        )
        _schema = _operation["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual("#/components/schemas/PaginatedCountingGroupList", _schema["$ref"])


class SchemaSnapshotTest(SimpleTestCase):
    def test_schema_should_match_the_committed_snapshot(self):
        """
        Every API change shows up as a diff of openapi.yaml, regenerate it with the default LANGUAGE_CODE
        (model verbose names end up in the descriptions):
        manage.py spectacular --validate --fail-on-warn --file geonode/api/v3/openapi.yaml
        """
        with tempfile.TemporaryDirectory() as _dir:
            _file = os.path.join(_dir, "openapi.yaml")
            call_command("spectacular", "--validate", "--fail-on-warn", "--file", _file)
            with (
                open(_file) as _generated,
                open(os.path.join(os.path.dirname(__file__), "..", "openapi.yaml")) as _snapshot,
            ):
                self.assertEqual(
                    _snapshot.read(), _generated.read(), self.test_schema_should_match_the_committed_snapshot.__doc__
                )


class SchemaEndpointTest(TestCase):
    def test_schema_endpoint_should_serve(self):
        self.assertEqual(200, APIClient().get(reverse("api_v3:schema")).status_code)

    def test_swagger_and_redoc_should_render(self):
        """#14201 was reported as 'redoc is broken', keep both reachable"""
        for name in ("api_v3:swagger-ui", "api_v3:redoc"):
            with self.subTest(view=name):
                self.assertEqual(200, APIClient().get(reverse(name)).status_code)
