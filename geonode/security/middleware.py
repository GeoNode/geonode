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
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import logout
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.auth import (
    extract_user_from_headers,
    get_token_object_from_session,
    visitor_ip_address,
    is_ipaddress_in_whitelist
)


# make sure login_url can be mapped to redirection URL and will match request.path
login_url = settings.LOGIN_URL.replace(settings.SITEURL.rstrip('/'), '')
if not login_url.startswith('/'):
    login_url = f"/{login_url}"

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('dataset_acls'),
        reverse('dataset_acls_dep'),
        reverse('dataset_resolve_user'),
        reverse('dataset_resolve_user_dep'),
        reverse('proxy'),
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

        if request.user and (not request.user.is_authenticated or request.user.is_anonymous):

            if not any(path.match(request.path) for path in white_list):
                return HttpResponseRedirect(
                    f"{self.redirect_to}?next={request.path}"
                )


class LoginFromApiKeyMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):
        '''
        If an api key is provided and validated, the user can access to the page even without the login
        This middleware is deactivated by default, to activate it set ENABLE_APIKEY_LOGIN=True
        '''
        if request.user and (not request.user.is_authenticated or request.user.is_anonymous):

            request.user = extract_user_from_headers(request)

            if request.user and not request.user.is_anonymous and request.user.is_authenticated:
                return


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


class AdminAllowedMiddleware(MiddlewareMixin):
    """
    Middleware that checks if admin is making requests from allowed IPs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):
        whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
        if len(whitelist) > 0:
            # When the request reaches the middleware the user attached to it (directly or through a session)
            # might differ from the user from the headers. E.g. userX might have a an active session
            # and a request with admin's headers could be issues. For this reason we check both to find out if
            # an admin is trying a request somehow.
            potential_admins = []
            potential_admins.append(extract_user_from_headers(request))
            if hasattr(request, "user"):
                potential_admins.append(request.user)

            is_admin = any([u.is_superuser for u in potential_admins])

            if is_admin:
                visitor_ip = visitor_ip_address(request)
                if not is_ipaddress_in_whitelist(visitor_ip, whitelist):
                    try:
                        if hasattr(request, "session"):
                            logout(request)
                        if hasattr(request, "user"):
                            request.user = AnonymousUser()
                        if "HTTP_AUTHORIZATION" in request.META:
                            del request.META["HTTP_AUTHORIZATION"]
                        if "apikey" in request.GET:
                            del request.GET["apikey"]
                    finally:
                        try:
                            from django.contrib import messages
                            from django.utils.translation import ugettext_noop as _
                            messages.warning(request, _("Admin access forbidden from {visitor_ip}"))
                        except Exception:
                            pass
        return self.get_response(request)
