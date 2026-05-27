#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import json

from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt

from guardian.models import Group

from oauth2_provider.models import AccessToken
from oauth2_provider.exceptions import OAuthToolkitError, FatalClientError
from allauth.account.utils import user_field, user_email, user_username

from ..utils import json_response
from ..decorators import superuser_or_apiauth
from ..base.auth import get_token_object_from_session, get_auth_token

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ReadOnlyModelViewSet
from dynamic_rest.viewsets import WithDynamicViewSetMixin

from django.conf import settings
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from geonode.groups.models import GroupCategory, GroupProfile
from geonode.base.api.pagination import GeoNodeApiPagination
from .serializers import (
    GroupCategorySerializer,
    GroupProfileSerializer,
    GroupSerializer,
)
from .filters import GroupCategoryFilter, GroupProfileFilter, GroupFilter


def verify_access_token(request, key):
    try:
        token = None
        if request:
            token = get_token_object_from_session(request.session)
        if not token or token.key != key:
            token = AccessToken.objects.get(token=key)
        if not token.is_valid():
            raise OAuthToolkitError("AccessToken is not valid.")
        if token.is_expired():
            raise OAuthToolkitError("AccessToken has expired.")
    except AccessToken.DoesNotExist:
        raise FatalClientError("AccessToken not found at all.")
    except Exception:
        return None
    return token


class UserInfoView(APIView):

    def get(self, request):
        user = request.user

        if not user or user.is_anonymous:
            out = {"success": False, "status": "error", "errors": {"user": ["User is not authenticated"]}}
            return json_response(out, status=401)

        access_token = get_auth_token(user)

        groups = [group.name for group in user.groups.all()]
        if user.is_superuser:
            groups.append("admin")

        user_info = {
            "sub": str(user.id),
            "name": " ".join([user_field(user, "first_name"), user_field(user, "last_name")]),
            "given_name": user_field(user, "first_name"),
            "family_name": user_field(user, "last_name"),
            "email": user_email(user),
            "preferred_username": user_username(user),
            "groups": groups,
            "access_token": str(access_token),
        }

        response = Response(user_info)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response


class GroupCategoryViewSet(WithDynamicViewSetMixin, ReadOnlyModelViewSet):
    serializer_class = GroupCategorySerializer
    pagination_class = GeoNodeApiPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GroupCategoryFilter
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        if settings.API_LOCKDOWN and not self.request.user.is_authenticated:
            return GroupCategory.objects.none()
        return GroupCategory.objects.all()


class GroupProfileViewSet(WithDynamicViewSetMixin, ReadOnlyModelViewSet):
    serializer_class = GroupProfileSerializer
    pagination_class = GeoNodeApiPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GroupProfileFilter
    ordering_fields = ["title", "last_modified"]
    ordering = ["title"]

    def get_queryset(self):
        user = self.request.user

        if settings.API_LOCKDOWN and not user.is_authenticated:
            return GroupProfile.objects.none()

        qs = GroupProfile.objects.all()

        if not user.is_authenticated:
            return qs.exclude(access="private")

        if not user.is_superuser:
            return qs.filter(Q(pk__in=user.group_list_all()) | ~Q(access="private"))

        return qs


class GroupViewSet(WithDynamicViewSetMixin, ReadOnlyModelViewSet):
    serializer_class = GroupSerializer
    pagination_class = GeoNodeApiPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GroupFilter
    ordering_fields = ["name", "groupprofile__last_modified"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user

        if settings.API_LOCKDOWN and not user.is_authenticated:
            return Group.objects.none()

        qs = Group.objects.exclude(groupprofile=None).exclude(name="anonymous")

        if not user.is_authenticated:
            return qs.exclude(groupprofile__access="private")

        if not user.is_superuser:
            return qs.filter(Q(groupprofile__in=user.group_list_all()) | ~Q(groupprofile__access="private"))

        return qs


@csrf_exempt
def verify_token(request):
    if request.POST and "token" in request.POST:
        token = None
        try:
            access_token = request.POST.get("token")
            token = verify_access_token(request, access_token)
        except Exception as e:
            return HttpResponse(json.dumps({"error": str(e)}), status=403, content_type="application/json")

        if token:
            token_info = json.dumps(
                {
                    "client_id": token.application.client_id,
                    "user_id": token.user.id,
                    "username": token.user.username,
                    "issued_to": token.user.username,
                    "access_token": access_token,
                    "email": token.user.email,
                    "verified_email": "true",
                    "access_type": "online",
                    "expires_in": (token.expires - timezone.now()).total_seconds() * 1000,
                }
            )

            response = HttpResponse(token_info, content_type="application/json")
            response["Authorization"] = f"Bearer {access_token}"
            return response
        else:
            return HttpResponse(
                json.dumps({"error": "No access_token from server."}), status=403, content_type="application/json"
            )

    return HttpResponse(json.dumps({"error": "invalid_request"}), status=403, content_type="application/json")


@csrf_exempt
@superuser_or_apiauth()
def roles(request):
    groups = [group.name for group in Group.objects.all()]
    groups.append("admin")

    return HttpResponse(json.dumps({"groups": groups}), content_type="application/json")


@csrf_exempt
@superuser_or_apiauth()
def users(request):
    user_name = request.path_info.rsplit("/", 1)[-1]
    User = get_user_model()

    if user_name is None or not user_name or user_name == "users":
        users = [user for user in User.objects.all()]
    else:
        users = [user for user in User.objects.filter(username=user_name)]

        if not users:
            # Try using the user email
            users = [user for user in User.objects.filter(email=user_name)]

    json_object = []
    for user in users:
        groups = [group.name for group in user.groups.all()]
        if user.is_superuser:
            groups.append("admin")

        json_object.append({"username": user.username, "groups": groups})

    return HttpResponse(json.dumps({"users": json_object}), content_type="application/json")


@csrf_exempt
@superuser_or_apiauth()
def admin_role(request):
    return HttpResponse(json.dumps({"adminRole": "admin"}), content_type="application/json")
