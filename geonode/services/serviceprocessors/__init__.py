#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import hashlib
import logging

from django.conf import settings
from geonode.services import enumerations
from django.core.cache import caches
from geonode.services.serviceprocessors.registry import service_type_registry

service_cache = caches["services"]
logger = logging.getLogger(__name__)


def _build_auth_cache_fingerprint(auth=None, auth_config=None):
    """Build a non-sensitive auth discriminator for service-handler cache keys."""
    if auth_config is not None:
        auth_config_id = getattr(auth_config, "id", None) or getattr(auth_config, "pk", None)
        if auth_config_id is not None:
            return f"authcfg:{auth_config_id}"
        auth_type = getattr(auth_config, "type", None)
        auth_username = (getattr(auth_config, "payload", None) or {}).get("username")
        return f"authcfg:unsaved:{auth_type or '-'}:{auth_username or '-'}"

    if auth is not None:
        # HashableAuthBase (see geonode.security.auth_handlers) wraps the actual
        # requests.auth.AuthBase instance in `.auth` to make it hashable; unwrap it
        # so the fingerprint reflects the real credentials, not just the wrapper class.
        wrapped_auth = getattr(auth, "auth", auth)
        if isinstance(wrapped_auth, tuple) and len(wrapped_auth) == 2:
            return f"auth:basic:{wrapped_auth[0]}"
        if hasattr(wrapped_auth, "__dict__") and wrapped_auth.__dict__:
            # Hash the full credential set (not just the username) so that e.g. a
            # password change on an otherwise-identical auth object busts the cache key.
            digest = hashlib.sha256(repr(sorted(wrapped_auth.__dict__.items())).encode("utf-8")).hexdigest()[:16]
            return f"auth:{wrapped_auth.__class__.__name__}:{digest}"
        if hasattr(wrapped_auth, "username"):
            return f"auth:{wrapped_auth.__class__.__name__}:{getattr(wrapped_auth, 'username', '-') or '-'}"
        return f"auth:{auth.__class__.__name__}"

    return "-"


def _build_url_cache_fingerprint(base_url):
    return hashlib.sha256((base_url or "").encode("utf-8")).hexdigest()


def get_service_cache_key(base_url, service_type=enumerations.AUTO, service_id=None, auth=None, auth_config=None):
    auth_fingerprint = _build_auth_cache_fingerprint(auth=auth, auth_config=auth_config)
    url_fingerprint = _build_url_cache_fingerprint(base_url)
    return f"{service_type}|{service_id or '-'}|{auth_fingerprint}|{url_fingerprint}"


def get_available_service_types():
    return service_type_registry.get_available_service_types()


def get_service_handler(base_url, service_type=enumerations.AUTO, service_id=None, *args, **kwargs):
    """Return the appropriate remote service handler for the input URL.
    If the service type is not explicitly passed in it will be guessed from
    """

    cache_key = get_service_cache_key(
        base_url,
        service_type=service_type,
        service_id=service_id,
        auth=kwargs.get("auth"),
        auth_config=kwargs.get("auth_config"),
    )

    if entry := service_cache.get(cache_key):
        return entry

    handler = service_type_registry.get_handler_class(service_type)
    try:
        service_handler = handler(base_url, service_id, *args, **kwargs)
        service_cache.set(cache_key, service_handler, settings.SERVICE_CACHE_EXPIRATION_TIME)
    except Exception as e:
        logger.exception(e)
        logger.exception(msg=f"Could not parse service {base_url}")
        raise
    return service_handler
