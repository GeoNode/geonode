from django.conf.urls import url, include

from .views import LocationView

urlpatterns = [

    url(r'^', LocationView.as_view(), name='locations'),

]
