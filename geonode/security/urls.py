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

from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.security.views',
                       url(r'^permissions/(?P<resource_id>\d+)$', 'resource_permissions', name='resource_permissions'),
                       url(r'^bulk-permissions/?$', 'set_bulk_permissions', name='bulk_permissions'),
                       url(r'^request-permissions/?$', 'request_permissions', name='request_permissions'),
                       )
