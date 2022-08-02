#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from geonode.base.auth import (
    visitor_ip_address,
    is_ipaddress_in_whitelist
)


# This backend only raises a permission deined id admin access is forbidden
# It delegates to downstream backends otherwise
class AdminRestrictedAccessBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        if request:
            whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
            if user and user.is_superuser and len(whitelist) > 0:
                visitor_ip = visitor_ip_address(request)
                if not is_ipaddress_in_whitelist(visitor_ip, whitelist):
                    raise PermissionDenied
