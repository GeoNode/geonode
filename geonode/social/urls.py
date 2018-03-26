# -*- coding: utf-8 -*-
#
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
#

from django.conf.urls import url
from geonode.social.views import RecentActivity, UserActivity

urlpatterns = [  # '',
    url(r'^recent-activity$',
        RecentActivity.as_view(), name='recent-activity'),
    url(r'^user-activity/(?P<actor>[^/]*)$',
        UserActivity.as_view(), name='user-activity'),
]
