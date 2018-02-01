# rest_framework api

from django.conf.urls import patterns, url
from geonode.geoserver.api.wms import GeoserverWMSListAPIView


urlpatterns = [
    url(r'^get-feature-info$', GeoserverWMSListAPIView.as_view())
]
