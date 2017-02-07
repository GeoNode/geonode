"""Replacement authentication decorators that work around redirection loops"""

from __future__ import absolute_import
from __future__ import unicode_literals

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlquote

__all__ = ['login_required', 'permission_required', 'user_passes_test']


def user_passes_test(test_func, login_url=None,
                     redirect_field_name=REDIRECT_FIELD_NAME):
    """Replacement for django.contrib.auth.decorators.user_passes_test that
    returns 403 Forbidden if the user is already logged in.
    """

    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            elif request.user.is_authenticated():
                return HttpResponseForbidden('<h1>Permission denied</h1>')
            else:
                path = '%s?%s=%s' % (login_url, redirect_field_name,
                                     urlquote(request.get_full_path()))
                return HttpResponseRedirect(path)
        return wrapper
    return decorator


def permission_required(perm, login_url=None):
    """Replacement for django.contrib.auth.decorators.permission_required that
    returns 403 Forbidden if the user is already logged in.
    """

    return user_passes_test(lambda u: u.has_perm(perm), login_url=login_url)
