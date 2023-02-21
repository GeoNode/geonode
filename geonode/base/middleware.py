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


# Geonode functionality

from django.shortcuts import render
from geonode.base.utils import configuration_session_cache


class ReadOnlyMiddleware:
    """
    A Middleware disabling all content modifying requests, if read-only Configuration setting is True,
    with an exception for whitelisted url names.
    """

    FORBIDDEN_HTTP_METHODS = ["POST", "PUT", "DELETE"]

    WHITELISTED_URL_NAMES = [
        "login",
        "logout",
        "account_login",
        "account_logout",
        "ows_endpoint",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        session = request.session
        configuration_session_cache(session)

        # check if the Geonode instance is read-only
        if session.get("config").get("configuration").get("read_only"):
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser or not request.user.is_active:
                # check if the request's method is forbidden in read-only instance
                if request.method in self.FORBIDDEN_HTTP_METHODS:
                    # check if the request is not against whitelisted views (check by URL names)
                    if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                        # return HttpResponse('Error: Instance in read-only mode', status=405)
                        return render(request, "base/read_only_violation.html", status=405)


class MaintenanceMiddleware:
    """
    A Middleware redirecting all requests to maintenance info page, except:
        - admin panel login,
        - admin panel logout,
        - requests performed by superuser,
    if maintenance Configuration setting is True.
    """

    # URL's enabling superuser to login/logout to/from admin panel
    WHITELISTED_URL_NAMES = [
        "login",
        "logout",
        "index",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        session = request.session
        configuration_session_cache(session)

        # check if the Geonode instance is in maintenance mode
        if session.get("config").get("configuration").get("maintenance"):
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser:
                # check if the request is not against whitelisted views (check by URL names)
                if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                    return render(request, "base/maintenance.html", status=503)
