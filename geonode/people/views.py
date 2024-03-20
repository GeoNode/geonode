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
from allauth.account.views import SignupView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from django.conf import settings
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.views import View
from geonode.tasks.tasks import send_email
from geonode.people.forms import ProfileForm
from geonode.people.utils import get_available_users
from geonode.base.auth import get_or_create_token
from geonode.people.forms import ForgotUsernameForm
from geonode.base.views import user_and_group_permission
from dal import autocomplete

from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from geonode.base.models import ResourceBase
from geonode.base.api.filters import DynamicSearchFilter
from geonode.groups.models import GroupProfile, GroupMember
from geonode.base.api.permissions import IsOwnerOrAdmin
from geonode.base.api.serializers import UserSerializer, GroupProfileSerializer, ResourceBaseSerializer
from geonode.base.api.pagination import GeoNodeApiPagination

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from geonode.security.utils import get_visible_resources
from guardian.shortcuts import get_objects_for_user
from rest_framework.exceptions import PermissionDenied
from geonode.people.utils import call_user_deletion_rules


class SetUserLayerPermission(View):
    def get(self, request):
        return user_and_group_permission(request, "profile")

    def post(self, request):
        return user_and_group_permission(request, "profile")


class CustomSignupView(SignupView):
    def get_context_data(self, **kwargs):
        ret = super().get_context_data(**kwargs)
        ret.update({"account_geonode_local_signup": settings.SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP})
        return ret


@login_required
def profile_edit(request, username=None):
    if username is None:
        try:
            profile = request.user
            username = profile.username
        except get_user_model().DoesNotExist:
            return redirect("profile_browse")
    else:
        profile = get_object_or_404(get_user_model(), Q(is_active=True), username=username)

    if username == request.user.username or request.user.is_superuser:
        if request.method == "POST":
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, (f"Profile {username} updated."))
                return redirect(reverse("profile_detail", args=[username]))
        else:
            form = ProfileForm(instance=profile)

        return render(
            request,
            "people/profile_edit.html",
            {
                "profile": profile,
                "form": form,
            },
        )
    else:
        return HttpResponseForbidden("You are not allowed to edit other users profile")


@login_required
def profile_detail(request, username):
    profile = get_object_or_404(get_user_model(), Q(is_active=True), username=username)
    # combined queryset from each model content type

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    return render(
        request,
        "people/profile_detail.html",
        {
            "access_token": access_token,
            "profile": profile,
        },
    )


def forgot_username(request):
    """Look up a username based on an email address, and send an email
    containing the username if found"""

    username_form = ForgotUsernameForm()

    message = ""

    site = Site.objects.get_current()

    email_subject = _(f"Your username for {site.name}")

    if request.method == "POST":
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():
            users = get_user_model().objects.filter(email=username_form.cleaned_data["email"])

            if users:
                username = users[0].username
                email_message = f"{email_subject} : {username}"
                send_email(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [username_form.cleaned_data["email"]],
                    fail_silently=False,
                )
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")

    return render(request, "people/forgot_username_form.html", context={"message": message, "form": username_form})


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    http_method_names = ["get", "post", "patch", "delete"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrAdmin,
    ]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        """
        Filters and sorts users.
        """
        if self.request and self.request.user:
            queryset = get_available_users(self.request.user)
        else:
            queryset = get_user_model().objects.all()

        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset.order_by("username")

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            raise PermissionDenied()
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return instance

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response("User deleted sucessfully", status=200)

    def perform_destroy(self, instance):
        call_user_deletion_rules(instance)
        instance.delete()

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve the Resources visible to the user.",
    )
    @action(detail=True, methods=["get"])
    def resources(self, request, pk=None):
        user = self.get_object()
        permitted = get_objects_for_user(user, "base.view_resourcebase")
        qs = ResourceBase.objects.all().filter(id__in=permitted).order_by("title")

        resources = get_visible_resources(
            qs,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )

        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True, context={"request": request})
        return paginator.get_paginated_response({"resources": serializer.data})

    @extend_schema(
        methods=["get"],
        responses={200: GroupProfileSerializer(many=True)},
        description="API endpoint allowing to retrieve the Groups the user is member of.",
    )
    @action(detail=True, methods=["get"])
    def groups(self, request, pk=None):
        user = self.get_object()
        qs_ids = GroupMember.objects.filter(user=user).values_list("group", flat=True)
        groups = GroupProfile.objects.filter(id__in=qs_ids)
        return Response(GroupProfileSerializer(embed=True, many=True).to_representation(groups))

    @action(detail=True, methods=["post"])
    def remove_from_group_manager(self, request, pk=None):
        user = self.get_object()
        target_ids = request.data.get("groups", [])
        user_groups = []
        invalid_groups = []

        if not target_ids:
            return Response({"error": "No groups IDs were provided"}, status=400)

        if target_ids == "ALL":
            user_groups = GroupProfile.groups_for_user(user)
        else:
            target_ids = set(target_ids)
            user_groups = GroupProfile.groups_for_user(user).filter(group_id__in=target_ids)
            # check for groups that user is not part of:
            invalid_groups.extend(target_ids - set(ug.group_id for ug in user_groups))

        for group in user_groups:
            group.demote(user)
        group_names = [group.title for group in user_groups]

        payload = {"success": f"User removed as a group manager from : {', '.join(group_names)}"}

        if invalid_groups:
            payload["error"] = f"User is not manager of the following groups: : {invalid_groups}"
            return Response(payload, status=400)
        return Response(payload, status=200)


class ProfileAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if self.request and self.request.user:
            qs = get_available_users(self.request.user)
        else:
            qs = get_user_model().objects.all()

        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(email__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
            )

        return qs
