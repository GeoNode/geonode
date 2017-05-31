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
from socket import gethostbyname
from datetime import datetime

from django.db import models
from django.conf import settings
from jsonfield import JSONField

from django.utils.translation import ugettext_noop as _

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


class ServiceType(models.Model):
    TYPE_GEONODE = 'geonode'
    TYPE_GEOSERVER = 'geoserver'
    TYPE_HOST = 'host'

    TYPES = ((TYPE_GEONODE, _("GeoNode"),),
             (TYPE_GEOSERVER, _("GeoServer"),),
             (TYPE_HOST, _("Host",),),
             )
    name = models.CharField(max_length=255, unique=True, blank=False, null=False, choices=TYPES)


class Service(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    host = models.ForeignKey(Host, null=False)
    service_type = models.ForeignKey(ServiceType, null=False)


class MetricType(models.Model):
    TYPE_COUNTER = 'counter'
    TYPE_RATE = 'rate'
    TYPE_VALUE = 'value'
    TYPES = ((TYPE_COUNTER, _('Counter'),),
             (TYPE_RATE, _('Rate'),),
             (TYPE_VALUE, _('Value'),),
             )
    UNIT_NONE = ''
    UNIT_BPS = 'bps'
    UNIT_SECOND = 'second'
    UNIT_BIT = 'bit'
    UNIT_BYTE = 'byte'
    UNIT_MINUTE = 'minute'

    UNITS = ((UNIT_NONE, _('no unit'),),
             (UNIT_BPS, _('bits per second',),),
             (UNIT_SECOND, _('second'),),
             (UNIT_BIT, _('bit'),),
             (UNIT_BYTE, _('byte'),),
             (UNIT_MINUTE, _('minute'),),
             )

    name = models.CharField(max_length=32, choices=TYPES)
    unit = models.CharField(max_length=32, choices=UNITS, default=UNIT_NONE)


class Metric(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    type = models.ForeignKey(MetricType, null=False)


class ServiceTypeMetric(models.Model):
    service_type = models.ForeignKey(ServiceType)
    metric = models.ForeignKey(Metric)


class RequestEvent(models.Model):
    _methods = 'get post head options put delete'.upper().split(' ')
    _ows_types = 'tms wms-c wmts wcs wfs wms wps'.upper().split(' ')
    METHODS = zip(_methods, _methods)
    OWS_OTHER = 'other'
    OWS_TYPES = zip(_ows_types, _ows_types) + [(OWS_OTHER, _("Other"))]
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service)
    ows_type = models.CharField(max_length=255, choices=OWS_TYPES, default=OWS_OTHER, null=False, blank=False)
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
    resources = models.TextField(blank=True, default='', help_text=_("Resources name (style, layer, document, map)"))

    request_method = models.CharField(max_length=16, choices=METHODS)
    response_status = models.PositiveIntegerField(null=False, blank=False)
    response_size = models.PositiveIntegerField(null=False, default=0)
    response_time = models.PositiveIntegerField(null=False, default=0, help_text=_("Response processing time in ms"))
    response_type = models.CharField(max_length=255, null=False, default='')
    user_agent = models.CharField(max_length=255, null=True, blank=True, default=None)
    user_agent_family = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_ip = models.GenericIPAddressField(null=False)
    client_lat = models.DecimalField(max_digits=8, decimal_places=5, null=True, default=None, blank=True)
    client_lon = models.DecimalField(max_digits=8, decimal_places=5, null=True, default=None, blank=True)
    client_country = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_region = models.CharField(max_length=255, null=True, default=None, blank=True)
    client_city = models.CharField(max_length=255, null=True, default=None, blank=True)

    custom_id = models.CharField(max_length=255, null=True, default=None, db_index=True)

    @staticmethod
    def _get_geonode_resources(request):
        """
        Return serialized resources affected by request
        """
        rqmeta = getattr(request, '_metadata', {})
        resources = []
        for type_name in 'layer map document style'.split():
            res = rqmeta.get('{}s'.format(type_name)) or []
            for r in res:
                resources.append('{}={}'.format(type_name, r))
        return '\n'.join(resources)

    @staticmethod
    def _get_ua_family(ua):
        return str(user_agents.parse(ua))

    @classmethod
    def from_geonode(cls, service,  request, response):
        received = datetime.now()
        rqmeta = getattr(request, '_metadata', {})
        created = rqmeta.get('started', received)
        if not isinstance(created, datetime):
            created = parse_datetime(created)
        _ended = rqmeta.get('finished', datetime.now())
        duration = (_ended - created).seconds

        ua = request.META['HTTP_USER_AGENT']
        ua_family = cls._get_ua_family(ua)

        ip = request.get_host()
        lat = lon = None
        country = region = city = None
        if ip:
            ip = ip.split(':')[0]
            if settings.TEST and ip == 'testserver':
                ip = '127.0.0.1'
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
                'request_path': request.get_full_path(),
                'request_method': request.method,
                'resources': cls._get_geonode_resources(request),
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
        return cls.objects.create(**data)

    @classmethod
    def from_geoserver(cls, service, request_data):
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
        received = datetime.now()
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

        data = {'created': start_time,
                'received': received,
                'host': rd['host'],
                'service': service,
                'request_path': rd['path'],
                'request_method': rd['httpMethod'],
                'resources': rd['resources']['string'] if rd['service'] in cls._ows_types else [],
                'response_status': rd['responseStatus'],
                'response_size': rd['responseLength'],
                'response_type': rd.get('responseContentType'),
                'response_time': rd['totalTime'],
                'user_agent': ua,
                'user_agent_family': ua_family,
                'client_ip': ip,
                'client_lat': lat,
                'client_lon': lon,
                'client_country': country,
                'client_region': region,
                'client_city': city}

        return cls.objects.create(**data)


class ExceptionEvent(models.Model):
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service)
    error_type = models.CharField(max_length=255, null=False, db_index=True)
    error_data = models.TextField(null=False, default='')
    request = models.ForeignKey(RequestEvent)

    @classmethod
    def add_error(cls, from_service, error_type, stack_trace, request=None, created=None):
        received = datetime.now()
        if not isinstance(created, datetime):
            created = received
        return cls.objects.create(created, received, from_service, error_type, stack_trace, request=request)


class Event(models.Model):
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service_type = models.ForeignKey(ServiceTypeMetric)
    service = models.ForeignKey(Service)
    value = models.CharField(max_length=255, null=False, blank=False)
    value_num = models.DecimalField(max_digits=16, decimal_places=4, null=True, default=None, blank=True)
    value_raw = models.TextField(null=True, default=None, blank=True)
    data = JSONField(null=False, default={})


class BuiltIns(object):
    metric_types = (MetricType.TYPE_COUNTER, MetricType.TYPE_RATE, MetricType.TYPE_VALUE,)
    service_types = (ServiceType.TYPE_GEONODE, ServiceType.TYPE_GEOSERVER, ServiceType.TYPE_HOST,)
    geonode_metrics = ('requests', 'requests.wms', 'requests.wfs', 'requests.wcs', 'requests.layer',
                       'requests.document', 'requests.map', 'requests.admin', 'requests.response',
                       'requests.response.time', 'requests.response.ok', 'requests.response.error',
                       'requests.response.size', 'request.response',
                       )
    geoserver_metrics = ('requests',)
    host_metrics = ('load.1m', 'load.5m', 'load.10m',)


def populate():
    for st in BuiltIns.service_types:
        ServiceType.objects.get_or_create(name=st)
