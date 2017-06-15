# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from datetime import datetime

from django.shortcuts import render

from django import forms
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse

from geonode.utils import json_response
from geonode.contrib.monitoring.collector import CollectorAPI
from geonode.contrib.monitoring.models import Service, Host, Metric, ServiceTypeMetric, MetricLabel, MonitoredResource
from geonode.contrib.monitoring.utils import TypeChecks
from geonode.contrib.monitoring.service_handlers import exposes

# Create your views here.

capi = CollectorAPI()

class MetricsList(View):
    
    def get(self, *args, **kwargs):
        _metrics = capi.get_metric_names()
        out = [] 
        for srv, mlist in _metrics:
            out.append({'service': srv.name,
                        'metrics': [{'name': m.name, 'type': m.type} for m in mlist]})
        return json_response({'metrics': out})

class ServicesList(View):
    
    def get_queryset(self):
        return Service.objects.all().select_related()

    def get(self, *args, **kwargs):
        q = self.get_queryset()
        out = []
        for item in q:
            out.append({'name': item.name, 
                        'host': item.host.name, 
                        'check_interval': item.check_interval.total_seconds(),
                        'last_check': item.last_check})

        return json_response({'services': out})

class HostsList(View):
    
    def get_queryset(self):
        return Host.objects.all().select_related()

    def get(self, *args, **kwargs):
        q = self.get_queryset()
        out = []
        for item in q:
            out.append({'name': item.name, 'ip': item.ip})

        return json_response({'hosts': out})



class CheckTypeForm(forms.Form):
    def _check_type(self, tname):
        d = self.cleaned_data
        if not d:
            return
        val = d[tname]
        if not val:
            return
        tcheck = getattr(TypeChecks, '{}_type'.format(tname), None)
        if not tcheck:
            raise forms.ValidationError("No type check for {}".format(tname))
        try:
            return tcheck(val)
        except (Exception,), err:
            raise forms.ValidationError(err)


class MetricsFilters(CheckTypeForm):
    valid_from = forms.DateTimeField(required=False)
    valid_to = forms.DateTimeField(required=False)
    interval = forms.IntegerField(min_value=60, required=False)
    service = forms.CharField(required=False)
    label = forms.CharField(required=False)
    resource = forms.CharField(required=False)

    def clean_resource(self):
        return self._check_type('resource')

    def clean_service(self):
        return self._check_type('service')

    def clean_label(self):
        return self._check_type('label')


class LabelsFilterForm(CheckTypeForm):
    metric_name = forms.CharField(required=False)

    def clean_metric(self):
        return self._check_type('metric_name')


class ResourcesFilterForm(LabelsFilterForm):
    resource_type = forms.CharField(required=False)
    
    def clean_resource_type(self):
        return self._check_type('resource_type')



class FilteredView(View):
    # form which validates request.GET for get_queryset()
    filter_form = None

    # iterable of pairs (from model field, to key name) to map
    # fields from model to elements of output data
    fields_map = tuple()    
  
    # key name for output ({output_name: data})
    output_name = None

    def get_filter_args(self, request):
        if not self.filter_form:
            return {}
        f = self.filter_form(data=request.GET)
        if f.is_valid():
            return f.cleaned_data
        return {}

    def get(self, request, *args, **kwargs):
        qargs = self.get_filter_args(request)
        q = self.get_queryset(**qargs)
        from_fields = [f[0] for f in self.fields_map]
        to_fields = [f[1] for f in self.fields_map]
        out = [dict(zip(to_fields, (getattr(item, f) for f in from_fields))) for item in q]
        return json_response({self.output_name: out})


class ResourcesList(FilteredView):

    filter_form = ResourcesFilterForm
    fields_map = (('id', 'id',),
                  ('type', 'type',),
                  ('name', 'name',),)

    output_name = 'resources'

    def get_queryset(self, metric_name=None, resource_type=None):
        q = MonitoredResource.objects.all().distinct()
        if resource_type:
            q = q.filter(type=resource_type)
        if metric_name:
            sm = ServiceTypeMetric.objects.filter(metric__name=metric_name)
            q = q.filter(metric_values__service_metric__in=sm)
        return q


class LabelsList(FilteredView):

    filter_form = LabelsFilterForm
    fields_map = (('id', 'id',),
                  ('name', 'name',),)
    output_names = 'labels'

    def get_queryset(self, metric_name):
        q = MetricLabel.objects.all().distinct()
        if metric_name:
            sm = ServiceTypeMetric.objects.filter(metric__name=metric_name)
            q = q.filter(metric_values__service_metric__in=sm)
        return q


class MetricDataView(View):

    def get_filters(self, **kwargs):
        out = {}
        f = MetricsFilters(data=self.request.GET)

        if f.is_valid():
            out.update(f.cleaned_data)
        else:
            print(f.errors)
        return out
        
    def get(self, *args, **kwargs):
        #def get_metrics_for(self, metric_name, valid_from=None, valid_to=None, interval=None, service=None, label=None, resource=None):
        filters = self.get_filters(**kwargs)
        metric_name = kwargs['metric_name']
        out = capi.get_metrics_for(metric_name, **filters)
        return json_response({'data': out})



class BeaconView(View):
    

    def get(self, request, *args, **kwargs):
        service = kwargs.get('exposed')
        if not service:
            data = [{'name': s, 'url': reverse('monitoring:api_beacon_exposed', args=(s,))} for s in exposes.keys()]
            return json_response({'exposed': data})
        try:
            ex = exposes[service]()
        except KeyError:
            return json_response(errors={'exposed': 'No service for {}'.format(service)}, status=404)
        out = {'data': ex.expose(),
               'timestamp': datetime.now()}
        return json_response(out)


api_metrics = MetricsList.as_view()
api_services = ServicesList.as_view()
api_hosts = HostsList.as_view()
api_labels = LabelsList.as_view()
api_resources = ResourcesList.as_view()
api_metric_data = MetricDataView.as_view()
api_beacon = BeaconView.as_view()
