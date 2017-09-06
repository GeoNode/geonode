from django.conf import settings
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns
from django.conf.urls import patterns, url
urlpatterns = patterns('geonode.certification.views',
    url(r'^(?P<modeltype>[a-zA-Z\.]+)/(?P<modelid>\d+)/certify/?$', 'certify', name="certify"),
    url(r'^(?P<modeltype>[a-zA-Z\.]+)/(?P<modelid>\d+)/uncertify/?$', 'uncertify', name="uncertify"),
)
