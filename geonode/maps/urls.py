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
from django.views.generic import TemplateView

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
                       url(r'^$', TemplateView.as_view(template_name='maps/map_list.html'), name='maps_browse'),
                       url(r'^new$', 'new_map', name="new_map"),
                       url(r'^new/data$', 'new_map_json', name='new_map_json'),
                       url(r'^checkurl/?$', 'ajax_url_lookup'),
                       url(r'^snapshot/create/?$', 'snapshot_create'),
                       url(r'^(?P<mapid>[^/]+)$', 'map_detail', name='map_detail'),
                       url(r'^(?P<mapid>[^/]+)/view$', 'map_view', name='map_view'),
                       url(r'^(?P<mapid>[^/]+)/data$', 'map_json', name='map_json'),
                       url(r'^(?P<mapid>[^/]+)/download$', 'map_download', name='map_download'),
                       url(r'^(?P<mapid>[^/]+)/wmc$', 'map_wmc', name='map_wmc'),
                       url(r'^(?P<mapid>[^/]+)/wms$', 'map_wms', name='map_wms'),
                       url(r'^(?P<mapid>[^/]+)/remove$', 'map_remove', name='map_remove'),
                       url(r'^(?P<mapid>[^/]+)/metadata$', 'map_metadata', name='map_metadata'),
                       url(r'^(?P<mapid>[^/]+)/embed$', 'map_embed', name='map_embed'),
                       url(r'^(?P<mapid>[^/]+)/history$', 'ajax_snapshot_history'),
                       url(r'^(?P<mapid>\d+)/thumbnail$', 'map_thumbnail', name='map_thumbnail'),
                       url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/view$', 'map_view'),
                       url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/info$', 'map_detail'),
                       url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/embed/?$', 'map_embed'),
                       url(r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/data$', 'map_json', name='map_json'),
                       url(r'^check/$', 'map_download_check', name='map_download_check'),
                       url(r'^embed/$', 'map_embed', name='map_embed'),
                       url(r'^(?P<layername>[^/]*)/attributes', 'maplayer_attributes', name='maplayer_attributes'),
                       # url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
                       )
