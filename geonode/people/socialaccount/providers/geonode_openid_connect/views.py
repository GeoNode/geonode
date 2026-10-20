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
import logging

from django.conf import settings
from django.utils.module_loading import import_string

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)

from geonode.people.socialaccount.providers.geonode_openid_connect.provider import GenericOpenIDConnectProvider

logger = logging.getLogger(__name__)

# SOCIALACCOUNT_ADAPTER used to be the OAuth2 adapter too, its protocol overrides are no longer applied
if hasattr(import_string(settings.SOCIALACCOUNT_ADAPTER), "complete_login"):
    logger.warning(
        "SOCIALACCOUNT_ADAPTER %s defines complete_login, which is ignored: "
        "move the OAuth2 customizations to the OAUTH2_ADAPTER_CLASS provider setting",
        settings.SOCIALACCOUNT_ADAPTER,
    )

oauth2_login = OAuth2LoginView.adapter_view(GenericOpenIDConnectProvider.oauth2_adapter_class)
oauth2_callback = OAuth2CallbackView.adapter_view(GenericOpenIDConnectProvider.oauth2_adapter_class)
