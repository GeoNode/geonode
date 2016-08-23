"""Django CAS 1.0/2.0 authentication backend"""

from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

__all__ = []

_DEFAULTS = {
    'CAS_ADMIN_PREFIX': None,
    'CAS_CREATE_USER': True,
    'CAS_EXTRA_LOGIN_PARAMS': None,
    'CAS_RENEW': False,
    'CAS_IGNORE_REFERER': False,
    'CAS_LOGOUT_COMPLETELY': True,
    'CAS_FORCE_CHANGE_USERNAME_CASE': None,
    'CAS_REDIRECT_URL': '/',
    'CAS_RETRY_LOGIN': False,
    'CAS_SERVER_URL': None,
    'CAS_VERSION': '2',
    'CAS_USERNAME_ATTRIBUTE': 'uid',
    'CAS_PROXY_CALLBACK': None,
    'CAS_LOGIN_MSG': _("Login succeeded. Welcome, %s."),
    'CAS_LOGGED_MSG': _("You are logged in as %s."),
}

for key, value in list(_DEFAULTS.items()):
    try:
        getattr(settings, key)
    except AttributeError:
        setattr(settings, key, value)
    # Suppress errors from DJANGO_SETTINGS_MODULE not being set
    except ImportError:
        pass
