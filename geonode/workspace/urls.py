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
from django.conf import settings
from django.views.generic import TemplateView

from geonode.workspace.views import MemberWorkspaceLayer, MemberWorkspaceDocument, MemberWorkspaceMap
from geonode.workspace.views import AdminWorkspaceLayer, AdminWorkspaceDocument, AdminWorkspaceMap, AdminWorkspaceUserList

js_info_dict = {
    'packages': ('geonode.layers',),
}

urlpatterns = patterns(
    'geonode.workspace.views',
    url(r'^member/layer$', MemberWorkspaceLayer.as_view(), name='member-workspace-layer'),
    url(r'^member/document$', MemberWorkspaceDocument.as_view(), name='member-workspace-document'),
    url(r'^member/map$', MemberWorkspaceMap.as_view(), name='member-workspace-map'),
    url(r'^manager/layer$',AdminWorkspaceLayer.as_view(), name='admin-workspace-layer'),
    url(r'^manager/document$', AdminWorkspaceDocument.as_view(), name='admin-workspace-document'),
    url(r'^manager/map$', AdminWorkspaceMap.as_view(), name='admin-workspace-map'),
    url(r'^manager/userlist', AdminWorkspaceUserList.as_view(), name='admin-workspace-user-list'),
    url(r'^manager/(?P<slug>[-\w]+)/member_remove/(?P<username>.+)$', 'remove_group_member', name='remove-group-member'),

)
