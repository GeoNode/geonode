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

from django.conf.urls import url
from django.conf import settings
from django.views.generic import TemplateView

from geonode.contrib.edit_data import views as edit_data


urlpatterns = [
    url(r'^(?P<layername>[^/]*)/edit_data$', edit_data.edit_data, name="edit_data"),
    url(r'^save_edits$', edit_data.save_edits, name='save_edits'),
    url(r'^delete_edits$', edit_data.delete_edits, name='delete_edits'),
    url(r'^save_geom_edits$', edit_data.save_geom_edits, name='save_geom_edits'),
    url(r'^save_added_row$', edit_data.save_added_row, name='save_added_row'),
]
