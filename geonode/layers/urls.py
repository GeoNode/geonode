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
from geonode.monitoring import register_url_event

from . import views

js_info_dict = {
    'packages': ('geonode.layers',),
}

dataset_list = register_url_event()(TemplateView.as_view(template_name='datasets/dataset_list.html'))

urlpatterns = [
    # 'geonode.layers.views',
    url(r'^$',
        dataset_list,
        {'facet_type': 'dataset', 'is_dataset': True},
        name='dataset_browse'),
    url(r'^upload$', views.dataset_upload, name='dataset_upload'),
    url(r'^upload_metadata$', views.dataset_metadata_upload,
        name='dataset_metadata_upload'),
    url(r'^load_dataset_data$', views.load_dataset_data, name='load_dataset_data'),
    url(r'^(?P<layername>[^/]*)$', views.dataset_detail, name="dataset_detail"),
    url(r'^(?P<layername>[^/]*)/metadata$',
        views.dataset_metadata, name="dataset_metadata"),
    url(r'^(?P<layername>[^/]*)/metadata_advanced$',
        views.dataset_metadata_advanced, name="dataset_metadata_advanced"),
    url(r'^(?P<layername>[^/]*)/remove$',
        views.dataset_remove, name="dataset_remove"),
    url(r'^(?P<granule_id>[^/]*)/(?P<layername>[^/]*)/granule_remove$', views.dataset_granule_remove,
        name="dataset_granule_remove"),
    url(r'^(?P<layername>[^/]*)/replace$',
        views.dataset_replace, name="dataset_replace"),
    url(r'^(?P<layername>[^/]*)/append$',
        views.dataset_append, name="dataset_append"),
    url(r'^(?P<layername>[^/]*)/get$', views.get_dataset, name='get_dataset'),
    url(r'^(?P<layername>[^/]*)/metadata_detail$',
        views.dataset_metadata_detail, name='dataset_metadata_detail'),
    url(r'^(?P<layername>[^/]*)/metadata_upload$',
        views.dataset_metadata_upload, name='dataset_metadata_upload'),
    url(r'^(?P<layername>[^/]+)/embed$',
        views.dataset_embed, name='dataset_embed'),
    url(r'^(?P<layername>[^/]*)/style_upload$',
        views.dataset_sld_upload, name='dataset_sld_upload'),
    url(r'^(?P<layername>[^/]*)/style_edit$',
        views.dataset_sld_edit, name='dataset_sld_edit'),
    url(r'^(?P<layername>[^/]*)/feature_catalogue$',
        views.dataset_feature_catalogue, name='dataset_feature_catalogue'),
    url(r'^metadata/batch/$',
        views.dataset_batch_metadata, name='dataset_batch_metadata'),
    url(r'^permissions/batch/$',
        views.dataset_batch_permissions, name='dataset_batch_permissions'),
    url(r'^autocomplete/$',
        views.LayerAutocomplete.as_view(), name='autocomplete_dataset'),
    url(r'^', include('geonode.layers.api.urls')),
]

# -- Deprecated url routes for Geoserver authentication -- remove after GeoNode 2.1
# -- Use /gs/acls, gs/resolve_user/, gs/download instead
if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.views import dataset_acls, resolve_user
    urlpatterns = [  # 'geonode.geoserver.views',
        url(r'^acls/?$', dataset_acls, name='dataset_acls_dep'),
        url(r'^resolve_user/?$', resolve_user,
            name='dataset_resolve_user_dep'),
    ] + urlpatterns
