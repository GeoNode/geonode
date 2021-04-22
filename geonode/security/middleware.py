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
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.auth import get_token_object_from_session, basic_auth_authenticate_user

from guardian.shortcuts import get_anonymous_user


# make sure login_url can be mapped to redirection URL and will match request.path
login_url = settings.LOGIN_URL.replace(settings.SITEURL.rstrip('/'), '')
if not login_url.startswith('/'):
    login_url = f"/{login_url}"

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('layer_acls'),
        reverse('layer_acls_dep'),
        reverse('layer_resolve_user'),
        reverse('layer_resolve_user_dep'),
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
        login_url,
    )
else:
    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
        login_url,
    )

white_list = [compile(x) for x in white_list_paths + getattr(settings, "AUTH_EXEMPT_URLS", ())]


class LoginRequiredMiddleware(MiddlewareMixin):

    """
    Requires a user to be logged in to access any page that is not white-listed.

    This middleware simply checks user property of a request, to determine whether the query is authenticated or not,
    but since DRF assumes correlation between session authentication and presence of user property in the request,
    an additional check was introduced in the middleware, to allow Basic authenticated requests without additional
    middleware setting this property (otherwise, all DRF views configured with:
    `authentication_classes = [SessionAuthentication,]`
    would accept Basic authenticated requests (regardless of presence of `BasicAuthentication` in view's
    authentication_classes).
    """

    redirect_to = login_url

    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):

        if not request.user.is_authenticated or request.user == get_anonymous_user():

            if "HTTP_AUTHORIZATION" in request.META:
                auth_header = request.META.get("HTTP_AUTHORIZATION", request.META.get("HTTP_AUTHORIZATION2"))

                if auth_header and "Basic" in auth_header:
                    user = basic_auth_authenticate_user(auth_header)

                    if user:
                        # allow Basic Auth authenticated requests with valid credentials
                        return

            if not any(path.match(request.path) for path in white_list):
                return HttpResponseRedirect(
                    f"{self.redirect_to}?next={request.path}"
                )


class SessionControlMiddleware(MiddlewareMixin):
    """
    Middleware that checks if session variables have been correctly set.
    """

    redirect_to = getattr(settings, 'LOGIN_URL', reverse('account_login'))

    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):
        if request and request.user and not request.user.is_anonymous:
            if not request.user.is_active:
                self.do_logout(request)
            elif check_ogc_backend(geoserver.BACKEND_PACKAGE):
                try:
                    access_token = get_token_object_from_session(request.session)
                except Exception:
                    access_token = None
                    self.do_logout(request)

                # we extend the token in case the session is active but the token expired
                if access_token is None or access_token.is_expired():
                    self.do_logout(request)

    def do_logout(self, request):
        try:
            logout(request)
        finally:
            try:
                from django.contrib import messages
                from django.utils.translation import ugettext_noop as _
                messages.warning(request, _("Session is Expired. Please login again!"))
            except Exception:
                pass

            if not any(path.match(request.path) for path in white_list):
                return HttpResponseRedirect(
                    f'{self.redirect_to}?next={request.path}')
