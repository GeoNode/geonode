# rest_framework api
from .wfs import GeoserverWFSListAPIView, GeoserverCreateLayerByFeature
from .wms import GeoserverWMSGetFeatureInfoListAPIView
from django.conf.urls import patterns, url


urlpatterns = [
    url(r'^get-feature-info$', GeoserverWMSGetFeatureInfoListAPIView.as_view()),
    url(r'^wfs/create-layer/$', GeoserverCreateLayerByFeature.as_view()),
    url(r'^wfs/with-geometry/$', GeoserverWFSListAPIView.as_view(), {'include_geometry':True}),    
    url(r'^wfs/$', GeoserverWFSListAPIView.as_view())    
]
