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

from geonode import geoserver, qgis_server
from geonode.utils import check_ogc_backend

js_info_dict = {
    'packages': ('geonode.maps', ),
}

new_map_view = 'new_map'
existing_map_view = 'map_view'

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    new_map_view = 'new_map'
    existing_map_view = 'map_view'
    map_embed = 'map_embed'
    map_edit = 'map_edit'
    map_json = 'map_json'
    map_thumbnail = 'map_thumbnail'

elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    from geonode.maps.qgis_server_views import MapCreateView, \
        MapDetailView, MapEmbedView, MapEditView, MapUpdateView

    new_map_view = MapCreateView.as_view()
    existing_map_view = MapDetailView.as_view()
    map_embed = MapEmbedView.as_view()

    from geonode.maps.qgis_server_views import map_download_qlr, \
        map_download_leaflet, set_thumbnail_map

    map_download_qlr = map_download_qlr
    map_download_leaflet = map_download_leaflet
    map_edit = MapEditView.as_view()
    map_json = MapUpdateView.as_view()
    map_thumbnail = set_thumbnail_map

urlpatterns = patterns(
    'geonode.maps.views',
    url(r'^$',
        TemplateView.as_view(template_name='maps/map_list.html'),
        {'facet_type': 'maps'},
        name='maps_browse'),
    url(r'^new$', new_map_view, name="new_map"),
    url(r'^add_layer$', 'add_layer', name='add_layer'),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    url(r'^checkurl/?$', 'ajax_url_lookup'),
    url(r'^snapshot/create/?$', 'snapshot_create'),
    url(r'^(?P<mapid>[^/]+)$', 'map_detail', name='map_detail'),
    url(r'^(?P<mapid>[^/]+)/view$', existing_map_view, name='map_view'),
    url(r'^(?P<mapid>[^/]+)/edit$', map_edit, name='map_edit'),
    url(r'^(?P<mapid>[^/]+)/data$', map_json, name='map_json'),
    url(r'^(?P<mapid>[^/]+)/download$', 'map_download', name='map_download'),
    url(r'^(?P<mapid>[^/]+)/wmc$', 'map_wmc', name='map_wmc'),
    url(r'^(?P<mapid>[^/]+)/wms$', 'map_wms', name='map_wms'),
    url(r'^(?P<mapid>[^/]+)/remove$', 'map_remove', name='map_remove'),
    url(r'^(?P<mapid>[^/]+)/metadata$', 'map_metadata', name='map_metadata'),
    url(r'^(?P<mapid>[^/]+)/metadata_advanced$', 'map_metadata_advanced', name='map_metadata_advanced'),
    url(r'^(?P<mapid>[^/]+)/embed$', map_embed, name='map_embed'),
    url(r'^(?P<mapid>[^/]+)/embed_widget$', 'map_embed_widget', name='map_embed_widget'),
    url(r'^(?P<mapid>[^/]+)/history$', 'ajax_snapshot_history'),
    url(r'^(?P<mapid>\d+)/thumbnail$', map_thumbnail, name='map_thumbnail'),
    url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/view$', 'map_view'),
    url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/info$',
        'map_detail'),
    url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/embed/?$',
        'map_embed'),
    url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/data$',
        'map_json',
        name='map_json'),
    url(r'^check/$', 'map_download_check', name='map_download_check'),
    url(r'^embed/$', 'map_embed', name='map_embed'),
    url(r'^metadata/batch/(?P<ids>[^/]*)/$', 'map_batch_metadata', name='map_batch_metadata'),
    url(r'^(?P<mapid>[^/]*)/metadata_detail$',
        'map_metadata_detail',
        name='map_metadata_detail'),
    url(r'^(?P<layername>[^/]*)/attributes',
        'maplayer_attributes',
        name='maplayer_attributes'),
    # url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
)

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    # Add QLR url specific for QGIS Server
    urlpatterns += [
        url(r'^(?P<mapid>[^/]+)/qlr$',
            map_download_qlr,
            name='map_download_qlr',
            prefix='geonode.maps.views'),
        url(r'^(?P<mapid>[^/]+)/download_leaflet',
            map_download_leaflet,
            name='map_download_leaflet',
            prefix='geonode.maps.views'),
    ]
