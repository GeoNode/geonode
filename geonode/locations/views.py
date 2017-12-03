from django.views.generic.base import TemplateView

from geonode.layers.models import Layer
from geonode.layers.views import _resolve_layer
from geonode.class_factory import ClassFactory


class LocationView(TemplateView):

    template_name = "locations/locations.html"

    def get_context_data(self, **kwargs):
        context = super(LocationView, self).get_context_data(**kwargs)
        # context['latest_articles'] = Article.objects.all()[:5]

        layers = Layer.objects.all()

        context['layers'] = layers

        return context
