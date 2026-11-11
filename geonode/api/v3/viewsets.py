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
import typing

from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from geonode.api.v3.constants import CONTEXT_KEY, FIELDS_PARAM
from geonode.api.v3.exceptions import problem_details_handler
from geonode.api.v3.pagination import V3Pagination
from geonode.api.v3.schema import V3AutoSchema

_UNSET = object()

# OPTIONS is safe too, but its metadata describes the write serializer, which is never narrowed
READ_METHODS = ("GET", "HEAD")

# the global default browsable renderer comes from dynamic-rest, v3 is plain DRF
V3_RENDERER_CLASSES = [JSONRenderer, BrowsableAPIRenderer]


class FieldSelectionViewSetMixin:
    """
    Implements ``?fields=`` on both the serializer and the queryset.
    The serializer declares what its fields cost in ``setup_queryset``, so the joins are added only when returned
    """

    _requested_fields_cache = _UNSET

    def get_requested_fields(self) -> typing.Optional[typing.Set[str]]:
        """The fields a read returns: ``?fields=``, else the serializer defaults. ``None`` on writes"""
        if self._requested_fields_cache is _UNSET:
            self._requested_fields_cache = self.__parse_requested_fields()
        return self._requested_fields_cache

    def get_response_fields(self) -> typing.Optional[typing.Set[str]]:
        """The fields of the response, a write answers with the read representation"""
        if (_fields := self.get_requested_fields()) is not None:
            return _fields
        return self.__default_fields(self.get_serializer_class())

    def get_serializer_context(self):
        _context = super().get_serializer_context()
        if (_fields := self.get_requested_fields()) is not None:
            _context[CONTEXT_KEY] = _fields
        return _context

    def setup_queryset(self, queryset):
        _serializer_class = self.get_serializer_class()
        if not hasattr(_serializer_class, "setup_queryset"):
            return queryset
        return _serializer_class.setup_queryset(queryset, self.get_response_fields(), getattr(self, "request", None))

    def __parse_requested_fields(self) -> typing.Optional[typing.Set[str]]:
        _request = getattr(self, "request", None)
        if _request is None or _request.method not in READ_METHODS:
            return None

        _serializer_class = self.get_serializer_class()
        _raw = _request.query_params.get(FIELDS_PARAM, "")
        _requested = {_name.strip() for _name in _raw.split(",") if _name.strip()}
        if not hasattr(_serializer_class, "available_field_names"):
            # ignoring it would silently return every field
            if _requested:
                raise ValidationError({FIELDS_PARAM: ["This endpoint does not support field selection."]})
            return None
        if not _requested:
            return self.__default_fields(_serializer_class)

        _available = _serializer_class.available_field_names()
        if _unknown := sorted(_requested - _available):
            raise ValidationError(
                {
                    FIELDS_PARAM: [
                        f"Unknown field(s): {', '.join(_unknown)}. Available: {', '.join(sorted(_available))}."
                    ]
                }
            )
        return _requested

    @staticmethod
    def __default_fields(serializer_class) -> typing.Optional[typing.Set[str]]:
        if not hasattr(serializer_class, "available_field_names"):
            return None
        # an explicit full set, so nested serializers still narrow to their own defaults
        _default = serializer_class.default_field_names()
        return _default if _default is not None else serializer_class.available_field_names()


class V3GenericViewSet(FieldSelectionViewSetMixin, viewsets.GenericViewSet):
    """
    Base of every v3 viewset, composed with the DRF mixins it needs.
    Subclasses override ``get_base_queryset``, so the ``?fields=`` setup is never skipped
    """

    # fail closed: REST_FRAMEWORK has no default, a viewset that forgets them would be AllowAny
    permission_classes = [IsAuthenticated]
    renderer_classes = V3_RENDERER_CLASSES
    pagination_class = V3Pagination
    # set here and not as DEFAULT_SCHEMA_CLASS, so drf-spectacular never inspects v2 views
    schema = V3AutoSchema()
    # emitted as x-stability in the schema, an endpoint is promoted by changing it
    stability = "experimental"

    def get_exception_handler(self):
        return problem_details_handler

    def get_base_queryset(self):
        return super().get_queryset()

    def get_queryset(self):
        return self.setup_queryset(self.get_base_queryset())

    def get_read_representation(self, instance):
        # refetched through get_queryset, an instance just saved has none of the annotations of setup_queryset
        _instance = self.get_queryset().filter(pk=instance.pk).first() or instance
        _context = self.get_serializer_context()
        if (_fields := self.get_response_fields()) is not None:
            _context[CONTEXT_KEY] = _fields
        return self.get_serializer(_instance, context=_context).data


class V3CreateModelMixin(mixins.CreateModelMixin):
    """Answers a create with the read representation"""

    def create(self, request, *args, **kwargs):
        _serializer = self.get_serializer(data=request.data)
        _serializer.is_valid(raise_exception=True)
        self.perform_create(_serializer)
        _data = self.get_read_representation(_serializer.instance)
        return Response(_data, status=201, headers=self.get_success_headers(_data))


class V3UpdateModelMixin(mixins.UpdateModelMixin):
    """Answers an update with the read representation"""

    def update(self, request, *args, **kwargs):
        _serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.pop("partial", False))
        _serializer.is_valid(raise_exception=True)
        self.perform_update(_serializer)
        return Response(self.get_read_representation(_serializer.instance), status=200)


class V3ModelViewSet(
    V3CreateModelMixin,
    mixins.RetrieveModelMixin,
    V3UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    V3GenericViewSet,
):
    pass


class V3RootView(APIRootView):
    """The v3 root lists the endpoints only, the endpoints check their own permissions"""

    permission_classes = [AllowAny]
    renderer_classes = V3_RENDERER_CLASSES
