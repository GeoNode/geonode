import json

import os
import logging
import tempfile
from zipfile import ZipFile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseServerError, HttpResponse, \
    HttpResponseBadRequest, HttpResponseRedirect
from django.views.generic import (
    ListView, CreateView, DetailView)

from geonode.layers.models import Layer
from geosafe.forms import (AnalysisCreationForm)
from geosafe.models import Analysis, Metadata
from geosafe.signals import analysis_post_save
from geosafe.tasks.headless.analysis import filter_impact_function

LOGGER = logging.getLogger("geosafe")


logger = logging.getLogger("geonode.geosafe.analysis")


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisCreationForm
    template_name = 'geosafe/analysis/create.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        # list all required layers
        def retrieve_layers(purpose, category=None):
            if category:
                metadatas = Metadata.objects.filter(
                    layer_purpose=purpose, category=category)
            else:
                metadatas = Metadata.objects.filter(
                    layer_purpose=purpose)
            return [m.layer for m in metadatas]
        exposure_population = retrieve_layers('exposure', 'population')
        exposure_road = retrieve_layers('exposure', 'road')
        exposure_building = retrieve_layers('exposure', 'structure')
        hazard_flood = retrieve_layers('hazard', 'flood')
        hazard_earthquake = retrieve_layers('hazard', 'earthquake')
        hazard_volcano = retrieve_layers('hazard', 'volcano')
        impact_layers = retrieve_layers('impact')
        try:
            analysis = Analysis.objects.get(id=self.kwargs.get('pk'))
        except:
            analysis = None
        context = super(AnalysisCreateView, self).get_context_data(**kwargs)
        context.update(
            {
                'exposure_population': exposure_population,
                'exposure_road': exposure_road,
                'exposure_building': exposure_building,
                'hazard_earthquake': hazard_earthquake,
                'hazard_flood': hazard_flood,
                'hazard_volcano': hazard_volcano,
                'impact_layers': impact_layers,
                'analysis': analysis,
            }
        )
        return context

    def get_success_url(self):
        kwargs = {
            'pk': self.object.pk
        }
        return reverse('geosafe:analysis-create', kwargs=kwargs)

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
        raise HttpResponseServerError()


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


def layer_list(request, layer_purpose, layer_category):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    if not layer_purpose or not layer_category:
        return HttpResponseBadRequest()

    try:
        metadatas = Metadata.objects.filter(
            layer_purpose=layer_purpose, category=layer_category)
        layers = []
        for m in metadatas:
            layer_obj = dict()
            layer_obj['id'] = m.layer.id
            layer_obj['name'] = m.layer.name
            layers += layer_obj

        return HttpResponse(
            json.dumps(layers), content_type="application/json")

    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def rerun_analysis(request, analysis_id=None):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    if not analysis_id:
        analysis_id = request.POST.get('analysis_id')

    if not analysis_id:
        return HttpResponseBadRequest()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis_post_save(None, analysis, True)
        return HttpResponseRedirect(
            reverse('geosafe:analysis-detail', kwargs={'pk': analysis.pk})
        )
    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def analysis_json(request, analysis_id):
    """Return the status of an analysis

    :param request:
    :param analysis_id:
    :return:
    """
    if request.method != 'GET':
        return HttpResponseBadRequest()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        retval = {
            'analysis_id': analysis_id,
            'impact_layer_id': analysis.impact_layer_id
        }
        return HttpResponse(
            json.dumps(retval), content_type="application/json")
    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def toggle_analysis_saved(request, analysis_id):
    """Toggle the state of keep of analysis

    :param request:
    :param analysis_id:
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.keep = not analysis.keep
        analysis.save()
        return HttpResponseRedirect(reverse('geosafe:analysis-list'))
    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def serve_files(file_stream, content_type, filename):
    response = HttpResponse(
        file_stream,
        content_type=content_type)
    response['Content-Disposition'] = 'inline; filename="%s";' % filename
    return response


def download_report(request, analysis_id, data_type='map'):
    """Download the pdf files of the analysis

    :param request:
    :param analysis_id:
    :param data_type: can be 'map' or 'table'
    """
    if request.method != 'GET':
        return HttpResponseBadRequest()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        layer_title = analysis.impact_layer.title
        if data_type == 'map':
            return serve_files(
                analysis.report_map.read(),
                'application/pdf',
                '%s_map.pdf' % layer_title)
        elif data_type == 'table':
            return serve_files(
                analysis.report_table.read(),
                'application/pdf',
                '%s_table.pdf' % layer_title)
        return HttpResponseServerError()
    except:
        return HttpResponseServerError()
