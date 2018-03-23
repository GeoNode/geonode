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

from functools import wraps
from django.utils.decorators import classonlymethod
from django.core.exceptions import PermissionDenied
from geonode.utils import check_ogc_backend


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
        if not request.user.is_superuser and not request.user.is_staff:
            raise PermissionDenied
        return function(request, *args, **kwargs)
    return _inner
