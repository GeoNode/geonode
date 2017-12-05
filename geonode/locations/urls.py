from django.conf.urls import url, include

from .views import LocationView, LayersAttributesAPIView

urlpatterns = [

    url(r'^api/layers/attributes/', LayersAttributesAPIView.as_view()),

    url(r'^', LocationView.as_view(), name='locations'),

]
