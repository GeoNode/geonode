from django.conf.urls.defaults import *
from django.conf import settings
from staticfiles.urls import staticfiles_urlpatterns
from geonode.sitemap import LayerSitemap, MapSitemap
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('geonode.hoods.views',
        (r'^$', 'create_hood'),
)