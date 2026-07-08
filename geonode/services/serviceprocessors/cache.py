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

from django.conf import settings
from django.core.cache import caches

from geonode.services import enumerations


class ServiceHandlerCache:
    """Caches remote service handler instances, keyed by URL, service type and auth."""

    def __init__(self):
        self.cache = caches["services"]

    @staticmethod
    def _digest(items):
        """Short, one-way digest of a credential-bearing mapping's items."""
        return hashlib.sha256(repr(sorted(items)).encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _build_auth_fingerprint(cls, auth=None, auth_config=None):
        """Build a non-sensitive auth discriminator for service-handler cache keys."""
        if auth_config is not None:
            # Digest the decrypted payload (not the encrypted `_payload` column): AuthConfig
            # uses Fernet, which embeds a random nonce, so the ciphertext changes on every save
            # even when the credentials don't. Digesting the plaintext content means the
            # fingerprint only changes when the actual credentials change.
            payload_digest = cls._digest((getattr(auth_config, "payload", None) or {}).items())
            auth_config_id = getattr(auth_config, "id", None) or getattr(auth_config, "pk", None)
            if auth_config_id is not None:
                return f"authcfg:{auth_config_id}:{payload_digest}"
            auth_type = getattr(auth_config, "type", None)
            return f"authcfg:unsaved:{auth_type or '-'}:{payload_digest}"

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
                digest = cls._digest(wrapped_auth.__dict__.items())
                return f"auth:{wrapped_auth.__class__.__name__}:{digest}"
            if hasattr(wrapped_auth, "username"):
                return f"auth:{wrapped_auth.__class__.__name__}:{getattr(wrapped_auth, 'username', '-') or '-'}"
            return f"auth:{auth.__class__.__name__}"

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
