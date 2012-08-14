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

from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    url(r'^$', 'maps_browse', name='maps_browse'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^new$', 'new_map', name="new_map"),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    url(r'^(?P<mapid>\d+)$', 'map_detail', name='map_detail'),
    url(r'^(?P<mapid>\d+)/view$', 'map_view', name='map_view'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
    url(r'^(?P<mapid>\d+)/download$', 'map_download', name='map_download'),
    url(r'^(?P<mapid>\d+)/remove$', 'map_remove', name='map_remove'),
    url(r'^(?P<mapid>\d+)/metadata$', 'map_metadata', name='map_metadata'),
    url(r'^(?P<mapid>\d+)/embed$', 'map_embed', name='map_embed'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'map_ajax_permissions', name='map_ajax_permissions'),
    url(r'^check/$', 'map_download_check', name='map_download_check'),
    url(r'^embed/$', 'map_embed', name='map_embed'),
    #url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
)
