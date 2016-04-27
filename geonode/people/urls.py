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
from django.views.generic import TemplateView

urlpatterns = patterns('geonode.people.views',
                       url(r'^$', TemplateView.as_view(template_name='people/profile_list.html'),
                           name='profile_browse'),
                       url(r"^edit/$", "profile_edit", name="profile_edit"),
                       url(r"^edit/(?P<username>[^/]*)$", "profile_edit", name="profile_edit"),
                       url(r"^profile/(?P<username>[^/]*)/$", "profile_detail", name="profile_detail"),
                       url(r'^forgotname', 'forgot_username', name='forgot_username'),
                       )
