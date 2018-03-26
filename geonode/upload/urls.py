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
from geonode.upload.views import UploadFileCreateView, UploadFileDeleteView

from . import views

urlpatterns = [  # 'geonode.upload.views',
    url(r'^new/$', UploadFileCreateView.as_view(),
        name='data_upload_new'),
    url(r'^progress$', views.data_upload_progress,
        name='data_upload_progress'),
    url(r'^(?P<step>\w+)?$', views.view, name='data_upload'),
    url(r'^delete/(?P<id>\d+)?$',
        views.delete, name='data_upload_delete'),
    url(r'^remove/(?P<pk>\d+)$',
        UploadFileDeleteView.as_view(), name='data_upload_remove'),
]
