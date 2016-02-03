import json
import logging

import os
import tempfile
import urlparse
from zipfile import ZipFile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseServerError, HttpResponse, \
    HttpResponseBadRequest
from django.views.generic import (
    ListView, CreateView, DetailView)

from geonode.layers.models import Layer
from geosafe.forms import (AnalysisCreationForm)
from geosafe.models import Analysis
from geosafe.tasks.headless.analysis import filter_impact_function

LOGGER = logging.getLogger("geosafe")


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisCreationForm
    template_name = 'geosafe/analysis/create.html'
    context_object_name = 'analysis'

    def get_success_url(self):
        return reverse('geosafe:analysis-detail', kwargs={'pk': self.object.pk})

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
        return HttpResponseBadRequest()

    exposure_id = request.GET.get('exposure_id')
    hazard_id = request.GET.get('hazard_id')

    if not (exposure_id and hazard_id):
        return HttpResponseBadRequest()

    try:
        exposure_layer = Layer.objects.get(id=exposure_id)
        hazard_layer = Layer.objects.get(id=hazard_id)

        hazard_url = Analysis.get_layer_url(hazard_layer)
        exposure_url = Analysis.get_layer_url(exposure_layer)

        async_result = filter_impact_function.delay(
            hazard_url,
            exposure_url)

        impact_functions = async_result.get()

        return HttpResponse(
            json.dumps(impact_functions), content_type="application/json")
    except Exception as e:
        LOGGER.exception(e)
        raise HttpResponseServerError


def layer_tiles(request):
    """Ajax request to get layer's url to show in the map.
    """
    if request.method != 'GET':
        raise HttpResponseBadRequest
    layer_id = request.GET.get('layer_id')
    if not layer_id:
        raise HttpResponseBadRequest
    try:
        layer = Layer.objects.get(id=layer_id)
        context = {
            'layer_tiles_url': layer.get_tiles_url(),
            'layer_bbox_x0': float(layer.bbox_x0),
            'layer_bbox_x1': float(layer.bbox_x1),
            'layer_bbox_y0': float(layer.bbox_y0),
            'layer_bbox_y1': float(layer.bbox_y1)
        }
        return HttpResponse(
            json.dumps(context), content_type="application/json"
        )
    except Exception as e:
        LOGGER.exception(e)
        raise HttpResponseServerError


def layer_metadata(request, layer_id):
    """request to get layer's xml metadata"""
    if request.method != 'GET':
        return HttpResponseBadRequest()
    if not layer_id:
        return HttpResponseBadRequest()
    try:
        layer = Layer.objects.get(id=layer_id)
        base_file, _ = layer.get_base_file()
        if not base_file:
            return HttpResponseServerError()
        base_file_path = base_file.file.path
        xml_file_path = base_file_path.split('.')[0] + '.xml'
        if not os.path.exists(xml_file_path):
            return HttpResponseServerError()
        with open(xml_file_path) as f:
            return HttpResponse(f.read(), content_type='text/xml')

    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def layer_archive(request, layer_id):
    """request to get layer's zipped archive"""
    if request.method != 'GET':
        return HttpResponseBadRequest()

    if not layer_id:
        return HttpResponseBadRequest()

    try:
        layer = Layer.objects.get(id=layer_id)
        base_file, _ = layer.get_base_file()
        if not base_file:
            return HttpResponseServerError
        base_file_path = base_file.file.path
        base_name, _ = os.path.splitext(base_file_path)
        tmp = tempfile.mktemp()
        with ZipFile(tmp, mode='w') as zf:
            for root, dirs, files in os.walk(os.path.dirname(base_file_path)):
                for f in files:
                    f_name = os.path.join(root, f)
                    f_base, f_ext = os.path.splitext(f_name)
                    if f_base == base_name:
                        zf.write(f_name, arcname=f)

        with open(tmp) as f:
            return HttpResponse(f.read(), content_type='application/zip')

    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()
