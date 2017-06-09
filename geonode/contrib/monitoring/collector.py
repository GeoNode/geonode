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

from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain

from geonode.utils import raw_sql
from geonode.contrib.monitoring.models import (Metric, MetricValue, ServiceTypeMetric,
                                               MonitoredResource, MetricLabel)

from geonode.contrib.monitoring.utils import generate_periods


class CollectorAPI(object):

    def __init__(self):
        pass

    def collect_from_endpoints(self):
        pass

    def collect_from_geonode(self):
        pass

    def collect_from_system(self):
        pass

    def get_labels_for_metric(self, metric_name, resource=None):
        mt = ServiceTypeMetric.objects.filter(metric__name=metric_name)
        if not mt:
            raise ValueError("No metric for {}".format(metric_name))
        
        qparams = {'metricvalue__service_metric__in': mt}
        if resource:
            qparams['metricvalue__resource'] = resource
        return list(MetricLabel.objects.filter(**qparams).distinct().values_list('name'))

    def get_resources_for_metric(self, metric_name):
        mt = ServiceTypeMetric.objects.filter(metric__name=metric_name)
        if not mt:
            raise ValueError("No metric for {}".format(metric_name))
        return list(MonitoredResource.objects.filter(metric_values__service_metric__in=mt)
                                             .exclude(name='', type='')
                                             .distinct()
                                             .order_by('type', 'name')
                                             .values_list('type', 'name'))

    def get_metric_names(self):
        """
        Returns list of tuples: (service type, list of metrics)
        """
        q = ServiceTypeMetric.objects.all().select_related().order_by('service_type', 'metric')
        out = []
        current_service = None
        current_set = []
        for item in q:
            service, metric = item.service_type, item.metric
            if current_service != service:
                if current_service is not None:
                    out.append((current_service, current_set,))
                    current_set = []
                current_service = service
            current_set.append(metric)
        if current_set:
            out.append((current_service, current_set,))

        return out

    def extract_resources(self, requests):
        resources = MonitoredResource.objects.filter(requests__in=requests).distinct()
        out = []
        for res in resources:
            out.append((res, requests.filter(resources=res).distinct(),))
        return out

    def set_metric_values(self, metric_name, column_name, service, valid_from, valid_to, resource=None, distinct=False):
        if distinct:
            sel = 'select distinct {}'.format(column_name)
        else:
            sel = 'select {}'.format(column_name)
        if resource:
            _sql = '{} as res, count(1) as cnt from monitoring_requestevent re join monitoring_requestevent_resources mr on (mr.requestevent_id = re.id) where re.service_id = %s and re.created > %s and re.created < %s and mr.monitoredresource_id = %s group by {} order by cnt desc limit 100'
            args = (service.id, valid_from, valid_to, resource.id,)
        else:
            _sql = '{} as res, count(1) as cnt from monitoring_requestevent re where re.service_id = %s and re.created > %s and re.created < %s group by {} order by cnt desc limit 100'
            args = (service.id, valid_from, valid_to,)
            
        sql = _sql.format(sel, column_name)
        rows = raw_sql(sql, args)
        metric_values = {'metric': metric_name,
                         'valid_from': valid_from,
                         'valid_to': valid_to,
                         'service': service,
                         'resource': resource}
        for row in rows:
            label = row['res']
            cnt = row['cnt']

            metric_values.update({'value': cnt,
                                  'label': label,
                                  'value_raw': cnt,
                                  'value_num': cnt if isinstance(cnt, (int,float,long,Decimal,)) else None,})

            MetricValue.add(**metric_values)

        
    def process_requests(self, service, requests, valid_from, valid_to):
        """
        Processes request list for specific service, generate stats
        """
        interval = service.check_interval
        periods = generate_periods(valid_from, interval, valid_to)
        for pstart, pend in periods:
            requests_batch = requests.filter(created__gte=pstart, created__lt=pend)
            self.process_requests_batch(service, requests_batch, pstart, pend)
         
    def process_requests_batch(self, service, requests, valid_from, valid_to):
        
        metric_defaults = {'valid_from': valid_from,
                           'valid_to': valid_to,
                           'service': service}
        MetricValue.objects.filter(valid_from__gte=valid_from, valid_to__lte=valid_to, service=service).delete()
        resources = self.extract_resources(requests)
        count = requests.count()
        MetricValue.add('request.count', valid_from, valid_to, service, 'Count', value=count, value_num=count, 
                            value_raw=count, resource=None)
        # calculate overall stats
        self.set_metric_values('request.ip', 're.client_ip', **metric_defaults)
        self.set_metric_values('request.country', 're.client_country',  **metric_defaults)
        self.set_metric_values('request.city', 're.client_city', **metric_defaults)
        self.set_metric_values('request.region', 're.client_region', **metric_defaults)
        self.set_metric_values('request.ua', 're.user_agent', **metric_defaults)
        self.set_metric_values('request.ua.family', 're.user_agent_family', **metric_defaults)

        # for each resource we should calculate another set of stats
        for resource, _requests in [(None, requests,)] + resources:
            count = _requests.count()

            metric_defaults['resource'] = resource
            #def add(cls, metric, valid_from, valid_to, service, label, value_raw, resource=None, value=None, value_num=None, data=None):
            MetricValue.add('request.count', valid_from, valid_to, service, 'Count', value=count, value_num=count, 
                            value_raw=count, resource=resource)
            self.set_metric_values('request.ip', 're.client_ip', **metric_defaults)
            self.set_metric_values('request.country', 're.client_country', **metric_defaults)
            self.set_metric_values('request.city', 're.client_city', **metric_defaults)
            self.set_metric_values('request.region', 're.client_region',  **metric_defaults)
            self.set_metric_values('request.ua', 're.user_agent', **metric_defaults)
            self.set_metric_values('request.ua.family', 're.user_agent_family', **metric_defaults)


    def get_metrics_for(self, metric_name, valid_from=None, valid_to=None, interval=None, service=None, label=None, resource=None):
        interval = interval or timedelta(minutes=1)
        now = datetime.now()
        valid_from = valid_from or (now - interval)
        valid_to = valid_to or now
        label = None #label or 'count'
        out = {'metric': metric_name,
               'input_valid_from': valid_from,
               'input_valid_to': valid_to,
               'interval': interval,
               'label': label,
               'data': []}
        periods = generate_periods(valid_from, interval, valid_to)
        for pstart, pend in periods:
            pdata = self.get_metrics_data(metric_name, pstart, pend, interval=interval, service=service, label=label, resource=resource)
            out['data'].append({'valid_from': pstart, 'valid_to': pend, 'data': pdata})
        return out


    def get_aggregate_function(self, column_name, metric_name, service=None):
        if service:
            metric = Metric.objects.get(name=metric_name, service_type___service_type_id=service.id)
        else:
            metric = Metric.objects.filter(name=metric_name).first()
        if not metric:
            raise ValueError("Invalid metric {}".format(metric_name))
        f = metric.get_aggregate_name()
        if not f:
            return column_name
        return '{}({})'.format(f, column_name)

    def get_metrics_data(self, metric_name, valid_from, valid_to, interval, service=None, label=None, resource=None):
       
        params = {}

        q_from = [  'from monitoring_metricvalue mv',
                    'join monitoring_servicetypemetric mt on (mv.service_metric_id = mt.id)'
                    'join monitoring_metric m on (m.id = mt.metric_id)' ]
        q_where = ['where', 'mv.valid_from >= %(valid_from)s and mv.valid_to <= %(valid_to)s '
                   'and m.name = %(metric_name)s',]
        q_group = []
        params.update({'metric_name': metric_name, 
                       'valid_from': valid_from, 
                       'valid_to': valid_to})
        
        col = 'mv.value_num'
        agg_f = self.get_aggregate_function(col, metric_name, service)
        has_agg = agg_f != col
        
        q_select = ['select {} as val'.format(agg_f)]
        if service:
            q_where.append('and mv.service_id = %(service_id)s')
            params['service_id'] = service.id
        if label:
            q_from.append('join monitoring_metriclabel ml on (mv.label_id = ml.id and ml.name = %(label)s)')
            params['label'] = label
        if resource:
            q_from.append('join monitoring_monitoredresource mr on (mv.resource_id = mr.id and mr.id = %(resource_id)s)')
            params['resource_id'] = resource.id
        if label and has_agg:
            q_group.extend(['ml.name'])
        if resource and has_agg:
            q_group.append('mr.name')
        if q_group:
            q_group = [ ' group by ', ','.join(q_group)]
                
        q = ' '.join(chain(q_select, q_from, q_where, q_group))
        #print('  ', q, params)
        #print()
        return list(raw_sql(q, params))
