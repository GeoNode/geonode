#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import hmac

from django.conf import settings
from django.core.cache import caches

from geonode.services import enumerations


class ServiceHandlerCache:
    """Caches remote service handler instances, keyed by URL, service type and auth."""

    def __init__(self):
        self.cache = caches["services"]

    @staticmethod
    def _digest(items):
        # HMAC-keyed, not a bare hash: cache keys can leak via backend
        # introspection (e.g. Redis SCAN), and a bare digest of low-entropy
        # credentials would allow offline guessing.
        message = repr(sorted(items)).encode("utf-8")
        return hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()[:16]

    @staticmethod
    def _collect_slots(obj):
        # __slots__ is per-class, not inherited automatically: walk the MRO to
        # find every slot actually available on this instance.
        names = set()
        for klass in type(obj).__mro__:
            slots = klass.__dict__.get("__slots__", ())
            names.update((slots,) if isinstance(slots, str) else slots)
        return names

    @classmethod
    def _build_auth_fingerprint(cls, auth=None, auth_config=None):
        """Build a non-sensitive auth discriminator for service-handler cache keys."""
        if auth_config is not None:
            # Content-based, not AuthConfig.pk: service_id already scopes the key,
            # and this keeps the fingerprint stable across its unsaved -> saved
            # transition during handler.create_geonode_service.
            payload_digest = cls._digest((getattr(auth_config, "payload", None) or {}).items())
            auth_type = getattr(auth_config, "type", None)
            return f"authcfg:{auth_type or '-'}:{payload_digest}"

        if auth is not None:
            # HashableAuthBase (geonode.security.auth_handlers) wraps the real
            # requests.auth.AuthBase in `.auth`; unwrap to fingerprint it.
            wrapped_auth = getattr(auth, "auth", auth)
            if isinstance(wrapped_auth, tuple) and len(wrapped_auth) == 2:
                digest = cls._digest({"username": wrapped_auth[0], "password": wrapped_auth[1]}.items())
                return f"auth:basic:{digest}"
            # __dict__ and __slots__ are not mutually exclusive: if any class in the MRO
            # lacks __slots__, the instance still gets a __dict__ in addition to whatever
            # slots a subclass declares. Merge both instead of treating them as
            # alternatives, or state living in one could be silently left out of the
            # fingerprint while state in the other made it look content-derived.
            values = dict(getattr(wrapped_auth, "__dict__", None) or {})
            for slot in cls._collect_slots(wrapped_auth):
                if slot in ("__dict__", "__weakref__"):
                    continue
                if hasattr(wrapped_auth, slot):
                    values[slot] = getattr(wrapped_auth, slot)
            if values:
                digest = cls._digest(values.items())
                return f"auth:{wrapped_auth.__class__.__name__}:{digest}"
            # Unknown auth shape: fall back to a content digest of the object itself, so
            # different (wrapped) auth objects never collapse into the same fingerprint.
            digest = cls._digest({"repr": repr(wrapped_auth)}.items())
            return f"auth:{wrapped_auth.__class__.__name__}:{digest}"

        return "-"

    @staticmethod
    def _build_url_fingerprint(base_url):
        return hashlib.sha256((base_url or "").encode("utf-8")).hexdigest()

    def get_key(self, base_url, service_type=enumerations.AUTO, service_id=None, auth=None, auth_config=None):
        auth_fingerprint = self._build_auth_fingerprint(auth=auth, auth_config=auth_config)
        url_fingerprint = self._build_url_fingerprint(base_url)
        return f"{service_type}|{service_id or '-'}|{auth_fingerprint}|{url_fingerprint}"

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache.set(key, value, settings.SERVICE_CACHE_EXPIRATION_TIME)

    def delete(self, key):
        self.cache.delete(key)


service_handler_cache = ServiceHandlerCache()
