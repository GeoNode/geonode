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
import logging

from functools import wraps
from django.contrib import auth
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import classonlymethod
from django.core.exceptions import PermissionDenied

from geonode.utils import (check_ogc_backend,
                           get_client_ip,
                           get_client_host)

logger = logging.getLogger(__name__)


def on_ogc_backend(backend_package):
    """Decorator for function specific to a certain ogc backend.

    This decorator will wrap function so it only gets executed if the
    specified ogc backend is currently used. If not, the function will just
    be skipped.

    Useful to decorate features/tests that only available for specific
    backend.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            on_backend = check_ogc_backend(backend_package)
            if on_backend:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def view_decorator(fdec, subclass=False):
    """
    Change a function decorator into a view decorator.

    https://github.com/lqc/django/tree/cbvdecoration_ticket14512
    """
    def decorator(cls):
        if not hasattr(cls, "as_view"):
            raise TypeError(
                "You should only decorate subclasses of View, not mixins.")
        if subclass:
            cls = type("%sWithDecorator(%s)" %
                       (cls.__name__, fdec.__name__), (cls,), {})
        original = cls.as_view.im_func

        @wraps(original)
        def as_view(current, **initkwargs):
            return fdec(original(current, **initkwargs))
        cls.as_view = classonlymethod(as_view)
        return cls
    return decorator


def view_or_apiauth(view, request, test_func, *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(auth.get_user(request)) or not settings.OAUTH2_API_KEY:
        # Already logged in, just return the view.
        #
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        _auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(_auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if _auth[0].lower() == "apikey":
                auth_api_key = _auth[1]
                if auth_api_key and auth_api_key == settings.OAUTH2_API_KEY:
                    return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    return response


def superuser_only(function):
    """
    Limit view to superusers only.

    Usage:
    --------------------------------------------------------------------------
    @superuser_only
    def my_view(request):
        ...
    --------------------------------------------------------------------------

    or in urls:

    --------------------------------------------------------------------------
    urlpatterns = patterns('',
        (r'^foobar/(.*)', is_staff(my_view)),
    )
    --------------------------------------------------------------------------
    """
    def _inner(request, *args, **kwargs):
        if not auth.get_user(request).is_superuser and not auth.get_user(request).is_staff:
            raise PermissionDenied
        return function(request, *args, **kwargs)
    return _inner


def superuser_protected(function):
    """Decorator that forces a view to be accessible by SUPERUSERS only.
    """
    def _inner(request, *args, **kwargs):
        if not auth.get_user(request).is_superuser:
            return HttpResponse(
                json.dumps({
                    'error': 'unauthorized_request'
                }),
                status=403,
                content_type="application/json"
            )
        return function(request, *args, **kwargs)
    return _inner


def whitelist_protected(function):
    """Decorator that forces a view to be accessible by WHITE_LISTED
    IPs only.
    """
    def _inner(request, *args, **kwargs):
        if not settings.AUTH_IP_WHITELIST or \
            (get_client_ip(request) not in settings.AUTH_IP_WHITELIST and
             get_client_host(request) not in settings.AUTH_IP_WHITELIST):
            return HttpResponse(
                json.dumps({
                    'error': 'unauthorized_request'
                }),
                status=403,
                content_type="application/json"
            )
        return function(request, *args, **kwargs)
    return _inner


def logged_in_or_apiauth():

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_apiauth(func, request,
                                   lambda u: u.is_authenticated(),
                                   *args, **kwargs)
        return wrapper

    return view_decorator


def superuser_or_apiauth():

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_apiauth(func, request,
                                   lambda u: u.is_superuser,
                                   *args, **kwargs)
        return wrapper

    return view_decorator


def dump_func_name(func):
    def echo_func(*func_args, **func_kwargs):
        logger.info(" ---------------------------------------------------------- ")
        logger.info('Start func: {}'.format(func.__name__))
        logger.info(" ---------------------------------------------------------- ")
        return func(*func_args, **func_kwargs)
    return echo_func
