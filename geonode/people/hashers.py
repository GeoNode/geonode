"""
This file includes code originally from the Django project
(https://www.djangoproject.com/), which is licensed under the BSD 3-Clause License.

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

This file is distributed as part of a larger work licensed under the
GNU General Public License version 3 (GPLv3).  Use of this file must
comply with both the above BSD license for the portions derived from Django
and the GPLv3 license for the combined work.
"""

import hashlib
import math
from django.utils.translation import gettext_noop as _
from django.utils.crypto import (
    RANDOM_STRING_CHARS,
    constant_time_compare,
)
from django.contrib.auth.hashers import PBKDF2SHA1PasswordHasher, BasePasswordHasher


def mask_hash(hash, show=6, char="*"):
    """
    Return the given hash, with only the first ``show`` number shown. The
    rest are masked with ``char`` for security reasons.
    """
    masked = hash[:show]
    masked += char * len(hash[show:])
    return masked


def must_update_salt(salt, expected_entropy):
    # Each character in the salt provides log_2(len(alphabet)) bits of entropy.
    return len(salt) * math.log2(len(RANDOM_STRING_CHARS)) < expected_entropy


class SHA1PasswordHasher(BasePasswordHasher):
    """
    The SHA1 password hashing algorithm (not recommended)
    """

    algorithm = "sha1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, password, salt):
        self._check_encode_args(password, salt)
        hash = hashlib.sha1((salt + password).encode()).hexdigest()
        return "%s$%s$%s" % (self.algorithm, salt, hash)

    def decode(self, encoded):
        algorithm, salt, hash = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "hash": hash,
            "salt": salt,
        }

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        encoded_2 = self.encode(password, decoded["salt"])
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("salt"): mask_hash(decoded["salt"], show=2),
            _("hash"): mask_hash(decoded["hash"]),
        }

    def must_update(self, encoded):
        decoded = self.decode(encoded)
        return must_update_salt(decoded["salt"], self.salt_entropy)

    def harden_runtime(self, password, encoded):
        pass


class PBKDF2SHA1WrappedSHA1PasswordHasher(PBKDF2SHA1PasswordHasher):
    """
    A password hasher that wraps SHA1 hashes in a PBKDF2SHA1 hash.
    """

    algorithm = "pbkdf2sha1_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        return super().encode(sha1_hash, salt, iterations)

    def encode(self, password, salt, iterations=None):
        _, _, sha1_hash = SHA1PasswordHasher().encode(password, salt).split("$", 2)
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
