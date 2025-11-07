#########################################################################
#
# Copyright (C) 2025 OSGeo
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
from django.conf import settings
from geonode.base.auth import get_or_create_token
from geonode.security.request_configuration_registry import BaseRequestConfigurationRuleHandler


class BaseConfigurationRuleHandler(BaseRequestConfigurationRuleHandler):
    """
    Base handler for configuration rules.
    """

    def get_rules(self, user):
        rules = []
        token_obj = get_or_create_token(user)
        access_token = token_obj.token

        rules.extend(
            [
                {
                    "urlPattern": f"{settings.GEOSERVER_WEB_UI_LOCATION.rstrip('/')}/.*",
                    "params": {"access_token": access_token},
                },
                {"urlPattern": f"{settings.SITEURL.rstrip('/')}/gs.*", "params": {"access_token": access_token}},
                {
                    "urlPattern": f"{settings.SITEURL.rstrip('/')}/api/v2.*",
                    "headers": {"Authorization": f"Bearer {access_token}"},
                },
            ]
        )
        return rules
