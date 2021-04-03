# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.oauth2_validators import OAuth2Validator

import json
import base64
import hashlib
import logging

from datetime import datetime, timedelta

from django.utils import dateformat, timezone

from jwcrypto import jwk, jwt

log = logging.getLogger(__name__)


class OIDCValidator(OAuth2Validator):

    """ e.g.
        Check username and password correspond to a valid and active User, if fails
        try Facebook token authentication
    def validate_user(self, username, password, client, request, *args, **kwargs):
        u = authenticate(username=username, password=password)
        if u is None or not u.is_active:
           u = authenticate_with_facebook()

        if u is not none and u.is_active:
           request.user = u
           return True

        return False
    """

    def get_authorization_code_nonce(self, client_id, code, redirect_uri, request):
        return None

    def get_id_token(self, token, token_handler, request):

        key = jwk.JWK.from_pem(oauth2_settings.OIDC_RSA_PRIVATE_KEY.encode("utf8"))

        # TODO: http://openid.net/specs/openid-connect-core-1_0.html#HybridIDToken2
        # Save the id_token on database bound to code when the request come to
        # Authorization Endpoint and return the same one when request come to
        # Token Endpoint

        # TODO: Check if at this point this request parameters are alredy validated

        expiration_time = timezone.now() + timedelta(seconds=oauth2_settings.ID_TOKEN_EXPIRE_SECONDS)
        # Required ID Token claims
        claims = {
            "iss": oauth2_settings.OIDC_ISS_ENDPOINT,
            "sub": str(request.user.id),
            "aud": request.client_id,
            "exp": int(dateformat.format(expiration_time, "U")),
            "iat": int(dateformat.format(datetime.utcnow(), "U")),
            "auth_time": int(dateformat.format(request.user.last_login, "U"))
        }

        nonce = getattr(request, "nonce", None)
        if nonce:
            claims["nonce"] = nonce

        # TODO: create a function to check if we should add at_hash
        # http://openid.net/specs/openid-connect-core-1_0.html#CodeIDToken
        # http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDToken
        # if request.grant_type in 'authorization_code' and 'access_token' in token:
        if (request.grant_type == "authorization_code" and "access_token" in token) or \
                request.response_type == "code id_token token" or \
                (request.response_type == "id_token token" and "access_token" in token):
            acess_token = token["access_token"]
            sha256 = hashlib.sha256(acess_token.encode("ascii"))
            bits128 = sha256.hexdigest()[:16]
            at_hash = base64.urlsafe_b64encode(bits128.encode("ascii"))
            claims['at_hash'] = at_hash.decode("utf8")

        # TODO: create a function to check if we should include c_hash
        # http://openid.net/specs/openid-connect-core-1_0.html#HybridIDToken
        if request.response_type in ("code id_token", "code id_token token"):
            code = token["code"]
            sha256 = hashlib.sha256(code.encode("ascii"))
            bits256 = sha256.hexdigest()[:32]
            c_hash = base64.urlsafe_b64encode(bits256.encode("ascii"))
            claims["c_hash"] = c_hash.decode("utf8")

        jwt_token = jwt.JWT(header=json.dumps({"alg": "RS256"}, default=str), claims=json.dumps(claims, default=str))
        jwt_token.make_signed_token(key)

        id_token = self._save_id_token(jwt_token, request, expiration_time)
        # this is needed by django rest framework
        request.access_token = id_token
        request.id_token = id_token

        return jwt_token.serialize()
