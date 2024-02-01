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
from django.urls import include, re_path
from django.contrib.auth.decorators import login_required

from .views import DocumentUploadView, DocumentUpdateView
from . import views

js_info_dict = {
    "packages": ("geonode.documents",),
}

urlpatterns = [  # 'geonode.documents.views',
    re_path(r"^(?P<docid>\d+)/download/?$", views.document_download, name="document_download"),
    re_path(r"^(?P<docid>\d+)/link/?$", views.document_link, name="document_link"),
    re_path(r"^(?P<docid>\d+)/replace$", login_required(DocumentUpdateView.as_view()), name="document_replace"),
    re_path(r"^(?P<docid>\d+)/embed/?$", views.document_embed, name="document_embed"),
    re_path(r"^upload/?$", login_required(DocumentUploadView.as_view()), name="document_upload"),
    re_path(r"^(?P<docid>[^/]*)/metadata_detail$", views.document_metadata_detail, name="document_metadata_detail"),
    re_path(r"^(?P<docid>\d+)/metadata$", views.document_metadata, name="document_metadata"),
    re_path(r"^metadata/batch/$", views.document_batch_metadata, name="document_batch_metadata"),
    re_path(r"^(?P<docid>\d+)/metadata_advanced$", views.document_metadata_advanced, name="document_metadata_advanced"),
    re_path(r"^", include("geonode.documents.api.urls")),
]
