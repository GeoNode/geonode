from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView


urlpatterns = patterns('',
    (r'^layers/attribute-view/$', TemplateView.as_view(template_name='layers/layer_attribute_view.html')),
)