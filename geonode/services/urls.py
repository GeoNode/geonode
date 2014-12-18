# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

urlpatterns = patterns('geonode.services.views',
                       url(r'^$', 'services', name='services'),
                       url(r'^register/$', 'register_service', name="register_service"),
                       url(r'^registerbytype/$', 'register_service_by_type'),
                       url(r'^(?P<service_id>\d+)/$', 'service_detail', name='service_detail'),
                       url(r'^(?P<service_id>\d+)/edit$', 'edit_service', name='edit_service'),
                       url(r'^(?P<service_id>\d+)/remove', 'remove_service', name='remove_service'),
                       url(r'^(?P<service_id>\d+)/ajax-permissions$', 'ajax_service_permissions',
                           name='ajax_service_permissions'),
                       )
