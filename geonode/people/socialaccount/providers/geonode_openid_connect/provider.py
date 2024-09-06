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

"""Custom account providers for django-allauth.

These are used in order to extend the default authorization provided by
django-allauth.

"""
from django.conf import settings
from django.utils.module_loading import import_string

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import AuthAction, ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from geonode.people.adapters import GenericOpenIDConnectAdapter

PROVIDER_ID = getattr(settings, "SOCIALACCOUNT_OIDC_PROVIDER", "geonode_openid_connect")


class GenericOpenIDConnectProviderAccount(ProviderAccount):
    def to_str(self):
        dflt = super(GenericOpenIDConnectProviderAccount, self).to_str()
        return self.account.extra_data.get("name", dflt)


class GenericOpenIDConnectProvider(OAuth2Provider):
    id = "geonode_openid_connect"
    name = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("NAME", "GeoNode OpenIDConnect")
    account_class = import_string(
        getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
        .get(PROVIDER_ID, {})
        .get(
            "ACCOUNT_CLASS",
            "geonode.people.socialaccount.providers.geonode_openid_connect.provider.GenericOpenIDConnectProviderAccount",
        )
    )
    oauth2_adapter_class = GenericOpenIDConnectAdapter

    def get_default_scope(self):
        scope = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("SCOPE", "")
        return scope

    def get_auth_params_from_request(self, request, action):
        ret = super(GenericOpenIDConnectProvider, self).get_auth_params_from_request(request, action)
        if action == AuthAction.REAUTHENTICATE:
            ret["prompt"] = (
                getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
                .get(PROVIDER_ID, {})
                .get("AUTH_PARAMS", {})
                .get("prompt", "")
            )
        return ret

    def extract_uid(self, data):
        _uid_field = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("UID_FIELD", None)
        if _uid_field:
            return data.get(_uid_field)
        else:
            return data.get("uid", data.get("sub", data.get("id")))

    def extract_common_fields(self, data):
        _common_fields = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get(PROVIDER_ID, {}).get("COMMON_FIELDS", {})
        __common_fields_data = {}
        for _common_field in _common_fields:
            __common_fields_data[_common_field] = data.get(_common_fields.get(_common_field), "")
        return __common_fields_data

    def extract_email_addresses(self, data):
        addresses = []
        email = data.get("email")
        if email:
            addresses.append(
                EmailAddress(
                    email=email,
                    verified=data.get("email_verified", False),
                    primary=True,
                )
            )
        return addresses


provider_classes = [GenericOpenIDConnectProvider]
