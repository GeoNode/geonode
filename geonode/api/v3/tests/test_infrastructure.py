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
from unittest.mock import ANY, patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import resolve, reverse
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from geonode.api.v3.constants import CONTEXT_KEY
from geonode.api.v3.pagination import V3Pagination
from geonode.api.v3.tests.utils import (
    GROUP_PREFIX,
    CountingGroupSerializer,
    GroupSerializer,
    GroupViewSet,
    NestingSerializer,
    PlainGroupViewSet,
    ReadOnlyGroupViewSet,
)
from geonode.api.v3.urls import router
from geonode.api.v3.viewsets import V3GenericViewSet


class FieldSelectionSerializerTest(SimpleTestCase):
    def setUp(self):
        self.group = Group(id=7, name="g")
        self.group.related_groups = [Group(id=8, name="h")]

    def test_available_field_names_should_ignore_narrowing(self):
        self.assertSetEqual({"id", "name"}, GroupSerializer.available_field_names())

    def test_available_field_names_should_leave_out_write_only_fields(self):
        """A write-only field never appears in a response, it cannot be selected"""

        class _WriteOnlySerializer(GroupSerializer):
            secret = serializers.CharField(write_only=True)

            class Meta(GroupSerializer.Meta):
                fields = ("id", "name", "secret")

        self.assertSetEqual({"id", "name"}, _WriteOnlySerializer.available_field_names())

    def test_default_field_names_should_read_the_meta(self):
        self.assertSetEqual({"id"}, GroupSerializer.default_field_names())
        self.assertIsNone(NestingSerializer.default_field_names())

    def test_get_fields_should_return_all_fields_without_selection(self):
        self.assertSetEqual({"id", "name"}, set(GroupSerializer().get_fields()))

    def test_only_fields_kwarg_should_narrow_the_output(self):
        self.assertDictEqual({"id": 7}, GroupSerializer(self.group, only_fields={"id"}).data)

    def test_context_should_narrow_the_output(self):
        self.assertDictEqual({"name": "g"}, GroupSerializer(self.group, context={CONTEXT_KEY: {"name"}}).data)

    def test_only_fields_kwarg_should_take_precedence_over_the_context(self):
        serializer = GroupSerializer(self.group, only_fields={"id"}, context={CONTEXT_KEY: {"name"}})
        self.assertDictEqual({"id": 7}, serializer.data)

    def test_root_list_should_narrow_each_item(self):
        serializer = GroupSerializer([self.group], many=True, context={CONTEXT_KEY: {"name"}})
        self.assertListEqual([{"name": "g"}], serializer.data)

    def test_nested_serializers_should_return_their_own_default_fields(self):
        """The requested names belong to the root, the shared context must not narrow nested serializers"""
        serializer = NestingSerializer(self.group, context={CONTEXT_KEY: {"id", "nested", "nested_list"}})
        expected = {"id": 7, "nested": {"id": 7}, "nested_list": [{"id": 8}]}
        self.assertDictEqual(expected, serializer.data)

    def test_nested_serializers_should_return_all_fields_on_writes(self):
        expected = {"id": 7, "name": "g", "nested": {"id": 7, "name": "g"}, "nested_list": [{"id": 8, "name": "h"}]}
        self.assertDictEqual(expected, NestingSerializer(self.group).data)


class FieldSelectionViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.group = Group.objects.create(name=f"{GROUP_PREFIX}one")

    def tearDown(self):
        Group.objects.filter(name__startswith=GROUP_PREFIX).delete()

    def _list(self, query="", viewset=GroupViewSet):
        return viewset.as_view({"get": "list"})(self.factory.get(f"/{query}"))

    def test_list_should_return_the_default_fields(self):
        response = self._list()
        self.assertEqual(200, response.status_code, response.data)
        self.assertListEqual([{"id": self.group.pk, "user_count": 0}], response.data["results"])

    def test_list_should_return_the_requested_fields(self):
        response = self._list("?fields=name")
        self.assertEqual(200, response.status_code, response.data)
        self.assertListEqual([{"name": self.group.name}], response.data["results"])

    def test_list_should_refuse_unknown_fields(self):
        self.assertEqual(400, self._list("?fields=id,foo").status_code)

    def test_options_should_ignore_the_field_selection(self):
        """OPTIONS describes the write serializer, which is never narrowed"""
        response = GroupViewSet.as_view({"get": "list", "post": "create"})(self.factory.options("/?fields=foo"))
        self.assertEqual(200, response.status_code, response.data)
        self.assertSetEqual({"id", "name", "user_count"}, set(response.data["actions"]["POST"]))

    def test_setup_queryset_should_receive_the_selected_fields(self):
        with patch.object(
            CountingGroupSerializer, "setup_queryset", wraps=CountingGroupSerializer.setup_queryset
        ) as _setup:
            self._list("?fields=name")
        _setup.assert_called_with(ANY, {"name"}, ANY)

    def test_fields_should_be_refused_if_the_serializer_cannot_select_them(self):
        """Ignoring ?fields= would silently return every field"""
        self.assertEqual(400, self._list("?fields=id", viewset=PlainGroupViewSet).status_code)
        response = self._list(viewset=PlainGroupViewSet)
        self.assertListEqual([{"id": self.group.pk, "name": self.group.name}], response.data["results"])

    def test_create_should_answer_with_the_read_representation(self):
        """The response is refetched, so the annotations of setup_queryset are there too"""
        request = self.factory.post("/", {"name": f"{GROUP_PREFIX}two"}, format="json")
        response = GroupViewSet.as_view({"post": "create"})(request)
        self.assertEqual(201, response.status_code, response.data)
        _created = Group.objects.get(name=f"{GROUP_PREFIX}two")
        self.assertDictEqual({"id": _created.pk, "user_count": 0}, response.data)

    def test_create_should_validate_the_full_serializer(self):
        response = GroupViewSet.as_view({"post": "create"})(self.factory.post("/", {}, format="json"))
        self.assertEqual(400, response.status_code, response.data)

    def test_update_should_answer_with_the_read_representation(self):
        request = self.factory.patch("/", {"name": f"{GROUP_PREFIX}renamed"}, format="json")
        response = GroupViewSet.as_view({"patch": "partial_update"})(request, pk=self.group.pk)
        self.assertEqual(200, response.status_code, response.data)
        self.assertDictEqual({"id": self.group.pk, "user_count": 0}, response.data)
        self.group.refresh_from_db()
        self.assertEqual(f"{GROUP_PREFIX}renamed", self.group.name)


class V3GenericViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.group = Group.objects.create(name=f"{GROUP_PREFIX}one")
        self.user = get_user_model().objects.create(username=f"{GROUP_PREFIX}user")

    def tearDown(self):
        Group.objects.filter(name__startswith=GROUP_PREFIX).delete()
        self.user.delete()

    def test_permission_classes_should_fail_closed(self):
        self.assertListEqual([IsAuthenticated], V3GenericViewSet.permission_classes)

    def test_anonymous_user_cannot_list_without_explicit_permission_classes(self):
        response = ReadOnlyGroupViewSet.as_view({"get": "list"})(self.factory.get("/"))
        self.assertEqual(401, response.status_code, response.data)

    def test_composed_viewset_should_select_fields(self):
        """A viewset composed with only the DRF mixins it needs keeps the ?fields= contract"""
        request = self.factory.get("/?fields=name")
        force_authenticate(request, user=self.user)
        response = ReadOnlyGroupViewSet.as_view({"get": "list"})(request)
        self.assertEqual(200, response.status_code, response.data)
        self.assertListEqual([{"name": self.group.name}], response.data["results"])

    def test_renderers_should_not_come_from_dynamic_rest(self):
        expected = [JSONRenderer, BrowsableAPIRenderer]
        self.assertListEqual(expected, V3GenericViewSet.renderer_classes)
        self.assertListEqual(expected, resolve(reverse("api_v3:api-root")).func.view_class.renderer_classes)


class V3PaginationTest(SimpleTestCase):
    def _page_size(self, value):
        return V3Pagination().get_page_size(Request(APIRequestFactory().get(f"/?page_size={value}")))

    def test_page_size_should_be_bounded(self):
        """v2 leaves MAX_PAGE_SIZE unset, v3 must not"""
        self.assertEqual(settings.REST_API_V3_MAX_PAGE_SIZE, self._page_size(100000))

    @override_settings(REST_API_V3_MAX_PAGE_SIZE=5)
    def test_max_page_size_should_be_read_at_request_time(self):
        self.assertEqual(5, self._page_size(50))


class V3RouterTest(SimpleTestCase):
    def test_trailing_slash_should_be_required(self):
        self.assertEqual("/", router.trailing_slash)

    def test_registered_viewsets_should_not_allow_any(self):
        """AllowAny makes an endpoint world-writable, a public read uses IsAuthenticatedOrReadOnly"""
        offenders = [
            f"{prefix} -> {viewset.__name__}"
            for prefix, viewset, _basename in router.registry
            if not viewset.permission_classes or AllowAny in viewset.permission_classes
        ]
        self.assertListEqual([], offenders)

    def test_registered_prefixes_should_be_unique(self):
        """DRF refuses a duplicate basename only, a duplicate prefix would be silently shadowed"""
        _prefixes = [prefix for prefix, _viewset, _basename in router.registry]
        self.assertListEqual(sorted(set(_prefixes)), sorted(_prefixes))

    def test_every_registered_serializer_should_declare_known_default_fields(self):
        offenders = []
        for prefix, viewset, _basename in router.registry:
            _serializer_class = getattr(viewset, "serializer_class", None)
            if not hasattr(_serializer_class, "default_field_names"):
                continue
            _default = _serializer_class.default_field_names() or set()
            if _unknown := _default - _serializer_class.available_field_names():
                offenders.append(f"{prefix} -> {sorted(_unknown)}")
        self.assertListEqual([], offenders)


class V3RootTest(TestCase):
    def test_anonymous_user_can_read_the_root(self):
        self.assertEqual(200, APIClient().get(reverse("api_v3:api-root")).status_code)
