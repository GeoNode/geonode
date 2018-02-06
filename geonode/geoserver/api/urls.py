# rest_framework api
from .wfs import GeoserverWFSListAPIView
from .wms import GeoserverWMSGetFeatureInfoListAPIView
from django.conf.urls import patterns, url


urlpatterns = [
    url(r'^get-feature-info$', GeoserverWMSGetFeatureInfoListAPIView.as_view()),
    url(r'^wfs/$', GeoserverWFSListAPIView.as_view())
    
]
