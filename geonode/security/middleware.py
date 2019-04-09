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

from re import compile

from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.auth import get_token_object_from_session

from guardian.shortcuts import get_anonymous_user

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('javascript-catalog'),
        reverse('lang'),
        reverse('layer_acls'),
        reverse('layer_acls_dep'),
        reverse('layer_resolve_user'),
        reverse('layer_resolve_user_dep'),
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
    )
else:
    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('javascript-catalog'),
        reverse('lang'),
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
    )

white_list = map(
    compile,
    white_list_paths +
    getattr(
        settings,
        "AUTH_EXEMPT_URLS",
        ()))


class LoginRequiredMiddleware(object):

    """
    Requires a user to be logged in to access any page that is not white-listed.
    """

    redirect_to = getattr(settings, 'LOGIN_URL', reverse('account_login'))

    def process_request(self, request):
        if not request.user.is_authenticated(
        ) or request.user == get_anonymous_user():
            if not any(path.match(request.path) for path in white_list):
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))


class SessionControlMiddleware(object):
    """
    Middleware that checks if session variables have been correctly set.
    """

    redirect_to = getattr(settings, 'LOGIN_URL', reverse('account_login'))

    def process_request(self, request):
        if request and request.user and not request.user.is_anonymous:
            if not request.user.is_active:
                self.do_logout(request)
            elif check_ogc_backend(geoserver.BACKEND_PACKAGE):
                try:
                    access_token = get_token_object_from_session(request.session)
                except BaseException:
                    access_token = None
                    self.do_logout(request)

                # we extend the token in case the session is active but the token expired
                if access_token is None or access_token.is_expired():
                    self.do_logout(request)

    def do_logout(self, request):
        try:
            logout(request)
        except BaseException:
            pass
        finally:
            try:
                from django.contrib import messages
                from django.utils.translation import ugettext_noop as _
                messages.warning(request, _("Session is Expired. Please login again!"))
            except BaseException:
                pass

            if not any(path.match(request.path) for path in white_list):
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))
