#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django.conf.urls import url, include
from django.views.generic import TemplateView

from geonode.base import register_url_event

from . import views

js_info_dict = {
    'packages': ('geonode.geoapps', ),
}

apps_list = register_url_event()(TemplateView.as_view(template_name='apps/app_list.html'))


urlpatterns = [
    # 'geonode.geoapps.views',
    url(r'^$',
        apps_list,
        {'facet_type': 'geoapps'},
        name='apps_browse'),
    url(r'^new$', views.new_geoapp, name="new_geoapp"),
    url(r'^preview/(?P<geoappid>[^/]*)$', views.geoapp_detail, name="geoapp_detail"),
    url(r'^preview/(?P<geoappid>\d+)/metadata$', views.geoapp_metadata, name='geoapp_metadata'),
    url(r'^preview/(?P<geoappid>[^/]*)/metadata_detail$',
        views.geoapp_metadata_detail, name='geoapp_metadata_detail'),
    url(r'^preview/(?P<geoappid>\d+)/metadata_advanced$',
        views.geoapp_metadata_advanced, name='geoapp_metadata_advanced'),
    url(r'^(?P<geoappid>\d+)/remove$', views.geoapp_remove, name="geoapp_remove"),
    url(r'^(?P<geoappid>[^/]+)/view$', views.geoapp_edit, name='geoapp_view'),
    url(r'^(?P<geoappid>[^/]+)/edit$', views.geoapp_edit, name='geoapp_edit'),
    url(r'^(?P<geoappid>[^/]+)/update$', views.geoapp_edit,
        {'template': 'apps/app_update.html'}, name='geoapp_update'),
    url(r'^(?P<geoappid>[^/]+)/embed$', views.geoapp_edit,
        {'template': 'apps/app_embed.html'}, name='geoapp_embed'),
    url(r'^(?P<geoappid>[^/]+)/download$', views.geoapp_edit,
        {'template': 'apps/app_download.html'}, name='geoapp_download'),
    url(r'^', include('geonode.geoapps.api.urls')),
]
