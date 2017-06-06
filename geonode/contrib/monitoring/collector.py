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

from decimal import Decimal

from django import db

from geonode.utils import raw_sql
from geonode.contrib.monitoring.models import (Host, ServiceType, Service,
    Metric, MetricValue, ServiceTypeMetric, RequestEvent, ExceptionEvent,
    RequestEvent, MonitoredResource)


class CollectorAPI(object):

    def __init__(self):
        pass


    def collect_from_endpoints(self):
        pass


    def collect_from_geonode(self):
        pass

    def collect_from_system(self):
        pass

    def extract_resources(self, requests):
        resources = MonitoredResource.objects.filter(requests__in=requests).distinct()
        out = []
        for res in resources:
            out.append((res, requests.filter(resources=res).distinct(),))
        return out

    def set_metric_values(self, metric_name, column_name, service, valid_from, valid_to, resource=None):
        if resource:
            _sql = 'select re.{} as res, count(1) as cnt from monitoring_requestevent re join monitoring_requestevent_resources mr on (mr.requestevent_id = re.id) where re.service_id = %s and re.created > %s and re.created < %s and mr.monitoredresource_id = %s group by re.{} order by cnt desc limit 100'
            args = (service.id, valid_from, valid_to, resource.id,)
        else:
            _sql = 'select re.{} as res, count(1) as cnt from monitoring_requestevent re where re.service_id = %s and re.created > %s and re.created < %s group by re.{} order by cnt desc limit 100'
            args = (service.id, valid_from, valid_to,)
            
        sql = _sql.format(column_name, column_name)
        rows = raw_sql(sql, args)
        metric_values = {'name': metric_name,
                         'valid_from': valid_from,
                         'valid_to': valid_to, 
                         'service': service,
                         'resource': resource}
        for row in rows:
            val = row['res']
            cnt = row['cnt']
            metric_values.update({'value': val,
                                  'value_raw': val,
                                  'value_num': val if isinstance(val, (int,float,long,Decimal,)) else None,})
            MetricValue.add(**metric_value)

        

    def process_requests(self, service, requests, valid_from, valid_to):
        
        geonode_metrics = ('request', 'request.count', 'request.ip', 'request.ua', 'request.ua.family', 'request.method',
                       'request.country', 'request.region', 'request.city',
                       'response', 'response.time', 'response.ok', 'response.error',
                       'response.size', 'response.status.2xx', 'response.status.3xx', 'response.status.4xx', 'response.status.5xx',)


        metric_defaults = {'valid_from': valid_from,
                           'valid_to': valid_to,
                           'service': service}
        MetricValue.objects.filter(valid_from=valid_from, valid_to=valid_to, service=service).delete()
        resources = self.extract_resources(requests)

        self.set_metric_values('request.ip', 'client_ip', **metric_defaults)
        self.set_metric_values('request.country', 'client_country',  **metric_defaults)
        self.set_metric_values('request.city', 'client_city', **metric_defaults)
        self.set_metric_values('request.region', 'client_region', **metric_defaults)
        self.set_metric_values('request.ua', 'user_agent', **metric_defaults)
        self.set_metric_values('request.ua.family', 'user_agent_family', **metric_defaults)

        for resource, _requests in [(None, requests,)] + resources:
            count = _requests.count()

            metric_defaults['resource'] = resource
            #def add(cls, metric, valid_from, valid_to, service, label, value_raw, resource=None, value=None, value_num=None, data=None):
            MetricValue.add('request.count', valid_from, valid_to, service, 'Count', value=count, value_num=count, 
                            value_raw=count, resource=resource)
            self.set_metric_values('request.ip', 'client_ip', **metric_defaults)
            self.set_metric_values('request.country', 'client_country', **metric_defaults)
            self.set_metric_values('request.city', 'client_city', **metric_defaults)
            self.set_metric_values('request.region', 'client_region',  **metric_defaults)
            self.set_metric_values('request.ua', 'user_agent', **metric_defaults)
            self.set_metric_values('request.ua.family', 'user_agent_family', **metric_defaults)
