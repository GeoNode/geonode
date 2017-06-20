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

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import chain

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from geonode.utils import raw_sql
from geonode.contrib.monitoring.models import (Metric, MetricValue, ServiceTypeMetric,
                                               MonitoredResource, MetricLabel, RequestEvent,
                                               ExceptionEvent)

from geonode.contrib.monitoring.utils import generate_periods, align_period_start, align_period_end
from geonode.utils import parse_datetime


log = logging.getLogger(__name__)


class CollectorAPI(object):

    def __init__(self):
        pass

    def _calculate_network_rate(self, metric_name, ifname, tx_value, valid_to):
        """
        Find previous network metric value and caclulate rate between them
        """
        prev = MetricValue.objects.filter(service_metric__metric__name=metric_name, label__name=ifname, valid_to__lt=valid_to).order_by('-valid_to').first()
        if not prev:
            return
        prev_val = prev.value_num
        interval = valid_to - prev.valid_to
        rate = float((tx_value - prev_val)) / interval.total_seconds()
        return rate

    def process_system_metrics(self, service, data, valid_from, valid_to):
        """
        Generates mertic values for system-level measurements
        """
        collected_at = parse_datetime(data['timestamp'])

        valid_from = align_period_start(collected_at, service.check_interval)
        valid_to = align_period_end(collected_at, service.check_interval)

        mdefaults = {'valid_from': valid_from,
                     'valid_to': valid_to,
                     'resource': None,
                     'service': service}

        MetricValue.objects.filter(service_metric__metric__name__in=('network.in', 'network.out'),
                                   valid_from=valid_from,
                                   valid_to=valid_to,
                                   service=service)\
                           .delete()

        for iface in data['data']['network']:
            ifname = iface['name']
            for tx_label, tx_value in iface['traffic'].iteritems():
                if tx_label not in ('in', 'out'):
                    continue
                mdata = {'value': tx_value,
                         'value_raw': tx_value,
                         'value_num': tx_value,
                         'label': ifname,
                         'metric': 'network.{}'.format(tx_label)}
                mdata.update(mdefaults)
                rate = self._calculate_network_rate(mdata['metric'], ifname, tx_value, valid_to)
                print MetricValue.add(**mdata)
                if rate:
                    mdata['metric'] = '{}.rate'.format(mdata['metric'])
                    mdata['value'] = rate
                    mdata['value_num'] = rate
                    mdata['value_raw'] = rate
                    print MetricValue.add(**mdata)


        ldata = data['data']['cpu']['load']
        llabel = ['1', '5', '15']

        memory_info = data['data']['memory']
        mkeys = [m.name[len('mem.'):] for m in service.get_metrics() if m.name.startswith('mem.')]
        for mkey in mkeys:
            mdata = memory_info[mkey]

            mdata = {'value': mdata,
                     'value_raw': mdata,
                     'value_num': mdata,
                     'metric': 'mem.{}'.format(mkey),
                     'label': 'MB',
                     }
            mdata.update(mdefaults)
            MetricValue.objects.filter(service_metric__metric__name=mdata['metric'],
                                       valid_from=mdata['valid_from'],
                                       valid_to=mdata['valid_to'],
                                       label__name='MB',
                                       service=service)\
                               .delete()
            print MetricValue.add(**mdata)

        MetricValue.objects.filter(service_metric__metric__name__in=('storage.total', 'storage.used', 'storage.free',),
                                   valid_from=valid_from,
                                   valid_to=valid_to,
                                   service=service)\
                           .delete()

        for df in data['data']['disks']['df']:
            dev, total, used, free, free_pct, mount = df
            for metric, val in (('storage.total', total,),
                                ('storage.used', used,),
                                ('storage.free', free,),):

                mdata = {'value': val,
                         'value_raw': val,
                         'value_num': val,
                         'metric': metric,
                         'label': mount,
                         }
                mdata.update(mdefaults)
                print MetricValue.add(**mdata)

        for lidx, l in enumerate(ldata):
            mdata = {'value': l,
                     'value_raw': l,
                     'value_num': l,
                     'metric': 'load.{}m'.format(llabel[lidx]),
                     'label': 'Value',
                     }

            mdata.update(mdefaults)
            MetricValue.objects.filter(service_metric__metric__name=mdata['metric'],
                                       valid_from=mdata['valid_from'],
                                       valid_to=mdata['valid_to'],
                                       label__name='Value',
                                       service=service)\
                               .delete()
            print MetricValue.add(**mdata)

    def get_labels_for_metric(self, metric_name, resource=None):
        mt = ServiceTypeMetric.objects.filter(metric__name=metric_name)
        if not mt:
            raise ValueError("No metric for {}".format(metric_name))

        qparams = {'metric_values__service_metric__in': mt}
        if resource:
            qparams['metricvalue__resource'] = resource
        return list(MetricLabel.objects.filter(**qparams).distinct().values_list('id', 'name'))

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

    def extract_ows_service(self, requests):
        q = requests.exclude(ows_service__isnull=True).distinct('ows_service').values_list('ows_service', flat=True)
        try:
            return q.get()
        except (ObjectDoesNotExist, MultipleObjectsReturned,):
            pass

    def extract_ows_services(self, requests):
        ows_services = requests.exclude(ows_service__isnull=True).distinct('ows_service').values_list('ows_service', flat=True)
        out = []
        for ows in ows_services:
            out.append((ows, requests.filter(ows_service=ows),))
        return out            

    def set_metric_values(self, metric_name, column_name, service, valid_from, valid_to, resource=None, ows_service=None):
        metric = Metric.get_for(metric_name, service=service)
        if metric.is_rate:
            sel = " 'value' as res, coalesce(avg({}), 0) as cnt".format(column_name)
            group_by = ''
        elif metric.is_count:
            sel = ' distinct {} as res, sum(count(1)) as cnt '.format(column_name)
            group_by = 'group by {}'.format(column_name)

        elif metric.is_value:
            sel = ' distinct {} as res, count(1) as cnt '.format(column_name)
            group_by = 'group by {}'.format(column_name)
        else:
            sel = ' {} as res, count(1) as cnt '.format(column_name)
            group_by = 'group by {}'.format(column_name)
        if resource:
            _sql = ('select {} from monitoring_requestevent re '
                    'join monitoring_requestevent_resources mr on (mr.requestevent_id = re.id)'
                    'where re.service_id = %s and re.created >= %s and re.created < %s '
                    'and mr.monitoredresource_id = %s {} order by cnt desc '
                    'limit 100')
            args = (service.id, valid_from, valid_to, resource.id,)
        else:
            _sql = ('select {} from monitoring_requestevent re '
                    'where re.service_id = %s and re.created > %s and re.created < %s '
                    '{} order by cnt desc limit 100')
            args = (service.id, valid_from, valid_to,)

        sql = _sql.format(sel, group_by)
        rows = raw_sql(sql, args)
        metric_values = {'metric': metric_name,
                         'valid_from': valid_from,
                         'valid_to': valid_to,
                         'service': service,
                         'ows_service': ows_service,
                         'resource': resource}
        for row in rows:
            label = row['res']
            cnt = row['cnt']
            metric_values.update({'value': cnt,
                                  'label': label,
                                  'value_raw': cnt,
                                  'value_num': cnt if isinstance(cnt, (int, float, long, Decimal,)) else None})

            print MetricValue.add(**metric_values)

    def process(self, service, data, valid_from, valid_to, *args, **kwargs):
        if service.is_system_monitor:
            return self.process_system_metrics(service, data, valid_from, valid_to, *args, **kwargs)
        else:
            return self.process_requests(service, data, valid_from, valid_to, *args, **kwargs)

    def process_requests(self, service, requests, valid_from, valid_to):
        """
        Processes request list for specific service, generate stats
        """
        interval = service.check_interval
        periods = generate_periods(valid_from, interval, valid_to)
        for pstart, pend in periods:
            requests_batch = requests.filter(created__gte=pstart, created__lt=pend)
            self.process_requests_batch(service, requests_batch, pstart, pend)


    def set_error_values(self, requests, valid_from, valid_to, service=None, resource=None, ows_service=None):
        with_errors = requests.filter(exceptions__isnull=False)
        if not with_errors.exists():
            return

        labels = ExceptionEvent.objects.filter(request__in=with_errors)\
                                       .distinct()\
                                       .values_list('error_type', flat=True)

        defaults = {'valid_from': valid_from,
                    'valid_to': valid_to,
                    'resource': resource,
                    'ows_service': ows_service,
                    'metric': 'response.errors',
                    'label': 'count',
                    'service': service}
        cnt = with_errors.count()
        print MetricValue.add(value=cnt, value_num=cnt, value_raw=cnt, **defaults)
        defaults['metric'] = 'response.errors.types'
        for label in labels:
            cnt = with_errors.filter(exceptions__error_type=label).count()
            defaults['label'] = label
            print MetricValue.add(value=cnt, value_num=cnt, value_raw=cnt, **defaults)

    def process_requests_batch(self, service, requests, valid_from, valid_to):
        """
        Processes requests information into metric values
        """
        log.info("Processing batch of %s requests from %s to %s", requests.count(), valid_from, valid_to)
        if not requests.count():
            return 
        metric_defaults = {'valid_from': valid_from,
                           'valid_to': valid_to,
                           'service': service}
        MetricValue.objects.filter(valid_from__gte=valid_from, valid_to__lte=valid_to, service=service).delete()

        resources = self.extract_resources(requests)
        ows_services = self.extract_ows_services(requests)
        count = requests.count()
        print MetricValue.add('request.count', valid_from, valid_to, service, 'Count',
                        value=count,
                        value_num=count,
                        value_raw=count,
                        resource=None)
        # calculate overall stats
        self.set_metric_values('request.ip', 're.client_ip', **metric_defaults)
        self.set_metric_values('request.country', 're.client_country',  **metric_defaults)
        self.set_metric_values('request.city', 're.client_city', **metric_defaults)
        self.set_metric_values('request.region', 're.client_region', **metric_defaults)
        self.set_metric_values('request.ua', 're.user_agent', **metric_defaults)
        self.set_metric_values('request.ua.family', 're.user_agent_family', **metric_defaults)
        self.set_metric_values('response.time', 're.response_time', **metric_defaults)
        self.set_metric_values('response.size', 're.response_size', **metric_defaults)
        self.set_metric_values('response.status', 're.response_status', **metric_defaults)
        self.set_metric_values('request.method', 're.request_method', **metric_defaults)
        self.set_error_values(requests, valid_from, valid_to, service=service, resource=None) 

        # for each resource we should calculate another set of stats
        for resource, _requests in [(None, requests,)] + resources:
            count = _requests.count()
            ows_service = self.extract_ows_service(_requests)
            metric_defaults['resource'] = resource
            metric_defaults['ows_service'] = ows_service
            MetricValue.add('request.count', valid_from, valid_to, service, 'Count', value=count, value_num=count,
                            value_raw=count, resource=resource)
            self.set_metric_values('request.ip', 're.client_ip', **metric_defaults)
            self.set_metric_values('request.country', 're.client_country', **metric_defaults)
            self.set_metric_values('request.city', 're.client_city', **metric_defaults)
            self.set_metric_values('request.region', 're.client_region',  **metric_defaults)
            self.set_metric_values('request.ua', 're.user_agent', **metric_defaults)
            self.set_metric_values('request.ua.family', 're.user_agent_family', **metric_defaults)
            self.set_metric_values('response.time', 're.response_time', **metric_defaults)
            self.set_metric_values('response.size', 're.response_size', **metric_defaults)
            self.set_metric_values('response.status', 're.response_status', **metric_defaults)
            self.set_metric_values('request.method', 're.request_method', **metric_defaults)
            self.set_error_values(_requests, valid_from, valid_to, service=service, resource=resource) 

        metric_defaults.pop('resource', None)
        for ows, _requests in [(None, requests,)] + ows_services:
            count = _requests.count()

            metric_defaults['ows_service'] = ows
            MetricValue.add('request.count', valid_from, valid_to, service, 'Count', value=count, value_num=count,
                            value_raw=count, ows_service=ows)
            self.set_metric_values('request.ip', 're.client_ip', **metric_defaults)
            self.set_metric_values('request.country', 're.client_country', **metric_defaults)
            self.set_metric_values('request.city', 're.client_city', **metric_defaults)
            self.set_metric_values('request.region', 're.client_region',  **metric_defaults)
            self.set_metric_values('request.ua', 're.user_agent', **metric_defaults)
            self.set_metric_values('request.ua.family', 're.user_agent_family', **metric_defaults)
            self.set_metric_values('response.time', 're.response_time', **metric_defaults)
            self.set_metric_values('response.size', 're.response_size', **metric_defaults)
            self.set_metric_values('response.status', 're.response_status', **metric_defaults)
            self.set_metric_values('request.method', 're.request_method', **metric_defaults)
            self.set_error_values(_requests, valid_from, valid_to, service=service, ows_service=ows)

    def get_metrics_for(self, metric_name, valid_from=None, valid_to=None, interval=None, service=None,
                        label=None, resource=None, ows_service=None):
        """
        Returns metric data for given metric. Returned dataset contains list of periods and values in that periods
        """
        now = datetime.now()
        valid_from = valid_from or (now - interval)
        valid_to = valid_to or now
        if not interval and (valid_to - valid_from).total_seconds() > 24*3600:
            interval = timedelta(seconds=3600)
        interval = interval or timedelta(minutes=1)
        if not isinstance(interval, timedelta):
            interval = timedelta(seconds=interval)

        out = {'metric': metric_name,
               'input_valid_from': valid_from,
               'input_valid_to': valid_to,
               'interval': interval.total_seconds(),
               'label': label.name if label else None,
               'data': []}
        periods = generate_periods(valid_from, interval, valid_to)
        for pstart, pend in periods:
            pdata = self.get_metrics_data(metric_name, pstart, pend,
                                          interval=interval,
                                          service=service,
                                          label=label,
                                          ows_service=ows_service,
                                          resource=resource)
            out['data'].append({'valid_from': pstart, 'valid_to': pend, 'data': pdata})
        return out

    def get_aggregate_function(self, column_name, metric_name, service=None):
        """
        Returns string with metric value column name surrounded by aggregate function
        based on metric type (which tells how to interpret value - is it a counter,
        rate or something else).
        """
        metric = Metric.get_for(metric_name, service=service)
        if not metric:
            raise ValueError("Invalid metric {}".format(metric_name))
        f = metric.get_aggregate_name()
        if not f:
            return column_name
        return '{}({})'.format(f, column_name)

    def get_metrics_data(self, metric_name, valid_from, valid_to, interval, service=None, label=None, resource=None, ows_service=None):
        """
        Returns metric values for metric within given time span
        """
        params = {}

        q_from = ['from monitoring_metricvalue mv',
                  'join monitoring_servicetypemetric mt on (mv.service_metric_id = mt.id)',
                  'join monitoring_metric m on (m.id = mt.metric_id)',
                  'join monitoring_metriclabel ml on (mv.label_id = ml.id) ']
        q_where = ['where', 'mv.valid_from >= %(valid_from)s and mv.valid_to <= %(valid_to)s ',
                   'and m.name = %(metric_name)s']
        q_group = ['ml.name']
        params.update({'metric_name': metric_name,
                       'valid_from': valid_from,
                       'valid_to': valid_to})

        col = 'mv.value_num'
        agg_f = self.get_aggregate_function(col, metric_name, service)
        has_agg = agg_f != col

        q_select = ['select ml.name as label, {} as val, count(1), min(mv.value_num), max(mv.value_num)'.format(agg_f)]
        if service:
            q_where.append('and mv.service_id = %(service_id)s')
            params['service_id'] = service.id
        if ows_service:
            q_where.append(' and mv.ows_service_id = %(ows_service)s ')
            params['ows_service'] = ows_service.id
        if label:
            q_where.append(' and ml.id = %(label)s')
            params['label'] = label.id
        if resource:
            q_from.append('join monitoring_monitoredresource mr on '
                          '(mv.resource_id = mr.id and mr.id = %(resource_id)s)')
            params['resource_id'] = resource.id
        if label and has_agg:
            q_group.extend(['ml.name'])
        if resource and has_agg:
            q_group.append('mr.name')
        if q_group:
            q_group = [' group by ', ','.join(q_group)]

        q = ' '.join(chain(q_select, q_from, q_where, q_group))
        return list(raw_sql(q, params))

    def clear_old_data(self):
        threshold = settings.MONITORING_DATA_TTL
        if not isinstance(threshold, timedelta):
            raise TypeError("MONITORING_DATA_TTL should be an instance of "
                            "datatime.timedelta, not {}".format(threshold.__class__))
        cutoff = datetime.now() - threshold
        ExceptionEvent.objects.filter(created__lte=cutoff).delete()
        RequestEvent.objects.filter(created__lte=cutoff).delete()
        MetricValue.objects.filter(valid_to__lte=cutoff).delete()
