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

from geonode.maps.views import MapListView

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    url(r'^$', MapListView.as_view(), name='maps_browse'),
    url(r'^popular/$', MapListView.as_view(
        map_filter="popular_count"
    ), name='maps_browse_popular'),
    url(r'^shared/$', MapListView.as_view(
        map_filter="share_count"
    ), name='maps_browse_shared'),
    url(r'^category/(?P<slug>[-\w]+?)/$', 'maps_category', name='maps_browse_category'),
    url(r'^tag/(?P<slug>[-\w]+?)/$', 'maps_tag', name='maps_browse_tag'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^new$', 'new_map', name="new_map"),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    url(r'^(?P<mapid>\d+)$', 'map_detail', name='map_detail'),
    url(r'^(?P<mapid>\d+)/view$', 'map_view', name='map_view'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
    url(r'^(?P<mapid>\d+)/download$', 'map_download', name='map_download'),
    url(r'^(?P<mapid>\d+)/wmc$', 'map_wmc', name='map_wmc'),
    url(r'^(?P<mapid>\d+)/remove$', 'map_remove', name='map_remove'),
    url(r'^(?P<mapid>\d+)/metadata$', 'map_metadata', name='map_metadata'),
    url(r'^(?P<mapid>\d+)/embed$', 'map_embed', name='map_embed'),
    url(r'^(?P<mapid>\d+)/permissions$', 'map_permissions', name='map_permissions'),
    url(r'^check/$', 'map_download_check', name='map_download_check'),
    url(r'^embed/$', 'map_embed', name='map_embed'),
    url(r'^(?P<layername>[^/]*)/attributes', 'maplayer_attributes', name='maplayer_attributes'),
    #url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
)
