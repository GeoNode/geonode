from django.conf.urls import url
from .views import annotations, annotation_details

urlpatterns = [
    url(r'^annotations/(?P<mapid>[0-9]*)$', annotations, name='annotations'),
    url(r'^annotations/(?P<mapid>[0-9]*)/(?P<id>[0-9]*)$', annotations, name='annotations'),
    url(r'^annotations/(?P<id>[0-9]*)/details$', annotation_details, name='annotation_details'),
]
