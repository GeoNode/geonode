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
import types

from socket import gethostbyname
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from jsonfield import JSONField

from django.utils.translation import ugettext_noop as _
from django.core.urlresolvers import reverse

try:
    from django.contrib.gis.geoip2 import GeoIP2 as GeoIP
except ImportError:
    from django.contrib.gis.geoip import GeoIP

import user_agents

from geonode.utils import parse_datetime


log = logging.getLogger(__name__)
# additional setup for geoip is needed
geoip = GeoIP()


class Host(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    ip = models.GenericIPAddressField(null=False, blank=False)
    active = models.BooleanField(null=False, blank=False, default=True)

    def __str__(self):
        return 'Host: {} ({})'.format(self.name, self.ip)


class ServiceType(models.Model):
    TYPE_GEONODE = 'geonode'
    TYPE_GEOSERVER = 'geoserver'
    TYPE_HOST_GN = 'hostgeonode'
    TYPE_HOST_GS = 'hostgeoserver'

    TYPES = ((TYPE_GEONODE, _("GeoNode"),),
             (TYPE_GEOSERVER, _("GeoServer"),),
             (TYPE_HOST_GS, _("Host (GeoServer)",),),
             (TYPE_HOST_GN, _("Host (GeoNode)",),),
             )
    name = models.CharField(max_length=255, unique=True, blank=False, null=False, choices=TYPES)

    def __str__(self):
        return 'Service Type: {}'.format(self.name)

    @property
    def is_system_monitor(self):
        return self.name in (self.TYPE_HOST_GN, self.TYPE_HOST_GS,)


class Service(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    host = models.ForeignKey(Host, null=False)
    check_interval = models.DurationField(null=False, blank=False, default=timedelta(seconds=60))
    last_check = models.DateTimeField(null=True, blank=True)
    service_type = models.ForeignKey(ServiceType, null=False)
    active = models.BooleanField(null=False, blank=False, default=True)
    notes = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True, default='')

    def __str__(self):
        return 'Service: {}@{}'.format(self.name, self.host.name)

    def get_metrics(self):
        return [m.metric for m in self.service_type.metric.all()]

    @property
    def is_system_monitor(self):
        return self.service_type.is_system_monitor


class MonitoredResource(models.Model):
    TYPE_EMPTY = ''
    TYPE_LAYER = 'layer'
    TYPE_MAP = 'map'
    TYPE_DOCUMENT = 'document'
    TYPE_STYLE = 'style'
    TYPE_ADMIN = 'admin'
    TYPE_OTHER = 'other'
    _TYPES = (TYPE_EMPTY, TYPE_LAYER, TYPE_MAP,
              TYPE_DOCUMENT, TYPE_STYLE, TYPE_ADMIN,
              TYPE_OTHER,)

    TYPES = ((TYPE_EMPTY, _("No resource"),),
             (TYPE_LAYER, _("Layer"),),
             (TYPE_MAP, _("Map"),),
             (TYPE_DOCUMENT, _("Document"),),
             (TYPE_STYLE, _("Style"),),
             (TYPE_ADMIN, _("Admin"),),
             (TYPE_OTHER, _("Other"),))

    name = models.CharField(max_length=255, null=False, blank=True, default='')
    type = models.CharField(max_length=255, null=False, blank=False, choices=TYPES, default=TYPE_EMPTY)

    class Meta:
        unique_together = (('name', 'type',),)

    def __str__(self):
        return 'Monitored Resource: {} {}'.format(self.name, self.type)


class Metric(models.Model):
    TYPE_RATE = 'rate'
    TYPE_COUNT = 'count'
    TYPE_VALUE = 'value'
    TYPES = ((TYPE_RATE, _("Rate"),),
             (TYPE_COUNT, _("Count"),),
             (TYPE_VALUE, _("Value"),),
             )

    AGGREGATE_MAP = {TYPE_RATE: 'avg',
                     TYPE_VALUE: 'max',
                     TYPE_COUNT: 'sum'}

    name = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=255, null=False, blank=False, default=TYPE_RATE, choices=TYPES)

    def get_aggregate_name(self):
        return self.AGGREGATE_MAP[self.type]

    def __str__(self):
        return "Metric: {}".format(self.name)

    @property
    def is_rate(self):
        return self.type == self.TYPE_RATE

    @property
    def is_count(self):
        return self.type == self.TYPE_COUNT

    @property
    def is_value(self):
        return self.type == self.TYPE_VALUE

    @classmethod
    def get_for(cls, name, service=None):
        if service:
            stype = ServiceTypeMetric.objects.get(service_type=service.service_type, metric__name=name)
            metric = stype.metric
        else:
            metric = Metric.objects.filter(name=name).first()
        return metric


class ServiceTypeMetric(models.Model):
    service_type = models.ForeignKey(ServiceType, related_name='metric')
    metric = models.ForeignKey(Metric, related_name='service_type')

    def __str__(self):
        return '{} - {}'.format(self.service_type, self.metric)


class OWSService(models.Model):
    _ows_types = 'tms wms-c wmts wcs wfs wms wps'.upper().split(' ')
    OWS_OTHER = 'other'
    OWS_TYPES = zip(_ows_types, _ows_types) + [(OWS_OTHER, _("Other"))]
    name = models.CharField(max_length=16, unique=True, 
                            choices=OWS_TYPES, 
                            null=False, 
                            blank=False)
    
    @classmethod
    def get(cls, service_name=None):
        if not service_name:
            return
        try:
            return cls.objects.get(name=service_name)
        except cls.DoesNotExist:
            return


class RequestEvent(models.Model):
    _methods = 'get post head options put delete'.upper().split(' ')
    METHODS = zip(_methods, _methods)
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service)
    ows_service = models.ForeignKey(OWSService, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, default='')
    request_path = models.CharField(max_length=255, blank=False, default='')

    # resources is a list of affected resources. it is buld as a pair of type and name:
    #  layer=geonode:sample_layer01
    # or
    #  document=documents/id
    # or
    #  map=some map
    #
    # list is separated with newline
    # resources = models.TextField(blank=True, default='', help_text=_("Resources name (style, layer, document, map)"))
    resources = models.ManyToManyField(MonitoredResource, null=True, blank=True,
                                       help_text=_("List of resources affected"),
                                       related_name='requests')

    request_method = models.CharField(max_length=16, choices=METHODS)
    response_status = models.PositiveIntegerField(null=False, blank=False)
    response_size = models.PositiveIntegerField(null=False, default=0)
    response_time = models.PositiveIntegerField(null=False, default=0, help_text=_("Response processing time in ms"))
    response_type = models.CharField(max_length=255, null=True, blank=True, default='')
    user_agent = models.CharField(max_length=255, null=True, blank=True, default=None)
    user_agent_family = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_ip = models.GenericIPAddressField(null=False)
    client_lat = models.DecimalField(max_digits=8, decimal_places=5, null=True, default=None, blank=True)
    client_lon = models.DecimalField(max_digits=8, decimal_places=5, null=True, default=None, blank=True)
    client_country = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_region = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_city = models.CharField(max_length=255, null=True, default=None, blank=True)

    custom_id = models.CharField(max_length=255, null=True, default=None, blank=True, db_index=True)

    @classmethod
    def _get_resources(cls, type_name, resources_list):
        out = []
        for r in resources_list:
            rinst, _ = MonitoredResource.objects.get_or_create(name=r, type=type_name)
            out.append(rinst)
        return out

    @classmethod
    def _get_geonode_resources(cls, request):
        """
        Return serialized resources affected by request
        """
        rqmeta = getattr(request, '_monitoring', {})
        resources = []
        for type_name in 'layer map document style'.split():
            res = rqmeta['resources'].get(type_name) or []
            resources.extend(cls._get_resources(type_name, res))
        return resources

    @staticmethod
    def _get_ua_family(ua):
        return str(user_agents.parse(ua))

    @classmethod
    def from_geonode(cls, service,  request, response):
        received = datetime.now()
        rqmeta = getattr(request, '_monitoring', {})
        created = rqmeta.get('started', received)
        if not isinstance(created, datetime):
            created = parse_datetime(created)
        _ended = rqmeta.get('finished', datetime.now())
        duration = (_ended - created).microseconds

        ua = request.META['HTTP_USER_AGENT']
        ua_family = cls._get_ua_family(ua)

        ip = request.get_host()
        lat = lon = None
        country = region = city = None
        if ip:
            ip = ip.split(':')[0]
            if settings.TEST and ip == 'testserver':
                ip = '127.0.0.1'
            ip = gethostbyname(ip)
            client_loc = geoip.city(ip)

            if client_loc:
                lat, lon = client_loc['latitude'], client_loc['longitude'],
                country = client_loc['country_code']
                region = client_loc['region']
                city = client_loc['city']
        data = {'received': received,
                'created': created,
                'host': request.get_host(),
                'service': service,
                'ows_service': None,
                'request_path': request.get_full_path(),
                'request_method': request.method,
                'response_status': response.status_code,
                'response_size': response.get('Content-length') or len(response.getvalue()),
                'response_type': response.get('Content-type'),
                'response_time': duration,
                'user_agent': ua,
                'user_agent_family': ua_family,
                'client_ip': ip,
                'client_lat': lat,
                'client_lon': lon,
                'client_country': country,
                'client_region': region,
                'client_city': city}
        inst = cls.objects.create(**data)
        resources = cls._get_geonode_resources(request)
        if resources:
            inst.resources.add(*resources)
            inst.save()
        return inst

    @classmethod
    def from_geoserver(cls, service, request_data, received=None):
        """
        Writes RequestEvent for data from audit log in GS
        """
        rd = request_data.get('org.geoserver.monitor.RequestData')
        if not rd:
            log.warning("No request data payload in %s", request_data)
            return
        if not rd.get('status') == 'FINISHED':
            log.warning("request not finished %s", request_data)
            return
        received = received or datetime.now()
        ua = rd['remoteUserAgent']
        ua_family = cls._get_ua_family(ua)
        ip = rd['remoteAddr']
        lat = lon = None
        country = region = city = None
        if ip:
            client_loc = geoip.city(ip)
            if client_loc:
                lat, lon = client_loc['latitude'], client_loc['longitude'],
                country = client_loc['country_code']
                region = client_loc['region']
                city = client_loc['city']

        start_time = parse_datetime(rd['startTime'])

        rl = rd['responseLength']
        data = {'created': start_time,
                'received': received,
                'host': rd['host'],
                'ows_service': OWSService.get(rd.get('service')),
                'service': service,
                'request_path': rd['path'],
                'request_method': rd['httpMethod'],
                'response_status': rd['responseStatus'],
                'response_size': rl[0] if isinstance(rl, list) else rl,
                'response_type': rd.get('responseContentType'),
                'response_time': rd['totalTime'],
                'user_agent': ua,
                'user_agent_family': ua_family,
                'custom_id': rd['internalid'],
                'client_ip': ip,
                'client_lat': lat,
                'client_lon': lon,
                'client_country': country,
                'client_region': region,
                'client_city': city}
        inst = cls.objects.create(**data)
        resource_names = rd.get('resources', {}).get('string') or []
        if not isinstance(resource_names, (list, tuple,)):
            resource_names = [resource_names]
        resources = cls._get_resources('layer', resource_names)
        if resources:
            inst.resources.add(*resources)
            inst.save()
        return inst


class ExceptionEvent(models.Model):
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service)
    error_type = models.CharField(max_length=255, null=False, db_index=True)
    error_data = models.TextField(null=False, default='')
    request = models.ForeignKey(RequestEvent, related_name='exceptions')

    @classmethod
    def add_error(cls, from_service, error_type, stack_trace, request=None, created=None):
        received = datetime.now()
        if not isinstance(error_type, types.StringTypes):
            _cls = error_type.__class__
            error_type = '{}.{}'.format(_cls.__module__, _cls.__name__)

        if isinstance(stack_trace, (list, tuple,)):
            stack_trace = ''.join(stack_trace)
        if not isinstance(created, datetime):
            created = received
        return cls.objects.create(created=created,
                                  received=received,
                                  service=from_service,
                                  error_type=error_type,
                                  error_data=stack_trace,
                                  request=request)
    @property
    def url(self):
        return reverse('monitoring:api_exception', args=(self.id,))

class MetricLabel(models.Model):

    name = models.TextField(null=False, blank=True, default='')

    def __str__(self):
        return 'Metric Label: {}'.format(self.name)

class MetricValue(models.Model):
    valid_from = models.DateTimeField(db_index=True, null=False)
    valid_to = models.DateTimeField(db_index=True, null=False)
    service_metric = models.ForeignKey(ServiceTypeMetric)
    service = models.ForeignKey(Service)
    ows_service = models.ForeignKey(OWSService, null=True, blank=True)
    resource = models.ForeignKey(MonitoredResource, related_name='metric_values')
    label = models.ForeignKey(MetricLabel, related_name='metric_values')
    value = models.CharField(max_length=255, null=False, blank=False)
    value_num = models.DecimalField(max_digits=16, decimal_places=4, null=True, default=None, blank=True)
    value_raw = models.TextField(null=True, default=None, blank=True)
    data = JSONField(null=False, default={})

    class Meta:
        unique_together = (('valid_from', 'valid_to', 'service', 'service_metric', 'resource', 'label', 'ows_service',))

    def __str__(self):
        metric = self.service_metric.metric.name
        if self.label:
            metric = '{} [{}]'.format(metric, self.label.name)
        if self.resource and self.resource.type:
            metric = '{} for {}'.format(metric, '{}={}'.format(self.resource.name, self.resource.type))
        return 'Metric Value: {}: {}[{}] (since {} until {})'.format(metric, self.value, self.value_num, self.valid_from, self.valid_to)

    @classmethod
    def add(cls, metric, valid_from, valid_to, service, label,
            value_raw=None, resource=None, value=None, value_num=None, data=None, ows_service=None):
        """
        Create new MetricValue shortcut
        """

        service_metric = ServiceTypeMetric.objects.get(service_type=service.service_type, metric__name=metric)

        label, _ = MetricLabel.objects.get_or_create(name=label or 'count')
        if not resource:
            resource, _ = MonitoredResource.objects.get_or_create(type=MonitoredResource.TYPE_EMPTY, name='')
        try:
            inst = cls.objects.get(valid_from=valid_from,
                                   valid_to=valid_to,
                                   service=service,
                                   label=label,
                                   resource=resource,
                                   ows_service=ows_service,
                                   service_metric=service_metric)
            inst.value = value_raw
            inst.value_raw = value_raw
            inst.value_num = value_num
            inst.save()
            return inst
        except cls.DoesNotExist:
            pass
        return cls.objects.create(valid_from=valid_from,
                                  valid_to=valid_to,
                                  service=service,
                                  service_metric=service_metric,
                                  label=label,
                                  resource=resource,
                                  ows_service=ows_service,
                                  value=value_raw,
                                  value_raw=value_raw,
                                  value_num=value_num,
                                  data=data or {})


class BuiltIns(object):
    service_types = (ServiceType.TYPE_GEONODE, ServiceType.TYPE_GEOSERVER,)
    host_service_types = (ServiceType.TYPE_HOST_GN, ServiceType.TYPE_HOST_GS,)

    metrics_rate = ('response.time', 'response.size',)
    # metrics_count = ('request.count', 'request.method', 'request.

    geonode_metrics = ('request', 'request.count', 'request.ip', 'request.ua',
                       'request.ua.family', 'request.method', 'response.error.count',
                       'request.country', 'request.region', 'request.city',
                       'response.time', 'response.status', 'response.size',
                       'response.error.types',)
    host_metrics = ('load.1m', 'load.5m', 'load.15m',
                    'mem.free', 'mem.usage', 'mem.free',
                    'mem.buffers', 'mem.all',
                    'uptime', 'cpu.usage',
                    'storage.free', 'storage.total', 'storage.used',  # mountpoint is the label
                    'network.in', 'network.out', 'network.in.rate', 'network.out.rate',)

    counters = ('request.count',  'network.in', 'network.out', 'response.error.count',)
    rates = ('response.time', 'response.size', 'network.in.rate', 'network.out.rate', 'load.1m', 'load.5m', 'load.15m',)
    values = ('request.ip', 'request.ua', 'request.ua.family', 'request.method',
              'request.country', 'request.region', 'request.city', 'response.status', 'response.error.types',)


def populate():
    for m in BuiltIns.geonode_metrics + BuiltIns.host_metrics:
        Metric.objects.get_or_create(name=m)
    for st in BuiltIns.service_types + BuiltIns.host_service_types:
        ServiceType.objects.get_or_create(name=st)

    for st in BuiltIns.service_types:
        for m in BuiltIns.geonode_metrics:
            _st = ServiceType.objects.get(name=st)
            _m = Metric.objects.get(name=m)
            ServiceTypeMetric.objects.get_or_create(service_type=_st, metric=_m)
    for st in BuiltIns.host_service_types:
        for m in BuiltIns.host_metrics:
            _st = ServiceType.objects.get(name=st)
            _m = Metric.objects.get(name=m)
            ServiceTypeMetric.objects.get_or_create(service_type=_st, metric=_m)
    Metric.objects.filter(name__in=BuiltIns.counters).update(type=Metric.TYPE_COUNT)
    Metric.objects.filter(name__in=BuiltIns.rates).update(type=Metric.TYPE_RATE)
    Metric.objects.filter(name__in=BuiltIns.values).update(type=Metric.TYPE_VALUE)

    for otype, otype_name in OWSService.OWS_TYPES:
        OWSService.objects.get_or_create(name=otype)
