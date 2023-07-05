#########################################################################
#
# Copyright (C) 2023 OSGeo
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
import os

_AZURE_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "")
_AZURE_SOCIALACCOUNT_PROVIDER = {
    "NAME": "Microsoft Azure",
    "SCOPE": [
        "User.Read",
        "openid",
    ],
    "AUTH_PARAMS": {
        "access_type": "online",
        "prompt": "select_account",
    },
    "COMMON_FIELDS": {"email": "mail", "last_name": "surname", "first_name": "givenName"},
    "ACCOUNT_CLASS": "allauth.socialaccount.providers.azure.provider.AzureAccount",
    "ACCESS_TOKEN_URL": f"https://login.microsoftonline.com/{_AZURE_TENANT_ID}/oauth2/v2.0/token",
    "AUTHORIZE_URL": f"https://login.microsoftonline.com/{_AZURE_TENANT_ID}/oauth2/v2.0/authorize",
    "PROFILE_URL": "https://graph.microsoft.com/v1.0/me",
}

_GOOGLE_SOCIALACCOUNT_PROVIDER = {
    "NAME": "Google",
    "SCOPE": [
        "profile",
        "email",
    ],
    "AUTH_PARAMS": {
        "access_type": "online",
        "prompt": "select_account consent",
    },
    "COMMON_FIELDS": {"email": "email", "last_name": "family_name", "first_name": "given_name"},
    "ACCOUNT_CLASS": "allauth.socialaccount.providers.google.provider.GoogleAccount",
    "ACCESS_TOKEN_URL": "https://oauth2.googleapis.com/token",
    "AUTHORIZE_URL": "https://accounts.google.com/o/oauth2/v2/auth",
    "ID_TOKEN_ISSUER": "https://accounts.google.com",
    "OAUTH_PKCE_ENABLED": True,
}

SOCIALACCOUNT_PROVIDERS_DEFS = {"azure": _AZURE_SOCIALACCOUNT_PROVIDER, "google": _GOOGLE_SOCIALACCOUNT_PROVIDER}
