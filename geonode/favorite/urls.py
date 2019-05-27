# -*- coding: utf-8 -*-
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

from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^document/(?P<id>\d+)$',
        views.favorite, {'subject': 'document'},
        name='add_favorite_document'
    ),
    url(
        r'^map/(?P<id>\d+)$',
        views.favorite, {'subject': 'map'},
        name='add_favorite_map'
    ),
    url(
        r'^layer/(?P<id>\d+)$',
        views.favorite, {'subject': 'layer'},
        name='add_favorite_layer'
    ),
    url(
        r'^user/(?P<id>\d+)$',
        views.favorite, {'subject': 'user'},
        name='add_favorite_user'
    ),
    url(
        r'^(?P<id>\d+)/delete$',
        views.delete_favorite,
        name='delete_favorite'
    ),
    url(
        r'^list/$',
        views.get_favorites,
        name='favorite_list'
    ),
]
