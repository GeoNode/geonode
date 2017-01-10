# -*- coding: utf-8 -*-
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

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.conf import settings
from django.http import HttpResponseForbidden

from geonode.people.models import Profile
from geonode.people.forms import ProfileForm
from geonode.people.forms import ForgotUsernameForm
from geonode.tasks.email import send_email


@login_required
def profile_edit(request, username=None):
    if username is None:
        try:
            profile = request.user
            username = profile.username
        except Profile.DoesNotExist:
            return redirect("profile_browse")
    else:
        profile = get_object_or_404(Profile, username=username)

    if username == request.user.username or request.user.is_superuser:
        if request.method == "POST":
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, ("Profile %s updated." % username))
                return redirect(
                    reverse(
                        'profile_detail',
                        args=[
                            username]))
        else:
            form = ProfileForm(instance=profile)

        return render(request, "people/profile_edit.html", {
            "profile": profile,
            "form": form,
        })
    else:
        return HttpResponseForbidden(
            'You are not allowed to edit other users profile')


def profile_detail(request, username):
    profile = get_object_or_404(Profile, username=username)
    # combined queryset from each model content type

    return render(request, "people/profile_detail.html", {
        "profile": profile,
    })


def forgot_username(request):
    """ Look up a username based on an email address, and send an email
    containing the username if found"""

    username_form = ForgotUsernameForm()

    message = ''

    site = Site.objects.get_current()

    email_subject = _("Your username for " + site.name)

    if request.method == 'POST':
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():

            users = get_user_model().objects.filter(
                email=username_form.cleaned_data['email'])

            if users:
                username = users[0].username
                email_message = email_subject + " : " + username
                send_email(email_subject, email_message, settings.DEFAULT_FROM_EMAIL,
                           [username_form.cleaned_data['email']], fail_silently=False)
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")

    return render_to_response('people/forgot_username_form.html',
                              RequestContext(request, {
                                  'message': message,
                                  'form': username_form
                              }))
