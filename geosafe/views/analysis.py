import json

import os
import logging
import tempfile
from zipfile import ZipFile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http.response import HttpResponseServerError, HttpResponse, \
    HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import (
    ListView, CreateView, DetailView)

from geonode.layers.models import Layer
from geosafe.forms import (AnalysisCreationForm)
from geosafe.models import Analysis, Metadata
from geosafe.signals import analysis_post_save
from geosafe.tasks.headless.analysis import filter_impact_function

LOGGER = logging.getLogger("geosafe")


logger = logging.getLogger("geonode.geosafe.analysis")


def retrieve_layers(purpose, category=None, bbox=None):
    """List all required layers"""

    if not category:
        category = None
    if bbox:
        bbox = json.loads(bbox)
        intersect = (
            Q(layer__bbox_x0__lte=bbox[2]) &
            Q(layer__bbox_x1__gte=bbox[0]) &
            Q(layer__bbox_y0__lte=bbox[3]) &
            Q(layer__bbox_y1__gte=bbox[1])
        )
        metadatas = Metadata.objects.filter(
            Q(layer_purpose=purpose),
            Q(category=category),
            intersect
        )
    else:
        metadatas = Metadata.objects.filter(
            layer_purpose=purpose, category=category)
    return [m.layer for m in metadatas]


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisCreationForm
    template_name = 'geosafe/analysis/create.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        purposes = [
            {
                'name': 'exposure',
                'categories': ['population', 'road', 'structure'],
            },
            {
                'name': 'hazard',
                'categories': ['flood', 'earthquake', 'volcano'],
            }
        ]
        sections = [];
        for p in purposes:
            categories = []
            for c in p.get('categories'):
                layers = retrieve_layers(p.get('name'), c)
                category = {
                    'name': c,
                    'layers': layers
                }
                categories.append(category)
            section = {
                'name': p.get('name'),
                'categories': categories
            }
            sections.append(section)

        impact_layers = retrieve_layers('impact')
        sections.append({
            'name': 'impact',
            'categories': [
                {
                    'name': 'impact',
                    'layers': impact_layers
                }
            ]
        })
        try:
            analysis = Analysis.objects.get(id=self.kwargs.get('pk'))
        except:
            analysis = None
        context = super(AnalysisCreateView, self).get_context_data(**kwargs)
        context.update(
            {
                'sections': sections,
                'analysis': analysis,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        super(AnalysisCreateView, self).post(request, *args, **kwargs)
        return HttpResponse(json.dumps({
            'success': True,
            'redirect': self.get_success_url()
        }), content_type='application/json')

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
    queryset = Analysis.objects.all().order_by("-impact_layer__date")

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
        return HttpResponse(
            json.dumps([]), content_type="application/json")

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


def is_bbox_intersects(bbox_1, bbox_2):
    """

    bbox is in the format: (x0,y0, x1, y1)

    :param bbox_1:
    :param bbox_2:
    :return:
    """
    points = [
        (bbox_1[0], bbox_1[1]),
        (bbox_1[0], bbox_1[3]),
        (bbox_1[2], bbox_1[1]),
        (bbox_1[2], bbox_1[3])
        ]
    for p in points:
        if bbox_2[0] <= p[0] << bbox_2[2] and bbox_2[1] <= p[1] <= bbox_2[3]:
            return True

    return False


def layer_list(request, layer_purpose, layer_category=None, bbox=None):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    if not layer_purpose:
        return HttpResponseBadRequest()

    try:
        layers_object = retrieve_layers(layer_purpose, layer_category, bbox)
        layers = []
        for l in layers_object:
            layer_obj = dict()
            layer_obj['id'] = l.id
            layer_obj['name'] = l.name
            layers.append(layer_obj)

        return HttpResponse(
            json.dumps(layers), content_type="application/json")

    except Exception as e:
        LOGGER.exception(e)
        return HttpResponseServerError()


def layer_panel(request, bbox=None):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    try:

        purposes = [
            {
                'name': 'exposure',
                'categories': ['population', 'road', 'structure'],
            },
            {
                'name': 'hazard',
                'categories': ['flood', 'earthquake', 'volcano'],
            }
        ]
        sections = [];
        for p in purposes:
            categories = []
            for c in p.get('categories'):
                layers = retrieve_layers(p.get('name'), c, bbox)
                category = {
                    'name': c,
                    'layers': layers
                }
                categories.append(category)
            section = {
                'name': p.get('name'),
                'categories': categories
            }
            sections.append(section)

        impact_layers = retrieve_layers('impact', bbox=bbox)
        sections.append({
            'name': 'impact',
            'categories': [
                {
                    'name': 'impact',
                    'layers': impact_layers
                }
            ]
        })
        form = AnalysisCreationForm(
            user=request.user,
            exposure_layer=retrieve_layers('exposure', bbox=bbox),
            hazard_layer=retrieve_layers('hazard', bbox=bbox))
        context = {
            'sections': sections,
            'form': form,
            'user': request.user,
        }
        return render(request, "geosafe/analysis/options_panel.html", context)

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
        return HttpResponse(json.dumps({
            'success': True,
            'is_saved': analysis.keep,
        }), content_type='application/json')
        # return HttpResponseRedirect(reverse('geosafe:analysis-list'))
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
        elif data_type == 'both':
            tmp = tempfile.mktemp()
            with ZipFile(tmp, mode='w') as zf:
                zf.writestr(
                    '%s_map.pdf' % layer_title,
                    analysis.report_map.read())
                zf.writestr(
                    '%s_table.pdf' % layer_title,
                    analysis.report_table.read())

            return serve_files(
                open(tmp),
                'application/zip',
                '%s_report.zip' % layer_title)
        return HttpResponseServerError()
    except Exception as e:
        LOGGER.debug(e)
        return HttpResponseServerError()


def analysis_summary(request, impact_id):
    """Get analysis summary from a given impact id"""

    if request.method != 'GET':
        return HttpResponseBadRequest()

    try:
        analysis = Analysis.objects.get(impact_layer__id=impact_id)
        context = {
            'analysis': analysis
        }
        return render(request, "geosafe/analysis/modal/impact_card.html",
                      context)
    except Exception as e:
        return HttpResponseServerError()
