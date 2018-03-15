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

from django.conf import settings
from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.geoserver.views',
                       # REST Endpoints
                       url(r'^rest/stores/(?P<store_type>\w+)/$',
                           'stores', name="stores"),
                       (r'^rest/styles', 'geoserver_proxy', dict(proxy_path='/gs/rest/styles',
                                                                 downstream_path='rest/styles')),
                       (r'^rest/workspaces/(?P<workspace>\w+)/styles', 'geoserver_proxy',
                        dict(proxy_path='/gs/rest/workspaces',
                             downstream_path='rest/workspaces')),
                       (r'^rest/layers', 'geoserver_proxy', dict(proxy_path='/gs/rest/layers',
                                                                 downstream_path='rest/layers')),
                       (r'^rest/sldservice', 'geoserver_proxy', dict(proxy_path='/gs/rest/sldservice',
                                                                     downstream_path='rest/sldservice')),

                       # OWS Endpoints
                       url(r'^ows', 'geoserver_proxy', dict(proxy_path='/gs/ows',
                                                            downstream_path='ows'), name='ows_endpoint'),
                       url(r'^wms', 'geoserver_protected_proxy', dict(proxy_path='/gs/wms',
                                                                      downstream_path='wms'), name='wms_endpoint'),
                       url(r'^wfs', 'geoserver_protected_proxy', dict(proxy_path='/gs/wfs',
                                                                      downstream_path='wfs'), name='wfs_endpoint'),
                       url(r'^wcs', 'geoserver_protected_proxy', dict(proxy_path='/gs/wcs',
                                                                      downstream_path='wcs'), name='wcs_endpoint'),
                       url(r'^pdf', 'geoserver_protected_proxy', dict(proxy_path='/gs/pdf',
                                                                      downstream_path='pdf'), name='pdf_endpoint'),
                       url(r'^(?P<workspace>[^/]*)/(?P<layername>[^/]*)/wms',
                           'geoserver_proxy',
                           dict(proxy_path='/gs/%s' % settings.DEFAULT_WORKSPACE, downstream_path='wms')),

                       url(r'^updatelayers/$', 'updatelayers',
                           name="updatelayers"),
                       url(r'^(?P<layername>[^/]*)/style$',
                           'layer_style', name="layer_style"),
                       url(r'^(?P<layername>[^/]*)/style/upload$',
                           'layer_style_upload', name='layer_style_upload'),
                       url(r'^(?P<layername>[^/]*)/style/manage$',
                           'layer_style_manage', name='layer_style_manage'),
                       url(r'^(?P<layername>[^/]*)/edit-check?$',
                           'feature_edit_check',
                           name="feature_edit_check"),
                       url(r'^acls/?$', 'layer_acls', name='layer_acls'),
                       url(r'^resolve_user/?$', 'resolve_user',
                           name='layer_resolve_user'),
                       url(r'^download$', 'layer_batch_download',
                           name='layer_batch_download'),
                       )
