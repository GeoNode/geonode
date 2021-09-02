# ##############################################################################
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
# ##############################################################################

from geonode import geoserver  # noqa
from geonode.utils import check_ogc_backend
from django.conf.urls import url, include
from django.views.generic import TemplateView
from geonode.base import register_url_event

from . import views

js_info_dict = {
    'packages': ('geonode.layers',),
}

layers_list = register_url_event()(TemplateView.as_view(template_name='layers/layer_list.html'))

urlpatterns = [
    # 'geonode.layers.views',
    url(r'^$',
        layers_list,
        {'facet_type': 'layers', 'is_layer': True},
        name='layer_browse'),
    url(r'^upload$', views.layer_upload, name='layer_upload'),
    url(r'^upload_metadata$', views.layer_metadata_upload,
        name='layer_metadata_upload'),
    url(r'^upload_style$', views.layer_sld_upload, name='layer_sld_upload'),
    url(r'^(?P<layername>[^/]*)$', views.layer_detail, name="layer_detail"),
    url(r'^(?P<layername>[^/]*)/metadata$',
        views.layer_metadata, name="layer_metadata"),
    url(r'^(?P<layername>[^/]*)/metadata_advanced$',
        views.layer_metadata_advanced, name="layer_metadata_advanced"),
    url(r'^(?P<layername>[^/]*)/remove$',
        views.layer_remove, name="layer_remove"),
    url(r'^(?P<granule_id>[^/]*)/(?P<layername>[^/]*)/granule_remove$', views.layer_granule_remove,
        name="layer_granule_remove"),
    url(r'^(?P<layername>[^/]*)/replace$',
        views.layer_replace, name="layer_replace"),
    url(r'^(?P<layername>[^/]*)/append$',
        views.layer_append, name="layer_append"),
    url(r'^(?P<layername>[^/]*)/get$', views.get_layer, name='get_layer'),
    url(r'^(?P<layername>[^/]*)/metadata_detail$',
        views.layer_metadata_detail, name='layer_metadata_detail'),
    url(r'^(?P<layername>[^/]*)/metadata_upload$',
        views.layer_metadata_upload, name='layer_metadata_upload'),
    url(r'^(?P<layername>[^/]+)/embed$',
        views.layer_embed, name='layer_embed'),
    url(r'^(?P<layername>[^/]*)/style_upload$',
        views.layer_sld_upload, name='layer_sld_upload'),
    url(r'^(?P<layername>[^/]*)/style_edit$',
        views.layer_sld_edit, name='layer_sld_edit'),
    url(r'^(?P<layername>[^/]*)/layer_export$',
        views.layer_export, name='layer_export'),
    url(r'^(?P<layername>[^/]*)/feature_catalogue$',
        views.layer_feature_catalogue, name='layer_feature_catalogue'),
    url(r'^metadata/batch/$',
        views.layer_batch_metadata, name='layer_batch_metadata'),
    url(r'^permissions/batch/$',
        views.layer_batch_permissions, name='layer_batch_permissions'),
    url(r'^autocomplete/$',
        views.LayerAutocomplete.as_view(), name='autocomplete_layer'),
    url(r'^', include('geonode.layers.api.urls')),
]

# -- Deprecated url routes for Geoserver authentication -- remove after GeoNode 2.1
# -- Use /gs/acls, gs/resolve_user/, gs/download instead
if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.views import layer_acls, resolve_user
    urlpatterns = [  # 'geonode.geoserver.views',
        url(r'^acls/?$', layer_acls, name='layer_acls_dep'),
        url(r'^resolve_user/?$', resolve_user,
            name='layer_resolve_user_dep'),
    ] + urlpatterns
