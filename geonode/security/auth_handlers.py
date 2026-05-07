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
import base64
import hashlib
import json
from abc import ABC, abstractmethod

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError
from requests.auth import AuthBase, HTTPBasicAuth

from geonode.security.models import AuthConfig

SECRET_KEY = settings.SECRET_KEY
ENCRYPTION_KEY = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
cipher = Fernet(ENCRYPTION_KEY)


class AuthHandler(ABC):
    handled_type = None
    config: AuthConfig

    def __init__(self, config: AuthConfig):
        self.config = config
        self._init_from_config()

    @abstractmethod
    def _init_from_config(self):
        pass

    def get_request_auth(self) -> AuthBase:
        raise NotImplementedError

    def auth_request(self, request, **kwargs):
        raise NotImplementedError

    def get_credentials(self):
        raise NotImplementedError

    @classmethod
    def validate(cls, payload, instance=None):
        raise NotImplementedError

    @classmethod
    def create_auth_config(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def encrypt_payload(cls, payload):
        return cipher.encrypt(json.dumps(payload).encode()).decode()

    @classmethod
    def decrypt_payload(cls, payload):
        return json.loads(cipher.decrypt(payload.encode()).decode())


class HashableAuthBase(AuthBase):
    """
    Wrapper around any AuthBase object to make it hashable.
    Required because lru_cache needs all arguments to be hashable.
    """

    def __init__(self, auth: AuthBase):
        self.auth = auth

    def __hash__(self):
        return hash((self.auth.__class__, tuple(sorted(self.auth.__dict__.items()))))

    def __eq__(self, other):
        return (
            isinstance(other, HashableAuthBase)
            and self.auth.__class__ is other.auth.__class__
            and self.auth.__dict__ == other.auth.__dict__
        )

    def __call__(self, r):
        return self.auth(r)


class BasicAuthHandler(AuthHandler):
    handled_type = "basic"
    username: str
    password: str

    @classmethod
    def validate(cls, payload, instance=None):
        if not payload.get("username"):
            raise ValidationError("Username is required for basic authentication.")
        if not payload.get("password") and not getattr(instance, "pk", None):
            raise ValidationError("Password is required for basic authentication.")
        return payload

    @classmethod
    def create_auth_config(cls, username, password):
        if username is None and password is None:
            return None
        payload = {"username": username, "password": password}
        cls.validate(payload)

        return AuthConfig.objects.create(
            type=cls.handled_type,
            payload=cls.encrypt_payload(payload),
        )

    def _init_from_config(self):
        payload = self.decrypt_payload(self.config.payload)
        self.username = payload.get("username")
        self.password = payload.get("password")

    def get_request_auth(self) -> AuthBase:
        return HashableAuthBase(HTTPBasicAuth(self.username, self.password))

    def auth_request(self, request, **kwargs):
        request.auth = self.get_request_auth()
        return request

    def get_credentials(self):
        return (self.username, self.password)
