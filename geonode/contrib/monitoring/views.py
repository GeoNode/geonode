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

from django.shortcuts import render

from django import forms
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from geonode.utils import json_response
from geonode.contrib.monitoring.collector import CollectorAPI
from geonode.contrib.monitoring.models import Service, Host, Metric
from geonode.contrib.monitoring.utils import TypeChecks

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

class MetricsFilters(forms.Form):
    valid_from = forms.DateTimeField(required=False)
    valid_to = forms.DateTimeField(required=False)
    interval = forms.IntegerField(min_value=60, required=False)
    service = forms.CharField(required=False)
    label = forms.CharField(required=False)
    resource = forms.CharField(required=False)

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

    def clean_resource(self):
        return self._check_type('resource')

    def clean_service(self):
        return self._check_type('service')

    def clean_label(self):
        return self._check_type('label')


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


api_metrics = MetricsList.as_view()
api_services = ServicesList.as_view()
api_hosts = HostsList.as_view()
api_metric_data = MetricDataView.as_view()
