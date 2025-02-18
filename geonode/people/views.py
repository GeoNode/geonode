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
from allauth.account.views import SignupView, LoginView
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


class SetUserLayerPermission(View):
    def get(self, request):
        return user_and_group_permission(request, "profile")

    def post(self, request):
        return user_and_group_permission(request, "profile")


class CustomSignupView(SignupView):
    def get_context_data(self, **kwargs):
        ret = super().get_context_data(**kwargs)
        ret.update({"account_geonode_local_signup": settings.SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP})
        # Push captcha field at the end
        form = ret["form"]
        form.field_order = [f for f in form.fields.keys() if f != "captcha"] + ["captcha"]
        form.order_fields(form.field_order)
        return ret


class CustomLoginView(LoginView):
    template_name = "people/account_login.html"


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
