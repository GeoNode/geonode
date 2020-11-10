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
from django.views.generic import TemplateView

from geonode import geoserver, qgis_server
from geonode.utils import check_ogc_backend
from geonode.monitoring import register_url_event

from . import views

js_info_dict = {
    'packages': ('geonode.maps', ),
}

new_map_view = views.new_map
existing_map_view = views.map_view

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    new_map_view = views.new_map
    existing_map_view = views.map_view
    map_embed = views.map_embed
    map_edit = views.map_edit
    map_json = views.map_json
    map_thumbnail = views.map_thumbnail

elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    from geonode.maps.qgis_server_views import MapCreateView, \
        MapDetailView, MapEmbedView, MapEditView, MapUpdateView

    new_map_view = MapCreateView.as_view()
    existing_map_view = MapDetailView.as_view()
    map_embed = MapEmbedView.as_view()

    from geonode.maps.qgis_server_views import map_download_qlr, \
        map_download_leaflet, set_thumbnail_map

    map_edit = MapEditView.as_view()
    map_json = MapUpdateView.as_view()
    map_thumbnail = set_thumbnail_map

maps_list = register_url_event()(TemplateView.as_view(template_name='maps/map_list.html'))

urlpatterns = [
    # 'geonode.maps.views',
    url(r'^$',
        maps_list,
        {'facet_type': 'maps'},
        name='maps_browse'),
    url(r'^new$', new_map_view, name="new_map"),
    url(r'^add_layer$', views.add_layer, name='add_layer'),
    url(r'^new/data$', views.new_map_json, name='new_map_json'),
    url(r'^checkurl/?$', views.ajax_url_lookup),
    url(r'^(?P<mapid>[^/]+)$', views.map_detail, name='map_detail'),
    url(r'^(?P<mapid>[^/]+)/view$', existing_map_view, name='map_view'),
    url(r'^(?P<mapid>[^/]+)/edit$', map_edit, name='map_edit'),
    url(r'^(?P<mapid>[^/]+)/data$', map_json, name='map_json'),
    url(r'^(?P<mapid>[^/]+)/wmc$', views.map_wmc, name='map_wmc'),
    url(r'^(?P<mapid>[^/]+)/remove$', views.map_remove, name='map_remove'),
    url(r'^(?P<mapid>[^/]+)/metadata$', views.map_metadata, name='map_metadata'),
    url(r'^(?P<mapid>[^/]+)/metadata_advanced$', views.map_metadata_advanced, name='map_metadata_advanced'),
    url(r'^(?P<mapid>[^/]+)/embed$', map_embed, name='map_embed'),
    url(r'^(?P<mapid>\d+)/thumbnail$', map_thumbnail, name='map_thumbnail'),
    url(r'^embed/$', views.map_embed, name='map_embed'),
    url(r'^metadata/batch/$', views.map_batch_metadata, name='map_batch_metadata'),
    url(r'^(?P<mapid>[^/]*)/metadata_detail$',
        views.map_metadata_detail,
        name='map_metadata_detail'),
    url(r'^(?P<layername>[^/]*)/attributes',
        views.maplayer_attributes,
        name='maplayer_attributes'),
    url(r'^autocomplete/$',
        views.MapAutocomplete.as_view(), name='autocomplete_map'),
]

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    # Add QLR url specific for QGIS Server
    urlpatterns += [
        url(r'^(?P<mapid>[^/]+)/download$',
            views.map_download,
            name='map_download'),
        url(r'^(?P<mapid>[^/]+)/qlr$',
            map_download_qlr,
            name='map_download_qlr'),
        url(r'^(?P<mapid>[^/]+)/download_leaflet',
            map_download_leaflet,
            name='map_download_leaflet'),
    ]
