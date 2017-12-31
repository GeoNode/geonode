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
import json

from agon_ratings.categories import slug

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
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth, messages
from user_messages.models import UserThread

from account import signals
from account.forms import SignupForm
from account.views import SignupView, InviteUserView
from account.utils import default_redirect

from geonode.people.models import Profile
from geonode.people.forms import ProfileForm
from geonode.people.forms import ForgotUsernameForm
from geonode.tasks.email import send_email
from geonode.groups.models import GroupProfile, GroupMember


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

    if profile.is_active:
        status = "Inactivate User"
    else:
        status = "Activate User"

    return render(request, "people/profile_detail.html", {
        "profile": profile,
        "status": status,
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


#@jahangir091

class CreateUser(SignupView):
    template_name = "account/create_user.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated() and (self.request.user.is_superuser or self.request.user.is_manager_of_any_group):
            return super(SignupView, self).get(*args, **kwargs)
        elif self.request.user.is_authenticated():
            return redirect(default_redirect(self.request, settings.ACCOUNT_LOGIN_REDIRECT_URL))
        if not self.is_open():
            return self.closed()
        return HttpResponseRedirect(reverse('account_signup'))

    def post(self, *args, **kwargs):
        if not self.is_open():
            return self.closed()
        return super(SignupView, self).post(*args, **kwargs)

    def login_user(self):
        user = self.request.user
        if settings.ACCOUNT_USE_AUTH_AUTHENTICATE:
            # call auth.authenticate to ensure we set the correct backend for
            # future look ups using auth.get_user().
            user = auth.authenticate(**self.user_credentials())
        else:
            # set auth backend to ModelBackend, but this may not be used by
            # everyone. this code path is deprecated and will be removed in
            # favor of using auth.authenticate above.
            user.backend = "django.contrib.auth.backends.ModelBackend"
        auth.login(self.request, user)
        self.request.session.set_expiry(0)


def activateuser(request, username):
    if request.method == 'GET':
        user = Profile.objects.get(username=username)
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse('profile_detail', args=[username]))


class UserSignup(SignupView):
    """
    Extending  geonodes SignupView to override some functionality.
    """

    def after_signup(self, form):
        """after signup add created user to default group """

        signals.user_signed_up.send(
            sender=SignupForm, user=self.created_user, form=form)

        default_group = get_object_or_404(GroupProfile, slug='default')
        default_group.join(self.created_user, role='member')


def inbox(request):
    """

    :param request:
    :return:
    """
    unread_messages = UserThread.objects.filter(user=request.user, unread=True)
    for msg in unread_messages:
        msg.unread = False
        msg.save()
    return HttpResponseRedirect(reverse('messages_inbox'))


class InviteUser(InviteUserView):
    """

    """

    def get_success_url(self, fallback_url=None, **kwargs):

        return reverse('invite_user')


@login_required
def get_current_user(request):
    if request.method == 'GET':
        return HttpResponse(
            json.dumps(
                dict(id=request.user.id, username=request.user.username),
                ensure_ascii=False),
            status=200,
            content_type='application/javascript')
# end
