from django.conf.urls import url, include

from .views import LocationView
from api.views import NearestPointAPIView

urlpatterns = [

    # call: locations/api/nearestpoint
    url(r'^api/nearestpoint', NearestPointAPIView.as_view()),

    url(r'^', LocationView.as_view(), name='locations'),

]
