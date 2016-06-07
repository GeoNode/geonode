__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'new_views.py'
__date__ = '4/18/16'
__copyright__ = 'imajimatika@gmail.com'


from django.views.generic import CreateView, DetailView
from geonode.maps.models import Map
from geonode.layers.models import Layer


class MapCreateView(CreateView):
    model = Map
    template_name = 'leaflet_maps/map_view.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        # list all required layers
        layers = Layer.objects.all()
        context = {
            'create': True,
            'layers': layers
        }
        return context

    def get_success_url(self):
        pass

    def get_form_kwargs(self):
        kwargs = super(MapCreateView, self).get_form_kwargs()
        return kwargs


class MapDetailView(DetailView):
    model = Map
    template_name = 'leaflet_maps/map_view.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        # list all required layers
        layers = Layer.objects.all()
        context = {
            'create': False,
            'layers': layers,
            'map': Map.objects.get(id=self.kwargs.get("mapid"))
        }
        return context

    def get_object(self):
        return Map.objects.get(id=self.kwargs.get("mapid"))