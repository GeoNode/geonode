# rest_framework api
from django.conf.urls import patterns, url
import views


urlpatterns = [
    url(r'^logs/$', views.LogsListAPIView.as_view()), 
]
