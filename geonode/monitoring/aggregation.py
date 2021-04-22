# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from datetime import datetime, timedelta, time
from decimal import Decimal
import logging

import pytz

from django.conf import settings
from django.db.models import Sum, F
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from geonode.monitoring.utils import generate_periods
from geonode.monitoring.models import (Metric, MetricValue, ServiceTypeMetric,
                                       MonitoredResource, MetricLabel, EventType,)


log = logging.getLogger(__name__)


def get_metric_names():
    """
    Returns list of tuples: (service type, list of metrics)
    """
    q = ServiceTypeMetric.objects.all().select_related(
    ).order_by('service_type', 'metric')

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


def get_labels_for_metric(metric_name, resource=None):
    mt = ServiceTypeMetric.objects.filter(metric__name=metric_name)
    if not mt:
        raise ValueError(f"No metric for {metric_name}")

    qparams = {'metric_values__service_metric__in': mt}
    if resource:
        qparams['metricvalue__resource'] = resource
    return list(MetricLabel.objects.filter(
        **qparams).distinct().values_list('id', 'name'))


def get_resources_for_metric(metric_name):
    mt = ServiceTypeMetric.objects.filter(metric__name=metric_name)
    if not mt:
        raise ValueError(f"No metric for {metric_name}")
    return list(MonitoredResource.objects.filter(metric_values__service_metric__in=mt)
                                         .exclude(name='', type='')
                                         .distinct()
                                         .order_by('type', 'name')
                                         .values_list('type', 'name'))


def extract_resources(requests):
    resources = MonitoredResource.objects.filter(
        requests__in=requests).distinct()
    out = []
    for res in resources:
        out.append((res, requests.filter(resources=res).distinct(),))
    return out


def extract_event_type(requests):
    q = requests.exclude(event_type__isnull=True).distinct(
        'event_type').values_list('event_type', flat=True)
    try:
        return q.get()
    except (ObjectDoesNotExist, MultipleObjectsReturned,):
        pass


def extract_event_types(requests):
    event_types = requests.exclude(event_type__isnull=True)\
        .distinct('event_type')\
        .values_list('event_type', flat=True)
    return [EventType.objects.get(id=evt_id) for evt_id in event_types]


def extract_special_event_types(requests):
    """
    Return list of pairs (event_type, requests)
    that should be registered as one of aggregating event types: ows:all, other,
    """
    out = []

    ows_et = requests.exclude(event_type__isnull=True)\
                     .filter(event_type__name__startswith='OWS:')\
                     .exclude(event_type__name=EventType.EVENT_OWS)\
                     .distinct('event_type')\
                     .values_list('event_type', flat=True)
    ows_rq = requests.filter(event_type__in=ows_et)
    ows_all = EventType.get(EventType.EVENT_OWS)
    out.append((ows_all, ows_rq,))

    nonows_et = requests.exclude(event_type__isnull=True)\
                        .exclude(event_type__name__startswith='OWS:')\
                        .exclude(event_type__name=EventType.EVENT_OTHER)\
                        .distinct('event_type')\
                        .values_list('event_type', flat=True)
    nonows_rq = requests.filter(event_type__in=nonows_et)
    nonows_all = EventType.get(EventType.EVENT_OTHER)
    out.append((nonows_all, nonows_rq,))

    return out


def calculate_rate(metric_name, metric_label,
                   current_value, valid_to):
    """
    Find previous network metric value and caclulate rate between them
    """
    prev = MetricValue.objects.filter(service_metric__metric__name=metric_name,
                                      label__name=metric_label,
                                      valid_to__lt=valid_to)\
        .order_by('-valid_to').first()
    if not prev:
        return
    prev_val = prev.value_num
    valid_to = valid_to.replace(tzinfo=pytz.utc)
    prev.valid_to = prev.valid_to.replace(tzinfo=pytz.utc)
    interval = valid_to - prev.valid_to
    if not isinstance(current_value, Decimal):
        current_value = Decimal(current_value)

    # this means counter was reset, don't want rates below 0
    if current_value < prev_val:
        return
    rate = float((current_value - prev_val)) / interval.total_seconds()
    return rate


def calculate_percent(
        metric_name, metric_label, current_value, valid_to):
    """
    Find previous network metric value and caclulate percent
    """
    rate = calculate_rate(
        metric_name, metric_label, current_value, valid_to)
    if rate is None:
        return
    return rate * 100


def adjust_now_to_noon(now):
    return pytz.utc.localize(datetime.combine(now.date(), time(0, 0, 0)))


def aggregate_past_periods(metric_data_q=None, periods=None, cleanup=True, now=None, max_since=None):
    """
    Aggregate past metric data into longer periods
    @param metric_data_q Query for metric data to use as input
                         (default: all MetricValues)
    @param periods list of tuples (cutoff, aggregation) to be used
                   (default: settings.MONITORING_DATA_AGGREGATION)
    @param cleanup flag if input data should be removed after aggregation
                   (default: True)
    @param now arbitrary now moment to start calculation of cutoff
               (default: current now)
    @param max_since look for data no older than max_since
                     (default: 1 year)
    """
    utc = pytz.utc
    if now is None:
        now = datetime.utcnow().replace(tzinfo=utc)
    if metric_data_q is None:
        metric_data_q = MetricValue.objects.all()
    if periods is None:
        periods = settings.MONITORING_DATA_AGGREGATION
    max_since = max_since or now - timedelta(days=356)
    previous_cutoff = None
    counter = 0
    now = adjust_now_to_noon(now)
    # start from the end, oldest one first
    for cutoff_base, aggregation_period in reversed(periods):
        since = previous_cutoff or max_since
        until = now - cutoff_base

        if since > until:
            log.debug("Wrong period boundaries, end %s is before start %s, agg: %s",
                      until, since, aggregation_period)
            previous_cutoff = max(until, since)
            continue

        log.debug("aggregation params: cutoff: %s agg period: %s"
                  "\n  since: '%s' until '%s', but previous cutoff:"
                  " '%s', aggregate to '%s'",
                  cutoff_base, aggregation_period, since, until, previous_cutoff, aggregation_period)

        periods = generate_periods(since, aggregation_period, end=until)

        # for each target period we select mertic values within it
        # and extract service, resource, event type and label combinations
        # then, for each distinctive set, calculate per-metric aggregate values
        for period_start, period_end in periods:
            log.debug('period %s - %s (%s s)', period_start, period_end, period_end - period_start)
            ret = aggregate_period(period_start, period_end, metric_data_q, cleanup)
            counter += ret
        previous_cutoff = until
    return counter


def aggregate_period(period_start, period_end, metric_data_q, cleanup=True):
    counter = 0
    to_remove_data = {'remove_at': period_start.strftime("%Y%m%d%H%M%S")}
    source_metric_data = metric_data_q.filter(valid_from__gte=period_start,
                                              valid_to__lte=period_end)\
        .exclude(valid_from=period_start,
                 valid_to=period_end,
                 data={})
    r = source_metric_data.values_list('service_id', 'service_metric_id', 'resource_id', 'event_type_id', 'label_id',)\
                          .distinct('service_id', 'service_metric_id', 'resource_id', 'event_type_id', 'label_id')
    source_metric_data.update(data=to_remove_data)

    for service_id, metric_id, resource_id, event_type_id, label_id in r:
        m = Metric.objects.filter(service_type__id=metric_id).get()
        f = m.get_aggregate_field()
        per_metric_q = source_metric_data.filter(service_metric_id=metric_id,
                                                 service_id=service_id,
                                                 resource_id=resource_id,
                                                 event_type_id=event_type_id,
                                                 label_id=label_id)

        try:
            value_q = per_metric_q.aggregate(fvalue=f,
                                             fsamples_count=Sum(F('samples_count')))
        except TypeError as err:
            raise ValueError(f, m, err)
        value = value_q['fvalue']
        samples_count = value_q['fsamples_count']
        if cleanup:
            per_metric_q.delete()
        log.debug('Metric %s: %s - %s (value: %s, samples: %s)',
                  m, period_start, period_end, value, samples_count)
        if not metric_data_q.filter(service_metric_id=metric_id,
                                    service_id=service_id,
                                    resource_id=resource_id,
                                    event_type_id=event_type_id,
                                    valid_from=period_start,
                                    valid_to=period_end,
                                    label_id=label_id).exists():
            MetricValue.objects.create(service_metric_id=metric_id,
                                       service_id=service_id,
                                       resource_id=resource_id,
                                       event_type_id=event_type_id,
                                       value=value,
                                       value_num=value,
                                       value_raw=value,
                                       valid_from=period_start,
                                       valid_to=period_end,
                                       label_id=label_id,
                                       samples_count=samples_count)
        else:
            metric_data_q.filter(service_metric_id=metric_id,
                                 service_id=service_id,
                                 resource_id=resource_id,
                                 event_type_id=event_type_id,
                                 valid_from=period_start,
                                 valid_to=period_end,
                                 label_id=label_id)\
                .update(value=value,
                        value_num=value,
                        value_raw=value,
                        data=None,
                        samples_count=samples_count)
        counter += 1

    if cleanup:
        source_metric_data.filter(data=to_remove_data).delete()
    return counter
