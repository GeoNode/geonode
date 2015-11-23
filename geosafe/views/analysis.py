import json
import os

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseServerError, HttpResponse
from django.views.generic import (
    ListView, CreateView, DetailView)
from geonode.layers.models import Layer
from geosafe.models import Analysis
from geosafe.forms import (AnalysisCreationForm)
from geosafe.tasks.analysis import if_list
from tastypie.http import HttpBadRequest


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisCreationForm
    template_name = 'geosafe/analysis/create.html'
    context_object_name = 'analysis'

    def get_success_url(self):
        return reverse('analysis-detail', kwargs={'pk':self.object.pk})

    def get_form_kwargs(self):
        kwargs = super(AnalysisCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class AnalysisListView(ListView):
    model = Analysis
    template_name = 'geosafe/analysis/list.html'
    context_object_name = 'analysis_list'

    def get_context_data(self, **kwargs):
        context = super(AnalysisListView, self).get_context_data(**kwargs)
        return context

class AnalysisDetailView(DetailView):
    model = Analysis
    template_name = 'geosafe/analysis/detail.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        context = super(AnalysisDetailView, self).get_context_data(**kwargs)
        return context

def impact_function_filter(request):
    """Ajax Request for filtered available IF
    """
    if request.method != 'GET':
        raise HttpBadRequest

    exposure_id = request.GET.get('exposure_id')
    hazard_id = request.GET.get('hazard_id')

    print exposure_id+' '+hazard_id

    if not (exposure_id and hazard_id):
        raise HttpBadRequest

    try:
        exposure_layer = Layer.objects.get(id=exposure_id)
        hazard_layer = Layer.objects.get(id=hazard_id)

        print exposure_layer
        print hazard_layer

        hazard_file_path = hazard_layer.get_base_file()[0].file.path
        exposure_file_path = exposure_layer.get_base_file()[0].file.path

        print hazard_file_path
        print exposure_file_path

        impact_functions = if_list(
            hazard_file=hazard_file_path,
            exposure_file=exposure_file_path,
            layer_folder=os.path.dirname(hazard_file_path)
        )

        return HttpResponse(
            json.dumps(impact_functions), content_type="application/json")
    except:
        raise HttpResponseServerError

def layer_tiles(request):
    """Ajax request to get layer's url to show in the map.
    """
    if request.method != 'GET':
        raise HttpBadRequest
    layer_id = request.GET.get('layer_id')
    if not layer_id:
        raise HttpBadRequest
    try:
        layer = Layer.objects.get(id=layer_id)
        context = {
            'layer_tiles_url': layer.get_tiles_url(),
            'layer_bbox_x0': float(layer.bbox_x0),
            'layer_bbox_x1': float(layer.bbox_x1),
            'layer_bbox_y0': float(layer.bbox_y0),
            'layer_bbox_y1': float(layer.bbox_y1)
        }
        print context
        return HttpResponse(
            json.dumps(context), content_type="application/json"
        )
    except Exception as e:
        print e
        raise HttpResponseServerError
