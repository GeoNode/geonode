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
from . import views

urlpatterns = [  # 'geonode.geoserver.views',
    # REST Endpoints
    url(r'^rest/stores/(?P<store_type>\w+)/$',
        views.stores, name="stores"),
    url(r'^rest/styles', views.geoserver_proxy, dict(proxy_path='/gs/rest/styles',
                                                     downstream_path='rest/styles')),
    url(r'^rest/workspaces/(?P<workspace>\w+)/styles', views.geoserver_proxy,
        dict(proxy_path='/gs/rest/workspaces',
             downstream_path='rest/workspaces')),
    url(r'^rest/layers', views.geoserver_proxy, dict(proxy_path='/gs/rest/layers',
                                                     downstream_path='rest/layers')),
    url(r'^rest/sldservice', views.geoserver_proxy, dict(proxy_path='/gs/rest/sldservice',
                                                         downstream_path='rest/sldservice')),

    # OWS Endpoints
    url(r'^ows', views.geoserver_proxy, dict(proxy_path='/gs/ows',
                                             downstream_path='ows')),
    url(r'^wms', views.geoserver_proxy, dict(proxy_path='/gs/wms',
                                             downstream_path='wms')),
    url(r'^wfs', views.geoserver_proxy, dict(proxy_path='/gs/wfs',
                                             downstream_path='wfs')),
    url(r'^wcs', views.geoserver_proxy, dict(proxy_path='/gs/wcs',
                                             downstream_path='wcs')),

    url(r'^updatelayers/$',
        views.updatelayers, name="updatelayers"),
    url(r'^(?P<layername>[^/]*)/style$',
        views.layer_style, name="layer_style"),
    url(r'^(?P<layername>[^/]*)/style/upload$',
        views.layer_style_upload, name='layer_style_upload'),
    url(r'^(?P<layername>[^/]*)/style/manage$',
        views.layer_style_manage, name='layer_style_manage'),
    url(r'^(?P<layername>[^/]*)/edit-check?$',
        views.feature_edit_check, name="feature_edit_check"),
    url(r'^acls/?$', views.layer_acls, name='layer_acls'),
    url(r'^resolve_user/?$', views.resolve_user,
        name='layer_resolve_user'),
    url(r'^download$', views.layer_batch_download,
        name='layer_batch_download'),
]
