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

from django.urls import re_path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from .views import ProfileAutocomplete, SetUserLayerPermission
from . import views


urlpatterns = [  # 'geonode.people.views',
    re_path(r"^$", TemplateView.as_view(template_name="people/profile_list.html"), name="profile_browse"),
    re_path(r"^edit/$", views.profile_edit, name="profile_edit"),
    re_path(r"^edit/(?P<username>[^/]*)$", views.profile_edit, name="profile_edit"),
    re_path(r"^profile/(?P<username>[^/]*)/$", views.profile_detail, name="profile_detail"),
    re_path(r"^forgotname", views.forgot_username, name="forgot_username"),
    re_path(r"^autocomplete/$", login_required(ProfileAutocomplete.as_view()), name="autocomplete_profile"),
    re_path(r"^dataset/permission/$", SetUserLayerPermission.as_view(), name="set_user_dataset_permissions"),
]
