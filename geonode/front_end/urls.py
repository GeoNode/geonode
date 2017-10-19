from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
    (r'^layers/attribute-view/$', TemplateView.as_view(template_name='layers/layer_attribute_view.html')),
    (r'^api/geoserver-settings/$', views.GeoserverSettings.as_view())
)