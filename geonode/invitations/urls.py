#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django.urls import re_path

import invitations
from . import views

app_name = "geonode.invitations"
urlpatterns = [
    re_path(r"^geonode-send-invite/$", views.GeoNodeSendInvite.as_view(), name="geonode-send-invite"),
    re_path(r"^send-json-invite/$", invitations.views.SendJSONInvite.as_view(), name="send-json-invite"),
    re_path(r"^accept-invite/(?P<key>\w+)/?$", invitations.views.AcceptInvite.as_view(), name="accept-invite"),
]
