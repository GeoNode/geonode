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
from django.conf.urls import url
from . import views

urlpatterns = [  # 'geonode.geoserver.views',
    # REST Endpoints
    url(r'^rest/stores/(?P<store_type>\w+)/$', views.stores, name="gs_stores"),
    url(r'^rest/styles', views.geoserver_proxy, dict(proxy_path='/gs/rest/styles',
                                                     downstream_path='rest/styles'), name="gs_styles"),
    url(r'^rest/workspaces/(?P<workspace>\w+)', views.geoserver_proxy, dict(proxy_path='/gs/rest/workspaces',
                                                                            downstream_path='rest/workspaces'), name="gs_workspaces"),
    url(r'^rest/layers', views.geoserver_proxy, dict(proxy_path='/gs/rest/layers',
                                                     downstream_path='rest/layers'), name="gs_layers"),
    url(r'^rest/imports', views.geoserver_proxy, dict(proxy_path='/gs/rest/imports',
                                                      downstream_path='rest/imports'), name="gs_imports"),
    url(r'^rest/sldservice', views.geoserver_proxy, dict(proxy_path='/gs/rest/sldservice',
                                                         downstream_path='rest/sldservice'), name="gs_sldservice"),

    # OWS Endpoints
    url(r'^ows', views.geoserver_proxy, dict(proxy_path='/gs/ows',
                                             downstream_path='ows'), name='ows_endpoint'),
    url(r'^gwc', views.geoserver_proxy, dict(proxy_path='/gs/gwc',
                                             downstream_path='gwc'), name='gwc_endpoint'),
    url(r'^wms', views.geoserver_proxy, dict(proxy_path='/gs/wms',
                                             downstream_path='wms'), name='wms_endpoint'),
    url(r'^wfs', views.geoserver_proxy, dict(proxy_path='/gs/wfs',
                                             downstream_path='wfs'), name='wfs_endpoint'),
    url(r'^wcs', views.geoserver_proxy, dict(proxy_path='/gs/wcs',
                                             downstream_path='wcs'), name='wcs_endpoint'),
    url(r'^wps', views.geoserver_proxy, dict(proxy_path='/gs/wps',
                                             downstream_path='wps'), name='wps_endpoint'),
    url(r'^pdf', views.geoserver_proxy, dict(proxy_path='/gs/pdf',
                                             downstream_path='pdf'), name='pdf_endpoint'),
    url(r'^(?P<workspace>[^/]*)/(?P<layername>[^/]*)/ows',
        views.geoserver_proxy,
        dict(proxy_path=f'/gs/{settings.DEFAULT_WORKSPACE}', downstream_path='ows')),
    url(r'^(?P<workspace>[^/]*)/(?P<layername>[^/]*)/wms',
        views.geoserver_proxy,
        dict(proxy_path=f'/gs/{settings.DEFAULT_WORKSPACE}', downstream_path='wms')),
    url(r'^(?P<workspace>[^/]*)/(?P<layername>[^/]*)/wfs',
        views.geoserver_proxy,
        dict(proxy_path=f'/gs/{settings.DEFAULT_WORKSPACE}', downstream_path='wfs')),
    url(r'^(?P<workspace>[^/]*)/(?P<layername>[^/]*)/wcs',
        views.geoserver_proxy,
        dict(proxy_path=f'/gs/{settings.DEFAULT_WORKSPACE}', downstream_path='wcs')),

    url(r'^updatelayers/$',
        views.updatelayers, name="updatelayers"),
    url(r'^(?P<layername>[^/]*)/style$',
        views.layer_style, name="layer_style"),
    url(r'^(?P<layername>[^/]*)/style/upload$',
        views.layer_style_upload, name='layer_style_upload'),
    url(r'^(?P<layername>[^/]*)/style/manage$',
        views.layer_style_manage, name='layer_style_manage'),
    url(r'^acls/?$', views.layer_acls, name='layer_acls'),
    url(r'^resolve_user/?$', views.resolve_user,
        name='layer_resolve_user'),
    url(r'^online/?$', views.server_online, name='server_online'),
]
