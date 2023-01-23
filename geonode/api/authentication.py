#########################################################################
#
# Copyright (C) 2019 OSGeo
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
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken
from tastypie.authentication import Authentication

from geonode.api.views import verify_access_token
from geonode.base.auth import get_token_from_auth_header


class OAuthAuthentication(Authentication):
    def extract_auth_header(self, request):
        auth_header = None
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION", request.META.get("HTTP_AUTHORIZATION2"))
        except KeyError:
            pass
        return auth_header

    def token_is_valid(self, token):
        valid = False
        try:
            verify_access_token(None, token)
            valid = True
        except Exception:
            pass
        return valid

    def is_authenticated(self, request, **kwargs):
        user = AnonymousUser()
        authenticated = False
        if "HTTP_AUTHORIZATION" in request.META:
            auth_header = self.extract_auth_header(request)
            if auth_header:
                access_token = get_token_from_auth_header(auth_header)
                if self.token_is_valid(access_token):
                    obj = AccessToken.objects.get(token=access_token)
                    user = obj.user
                    authenticated = True
        request.user = user
        return authenticated
