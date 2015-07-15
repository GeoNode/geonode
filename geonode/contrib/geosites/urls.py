from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

from geonode.urls import urlpatterns
from .api import api
from .views import site_layer_detail, site_document_detail, site_map_detail, layer_acls, \
                   ajax_login, ajax_lookup, SiteLoginView


# flake8: noqa
urlpatterns = patterns('',
    url(r'^/?$', TemplateView.as_view(template_name='site_index.html'), name='home'),
    url(r'', include(api.urls)),
    # Override the detail pages to respect the sites
    url(r'^gs/acls/?$', layer_acls, name='layer_acls_dep'),
    url(r'^layers/acls/?$', layer_acls, name='layer_acls_dep'),
    url(r'^layers/resolve_user/?$', 'geonode.geoserver.views.resolve_user', name='layer_resolve_user_dep'),
    url(r'^layers/download$', 'geonode.geoserver.views.layer_batch_download', name='layer_batch_download_dep'),
    url(r'^layers/?$', TemplateView.as_view(template_name='layers/layer_list.html'), name='layer_browse'),
    url(r'^layers/upload$', 'geonode.layers.views.layer_upload', name='layer_upload'),
    url(r'^layers/(?P<layername>[^/]*)$', site_layer_detail, name="layer_detail"),
    url(r'^documents/(?P<docid>\d+)$', site_document_detail, name='document_detail'),
    url(r'^maps/(?P<mapid>[^/]\d+)$', site_map_detail, name='map_detail'),
    url(r"^account/login/$", SiteLoginView.as_view(), name="account_login"),
    url(r'^account/ajax_login$', ajax_login, name='account_ajax_login'),
    url(r'^account/ajax_lookup$', ajax_lookup, name='account_ajax_lookup'),
) + urlpatterns

handler403 = 'geonode.views.err403'
