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
from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from geonode.api.v3.pagination import V3Pagination
from geonode.api.v3.serializers import CONTEXT_KEY, FieldSelectionModelSerializer
from geonode.api.v3.urls import router


class _GroupSerializer(FieldSelectionModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")


class FieldSelectionSerializerTest(SimpleTestCase):
    def test_available_field_names_ignores_narrowing(self):
        self.assertEqual(_GroupSerializer.available_field_names(), {"id", "name"})

    def test_no_narrowing_returns_all_fields(self):
        self.assertEqual(set(_GroupSerializer().get_fields()), {"id", "name"})

    def test_only_fields_kwarg_narrows_output(self):
        serializer = _GroupSerializer(Group(id=1, name="x"), only_fields={"id"})
        self.assertEqual(set(serializer.data), {"id"})

    def test_context_narrows_output(self):
        serializer = _GroupSerializer(Group(id=1, name="x"), context={CONTEXT_KEY: {"name"}})
        self.assertEqual(set(serializer.data), {"name"})

    def test_kwarg_takes_precedence_over_context(self):
        serializer = _GroupSerializer(
            Group(id=1, name="x"),
            only_fields={"id"},
            context={CONTEXT_KEY: {"name"}},
        )
        self.assertEqual(set(serializer.data), {"id"})


class V3PaginationTest(SimpleTestCase):
    def test_page_size_is_bounded(self):
        """v2 leaves MAX_PAGE_SIZE unset; v3 must not."""
        self.assertIsNotNone(V3Pagination.max_page_size)
        self.assertGreater(V3Pagination.max_page_size, 0)
        self.assertEqual(V3Pagination.page_size_query_param, "page_size")


class V3RouterTest(SimpleTestCase):
    def test_trailing_slash_is_required(self):
        self.assertEqual(router.trailing_slash, "/")

    def test_every_registered_viewset_declares_permission_classes(self):
        """REST_FRAMEWORK sets no DEFAULT_PERMISSION_CLASSES, so an omission is world-writable.

        Nothing is registered yet in this bootstrap-only skeleton, so this passes
        trivially today -- it exists as a standing guard for when the first
        resource viewset is registered.
        """
        offenders = []
        for prefix, viewset, _basename in router.registry:
            declared = viewset.__dict__.get("permission_classes")
            if not declared:
                # inherited is fine, as long as it is not DRF's AllowAny fallback
                declared = getattr(viewset, "permission_classes", None)
            if not declared or list(declared) == [AllowAny]:
                offenders.append(f"{prefix} -> {viewset.__name__}")
        self.assertEqual(offenders, [], f"v3 viewsets without explicit permission_classes: {offenders}")


class V3RootTest(TestCase):
    def test_root_is_reachable(self):
        response = APIClient().get(reverse("api_v3:api-root"))
        self.assertEqual(response.status_code, 200)
