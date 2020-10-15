# -*- coding: utf-8 -*-
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

from geonode.monitoring import register_url_event

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
    url(r'^', include('geonode.geoapps.api.urls')),
]
