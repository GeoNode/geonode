
from django.conf.urls import url, include

from geonode.analytics.api.views import (
    LayerLoadListAPIView,
    MapLoadListAPIView,
    VisitorListAPIView,
    PinpointUserActivityListAPIView,
    PinpointUserActivityCreateAPIView,

    VisitorCreateAPIView,
    LayerLoadCreateAPIView,
    MapLoadCreateAPIView,
    MapListAPIView,
    LayerListAPIView,
    DocumentListAPIView,
)

from .views import AnalyticsView

urlpatterns = [

    url(r'^api/user/activity/create/', PinpointUserActivityCreateAPIView.as_view()),
    url(r'^api/user/activity/', PinpointUserActivityListAPIView.as_view()),

    url(r'^api/visitor/create/', VisitorCreateAPIView.as_view()),
    url(r'^api/layer/load/create/', LayerLoadCreateAPIView.as_view()),
    url(r'^api/map/load/create/', MapLoadCreateAPIView.as_view()),

    url(r'maps/$', MapListAPIView.as_view()),
    url(r'layers/$', LayerListAPIView.as_view()),
    url(r'documents/$', DocumentListAPIView.as_view()),
    # url(r'^api/layer/load/', LayerLoadListAPIView.as_view()),
    # url(r'^api/map/load/', MapLoadListAPIView.as_view()),
    # url(r'^api/visitor/', VisitorListAPIView.as_view()),

    url(r'^', AnalyticsView.as_view(), name='analytics'),

]
