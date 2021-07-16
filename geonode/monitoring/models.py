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
import pytz
from urllib.parse import urlparse

from socket import gethostbyname
from datetime import datetime, timedelta
from decimal import Decimal

from django import forms
from django.db import models
from django.conf import settings
from django.http import Http404

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models.fields.json import JSONField
from django.utils.translation import ugettext_noop as _

try:
    from django.contrib.gis.geoip2 import GeoIP2 as GeoIP
except ImportError:
    try:
        from django.contrib.gis.geoip import GeoIP
    except ImportError:
        pass

import user_agents
from ipware import get_client_ip
import pycountry
from geonode.monitoring.forms import MultiEmailField

from django.db.models import Sum, F, Case, When, Max

log = logging.getLogger(__name__)

GEOIP_DB = None


def get_geoip():
    # defer init until it's really needed
    # otherwise, some cli commands may fail (like updating geouip)
    global GEOIP_DB
    if GEOIP_DB is None:
        try:
            GEOIP_DB = GeoIP()
        except Exception as e:
            log.exception(e)
    return GEOIP_DB


class Host(models.Model):

    """
    Describes one physical instance
    """
    name = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False)
    ip = models.GenericIPAddressField(null=False, blank=False)
    active = models.BooleanField(null=False, blank=False, default=True)

    def __str__(self):
        return f'Host: {self.name} ({self.ip})'


class ServiceType(models.Model):

    """
    Service Type list
    """
    TYPE_GEONODE = 'geonode'
    TYPE_GEOSERVER = 'geoserver'
    TYPE_HOST_GN = 'hostgeonode'
    TYPE_HOST_GS = 'hostgeoserver'

    TYPES = ((TYPE_GEONODE, _("GeoNode"),),
             (TYPE_GEOSERVER, _("GeoServer"),),
             (TYPE_HOST_GS, _("Host (GeoServer)",),),
             (TYPE_HOST_GN, _("Host (GeoNode)",),),
             )
    name = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        choices=TYPES)

    def __str__(self):
        return f'Service Type: {self.name}'

    @property
    def is_system_monitor(self):
        return self.name in (self.TYPE_HOST_GN, self.TYPE_HOST_GS,)


class Service(models.Model):

    """
    Service is a entity describing deployed processes.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False)
    host = models.ForeignKey(Host, null=False, on_delete=models.CASCADE)
    check_interval = models.DurationField(
        null=False, blank=False, default=timedelta(seconds=60))
    last_check = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    service_type = models.ForeignKey(ServiceType, null=False, on_delete=models.CASCADE)
    active = models.BooleanField(null=False, blank=False, default=True)
    notes = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True, default='')

    def __str__(self):
        return f'Service: {self.name}@{self.host.name}'

    def get_metrics(self):
        return [m.metric for m in self.service_type.metric.all()]

    @property
    def is_hostgeonode(self):
        return self.service_type.name == ServiceType.TYPE_HOST_GN

    @property
    def is_hostgeoserver(self):
        return self.service_type.name == ServiceType.TYPE_HOST_GS

    @property
    def is_system_monitor(self):
        return self.service_type.is_system_monitor


class MonitoredResource(models.Model):
    TYPE_EMPTY = ''
    TYPE_LAYER = 'dataset'
    TYPE_MAP = 'map'
    TYPE_RESOURCE_BASE = 'resource_base'
    TYPE_DOCUMENT = 'document'
    TYPE_STYLE = 'style'
    TYPE_ADMIN = 'admin'
    TYPE_URL = 'url'
    TYPE_OTHER = 'other'
    _TYPES = (TYPE_EMPTY, TYPE_LAYER, TYPE_MAP,
              TYPE_DOCUMENT, TYPE_STYLE, TYPE_ADMIN,
              TYPE_URL, TYPE_OTHER,)

    TYPES = ((TYPE_EMPTY, _("No resource"),),
             (TYPE_LAYER, _("Dataset"),),
             (TYPE_MAP, _("Map"),),
             (TYPE_RESOURCE_BASE, _("Resource base"),),
             (TYPE_DOCUMENT, _("Document"),),
             (TYPE_STYLE, _("Style"),),
             (TYPE_ADMIN, _("Admin"),),
             (TYPE_URL, _("URL"),),
             (TYPE_OTHER, _("Other"),))

    name = models.CharField(max_length=255, null=False, blank=True, default='')
    type = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        choices=TYPES,
        default=TYPE_EMPTY)
    resource_id = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (('name', 'type',),)

    def __str__(self):
        return f'Monitored Resource: {self.name} {self.type}'

    @classmethod
    def get(cls, resource_type, resource_name, or_create=False):
        if or_create:
            res, _ = cls.objects.get_or_create(type=resource_type, name=resource_name)
            return res
        res = cls.objects.get(type=resource_type, name=resource_name)


class Metric(models.Model):
    TYPE_RATE = 'rate'
    TYPE_COUNT = 'count'
    TYPE_VALUE = 'value'
    TYPE_VALUE_NUMERIC = 'value_numeric'
    TYPES = ((TYPE_RATE, _("Rate"),),
             (TYPE_COUNT, _("Count"),),
             (TYPE_VALUE, _("Value"),),
             (TYPE_VALUE_NUMERIC, _("Value numeric"),),

             )

    AGGREGATE_MAP = {TYPE_RATE: ('(case when sum(samples_count)> 0 '
                                 'then sum(value_num*samples_count)'
                                 '/sum(samples_count) else 0 end)'),
                     TYPE_VALUE: 'sum(value_num)',
                     TYPE_VALUE_NUMERIC: 'max(value_num)',
                     TYPE_COUNT: 'sum(value_num)'}

    AGGREGATE_DJANGO_MAP = {TYPE_RATE: (Sum(Case(When(samples_count__gt=0,
                                                      then=F('value_num')),
                                                 default=0),
                                            output_field=models.DecimalField(max_digits=16,
                                                                             decimal_places=2)) /
                                        Sum(Case(When(samples_count__gt=0,
                                                      then=F('samples_count')),
                                                 default=1),
                                            output_field=models.DecimalField(max_digits=16,
                                                                             decimal_places=2))),
                            TYPE_VALUE: Sum(F('value_num')),
                            TYPE_COUNT: Sum(F('value_num')),
                            TYPE_VALUE_NUMERIC: Max(F('value_num'))
                            }

    UNIT_BYTES = 'B'
    UNIT_KILOBYTES = 'KB'
    UNIT_MEGABYTES = 'MB'
    UNIT_GIGABYTES = 'GB'
    UNIT_BPS = 'B/s'
    UNIT_MBPS = 'MB/s'
    UNIT_KBPS = 'KB/s'
    UNIT_GBPS = 'GB/s'
    UNIT_SECONDS = 's'
    UNIT_COUNT = 'Count'
    UNIT_RATE = 'Rate'
    UNIT_PERCENTAGE = '%'

    UNITS = ((UNIT_BYTES, _("Bytes"),),
             (UNIT_KILOBYTES, _("Kilobytes"),),
             (UNIT_MEGABYTES, _("Megabytes"),),
             (UNIT_GIGABYTES, _("Gigabytes"),),
             (UNIT_BPS, _("Bytes per second"),),
             (UNIT_KBPS, _("Kilobytes per second"),),
             (UNIT_MBPS, _("Megabytes per second"),),
             (UNIT_GBPS, _("Gigabytes per second"),),
             (UNIT_SECONDS, _("Seconds"),),
             (UNIT_RATE, _("Rate"),),
             (UNIT_PERCENTAGE, _("Percentage"),),
             (UNIT_COUNT, _("Count"),))

    name = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=255, null=True)
    type = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        default=TYPE_RATE,
        choices=TYPES)
    unit = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=UNITS)

    def get_aggregate_field(self):
        return self.AGGREGATE_DJANGO_MAP[self.type]

    def get_aggregate_name(self):
        return self.AGGREGATE_MAP[self.type]

    def __unicode__(self):
        return f"Metric: {self.name}"

    @property
    def is_rate(self):
        return self.type == self.TYPE_RATE

    @property
    def is_count(self):
        return self.type == self.TYPE_COUNT

    @property
    def is_value_numeric(self):
        return self.type == self.TYPE_VALUE_NUMERIC

    @property
    def is_value(self):
        return self.type == self.TYPE_VALUE

    @classmethod
    def get_for(cls, name, service=None):
        metric = None
        if service:
            try:
                stype = ServiceTypeMetric.objects.get(
                    service_type=service.service_type, metric__name=name)
                metric = stype.metric
            except ServiceTypeMetric.DoesNotExist:
                raise Http404()
        else:
            metric = Metric.objects.filter(name=name).first()
        return metric


class ServiceTypeMetric(models.Model):
    service_type = models.ForeignKey(ServiceType, related_name='metric', on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, related_name='service_type', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.service_type} - {self.metric}'


class EventType(models.Model):
    _ows_types = 'tms wms-c wmts wcs wfs wms wps'.upper().split(' ')

    # OWS_OTHER = 'other'
    # OWS_ALL = 'all'
    # OWS_TYPES = zip(_ows_types, _ows_types) + \
    #     [(OWS_ALL, _("All"))] + [(OWS_OTHER, _("Other"))]

    EVENT_DOWNLOAD = 'download'
    EVENT_CREATE = 'create'
    EVENT_CHANGE = 'change'
    EVENT_CHANGE_METADATA = 'change_metadata'
    EVENT_REMOVE = 'remove'
    EVENT_VIEW = 'view'
    EVENT_VIEW_METADATA = 'view_metadata'
    EVENT_PUBLISH = 'publish'
    EVENT_UPLOAD = 'upload'
    EVENT_GEOSERVER = 'geoserver'  # other event from GS
    # special event types
    EVENT_OWS = 'OWS:ALL'  # any ows event
    EVENT_OTHER = 'other'  # non-ows event
    EVENT_ALL = 'all'  # all events - baseline: ows + non-ows

    EVENT_TYPES = list(zip([f'OWS:{ows}' for ows in _ows_types], _ows_types)) + \
        [(EVENT_OTHER, _("Not OWS"))] +\
        [(EVENT_OWS, _("Any OWS"))] +\
        [(EVENT_ALL, _("All"))] +\
        [(EVENT_CREATE, _("Create"))] +\
        [(EVENT_UPLOAD, _("Upload"))] +\
        [(EVENT_CHANGE, _("Change"))] +\
        [(EVENT_CHANGE_METADATA, _("Change Metadata"))] +\
        [(EVENT_VIEW_METADATA, _("View Metadata"))] +\
        [(EVENT_VIEW, _("View"))] +\
        [(EVENT_DOWNLOAD, _("Download"))] +\
        [(EVENT_PUBLISH, _("Publish"))] +\
        [(EVENT_REMOVE, _("Remove"))] +\
        [(EVENT_GEOSERVER, _("Geoserver event"))]

    name = models.CharField(max_length=16, unique=True,
                            choices=EVENT_TYPES,
                            null=False,
                            blank=False)

    def __str__(self):
        return f'Event Type: {self.name}'

    @classmethod
    def get(cls, service_name=None):
        if not service_name:
            return
        try:
            q = models.Q(name=service_name)
            try:
                s = int(service_name)
            except (ValueError, TypeError,):
                s = None
            if s:
                q = q | models.Q(id=s)
            return cls.objects.get(q)
        except cls.DoesNotExist:
            return

    @property
    def is_all(self):
        return self.name == self.EVENT_ALL

    @property
    def is_other(self):
        return self.name == self.EVENT_OTHER

    @property
    def is_ows(self):
        return self.name.upper().startswith('OWS:')

    @property
    def is_download(self):
        return self.name == self.EVENT_DOWNLOAD

    @property
    def is_view(self):
        return self.name == self.EVENT_VIEW


class RequestEvent(models.Model):
    _methods = 'get post head options put delete'.upper().split(' ')
    METHODS = list(zip(_methods, _methods))
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    event_type = models.ForeignKey(EventType, blank=True, null=True, on_delete=models.CASCADE)
    host = models.CharField(max_length=255, blank=True, default='')
    request_path = models.TextField(blank=False, default='')

    # resources is a list of affected resources. it is buld as a pair of type and name:
    #  layer=geonode:sample_dataset01
    # or
    #  document=documents/id
    # or
    #  map=some map
    #
    # list is separated with newline
    # resources = models.TextField(blank=True, default='',
    # help_text=_("Resources name (style, layer, document, map)"))
    resources = models.ManyToManyField(MonitoredResource, blank=True,
                                       help_text=_(
                                           "List of resources affected"),
                                       related_name='requests')

    request_method = models.CharField(max_length=16, choices=METHODS)
    response_status = models.PositiveIntegerField(null=False, blank=False)
    response_size = models.PositiveIntegerField(null=False, default=0)
    response_time = models.PositiveIntegerField(
        null=False, default=0, help_text=_("Response processing time in ms"))
    response_type = models.CharField(
        max_length=255, null=True, blank=True, default='')
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None)
    user_agent_family = models.CharField(
        max_length=255, null=True, default=None, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    client_lat = models.DecimalField(
        max_digits=11,
        decimal_places=5,
        null=True,
        default=None,
        blank=True)
    client_lon = models.DecimalField(
        max_digits=11,
        decimal_places=5,
        null=True,
        default=None,
        blank=True)
    client_country = models.CharField(
        max_length=255, null=True, default=None, blank=True)
    client_region = models.CharField(
        max_length=255, null=True, default=None, blank=True)
    client_city = models.CharField(
        max_length=255,
        null=True,
        default=None,
        blank=True)

    custom_id = models.CharField(
        max_length=255,
        null=True,
        default=None,
        blank=True,
        db_index=True)
    # keep user anonymized identifier
    user_identifier = models.CharField(
        max_length=255,
        null=True,
        default=None,
        blank=True,
        db_index=True)
    user_username = models.CharField(
        max_length=150,
        default=None,
        null=True,
        blank=True)

    @classmethod
    def _get_resources(cls, type_name, resources_list):
        out = []
        for r in resources_list:
            if r is None:
                continue
            rinst, _ = MonitoredResource.objects.get_or_create(
                name=r, type=type_name)
            out.append(rinst)
        return out

    @classmethod
    def _get_or_create_resources(cls, res_name, res_type, res_id):
        out = []
        r, _ = MonitoredResource.objects.get_or_create(
            name=res_name, type=res_type
        )
        if r and res_id:
            r.resource_id = res_id
            r.save()
        out.append(r)
        return out

    @classmethod
    def _get_geonode_resources(cls, request):
        """
        Return serialized resources affected by request
        """
        rqmeta = getattr(request, '_monitoring', {})
        events = rqmeta['events']
        resources = []
        # for type_name in 'layer map document style'.split():
        #     res = rqmeta['resources'].get(type_name) or []
        #     resources.extend(cls._get_resources(type_name, res))

        for evt_type, res_type, res_name, res_id in events:
            resources.extend(cls._get_or_create_resources(res_name, res_type, res_id))

        return resources

    @classmethod
    def _get_event_type(cls, request, default_event_type='view'):
        """
        Returns event type based on events
        """
        rqmeta = getattr(request, '_monitoring', {})
        events = {e[0] for e in rqmeta['events']}
        event_name = default_event_type
        if len(events) == 1:
            event_name = events.pop()
        elif len(events) == 2 and default_event_type in events:
            events.remove(default_event_type)
            event_name = events.pop()
        return EventType.get(event_name)

    @staticmethod
    def _get_ua_family(ua):
        return str(user_agents.parse(ua))

    @classmethod
    def _get_user_agent(cls, ua):
        ua_family = cls._get_ua_family(ua)
        return {'user_agent': ua,
                'user_agent_family': ua_family}

    @classmethod
    def _get_user_consent(cls, request):
        return settings.USER_ANALYTICS_ENABLED
        # if  request.user.is_authenticated:
        #    return request.user.allow_analytics
        # return True

    @classmethod
    def _get_user_location(cls, request_ip):
        out = {}
        lat = lon = None
        country = region = city = None
        if request_ip:
            geoip = get_geoip()
            if request_ip in ('127.0.0.1',):
                return out
            try:
                client_loc = geoip.city(request_ip)
            except Exception as err:
                log.warning("Cannot resolve %s: %s", request_ip, err)
                client_loc = None

            if client_loc:
                lat, lon = client_loc['latitude'], client_loc['longitude'],
                country = client_loc.get(
                    'country_code3') or client_loc['country_code']
                if len(country) == 2:
                    _c = pycountry.countries.get(alpha_2=country)
                    country = _c.alpha_3
                region = client_loc['region']
                city = client_loc['city']

                out.update({'client_ip': request_ip,
                            'client_lat': lat,
                            'client_lon': lon,
                            'client_country': country,
                            'client_region': region,
                            'client_city': city})
        return out

    @classmethod
    def _get_user_data_gn(cls, request):
        out = {}
        # check consent
        if not cls._get_user_consent(request):
            return out

        rqmeta = getattr(request, '_monitoring', {})
        if rqmeta.get('user_identifier'):
            out['user_identifier'] = rqmeta.get('user_identifier')
        if rqmeta.get('user_username'):
            out['user_username'] = rqmeta.get('user_username')

        ua = request.META.get('HTTP_USER_AGENT') or ''
        ua_data = cls._get_user_agent(ua)
        out.update(ua_data)

        request_ip, is_routable = get_client_ip(request)
        if request_ip and is_routable:
            location_data = cls._get_user_location(request_ip)
            out.update(location_data)
        return out

    @classmethod
    def _get_user_data_gs(cls, request):
        out = {}

        # check consent
        # if not cls._get_user_consent(request):
        #    return out

        ua = request.get('remoteUserAgent') or ''
        ua_data = cls._get_user_agent(ua)
        out.update(ua_data)

        request_ip = request.get('remoteAddr')
        if request_ip:
            location_data = cls._get_user_location(request_ip)
            out.update(location_data)
        return out

    @classmethod
    def from_geonode(cls, service, request, response):
        from geonode.utils import parse_datetime

        received = datetime.utcnow().replace(tzinfo=pytz.utc)
        rqmeta = getattr(request, '_monitoring', {})
        created = rqmeta.get('started', received)
        if not isinstance(created, datetime):
            created = parse_datetime(created)
        _ended = rqmeta.get(
            'finished',
            datetime.utcnow().replace(
                tzinfo=pytz.utc))
        duration = (_ended - created).microseconds / 1000.0

        sensitive_data = cls._get_user_data_gn(request)
        event_type = cls._get_event_type(request)

        # ua = request.META.get('HTTP_USER_AGENT') or ''
        # ua_family = cls._get_ua_family(ua)
        #
        # ip, is_routable = get_client_ip(request)
        # lat = lon = None
        # country = region = city = None
        # if ip and is_routable:
        #     ip = ip.split(':')[0]
        #     if settings.TEST and ip == 'testserver':
        #         ip = '127.0.0.1'
        #     try:
        #         ip = gethostbyname(ip)
        #     except Exception as err:
        #         pass
        #
        #     geoip = get_geoip()
        #     try:
        #         client_loc = geoip.city(ip)
        #     except Exception as err:
        #         log.warning("Cannot resolve %s: %s", ip, err)
        #         client_loc = None
        #
        #     if client_loc:
        #         lat, lon = client_loc['latitude'], client_loc['longitude'],
        #         country = client_loc.get(
        #             'country_code3') or client_loc['country_code']
        #         if len(country) == 2:
        #             _c = pycountry.countries.get(alpha_2=country)
        #             country = _c.alpha_3
        #
        #         region = client_loc['region']
        #         city = client_loc['city']

        data = {'received': received,
                'created': created,
                'host': request.get_host(),
                'service': service,
                'user_identifier': None,
                'user_username': None,
                'event_type': event_type,
                'request_path': request.get_full_path(),
                'request_method': request.method,
                'response_status': response.status_code,
                'response_size':
                    response.get('Content-length') or len(response.getvalue()),
                'response_type': response.get('Content-type'),
                'response_time': duration}

        data.update(sensitive_data)

        try:
            inst = cls.objects.create(**data)
            resources = cls._get_geonode_resources(request)
            if resources:
                inst.resources.add(*resources)
                inst.save()
            return inst
        except Exception:
            return None

    @classmethod
    def from_geoserver(cls, service, request_data, received=None):
        """
        Writes RequestEvent for data from audit log in GS
        """
        from dateutil.tz import tzlocal
        from geonode.utils import parse_datetime

        rd = request_data.get('org.geoserver.monitor.RequestData')
        if not rd:
            log.warning("No request data payload in %s", request_data)
            return
        if not rd.get('status') in ('FINISHED', 'FAILED',):
            log.warning("request not finished %s", rd.get('status'))
            return
        received = received or datetime.utcnow().replace(tzinfo=pytz.utc)

        sensitive_data = cls._get_user_data_gs(rd)

        # ua = rd.get('remoteUserAgent') or ''
        # ua_family = cls._get_ua_family(ua)
        # ip = rd['remoteAddr']
        # lat = lon = None
        # country = region = city = None
        # if ip:
        #     geoip = get_geoip()
        #     try:
        #         client_loc = geoip.city(ip)
        #     except Exception as err:
        #         log.warning("Cannot resolve %s: %s", ip, err)
        #         client_loc = None
        #
        #     if client_loc:
        #         lat, lon = client_loc['latitude'], client_loc['longitude'],
        #         country = client_loc.get(
        #             'country_code3') or client_loc['country_code']
        #         if len(country) == 2:
        #             _c = pycountry.countries.get(alpha_2=country)
        #             country = _c.alpha_3
        #         region = client_loc['region']
        #         city = client_loc['city']

        utc = pytz.utc
        try:
            local_tz = pytz.timezone(datetime.now(tzlocal()).tzname())
        except Exception:
            local_tz = pytz.timezone(settings.TIME_ZONE)

        start_time = parse_datetime(rd['startTime'])
        # Assuming GeoServer stores dates @ UTC
        start_time = start_time.replace(tzinfo=utc).astimezone(local_tz)

        rl = rd['responseLength']
        event_type_name = rd.get('service')
        if event_type_name:
            event_type = EventType.get(f'OWS:{event_type_name.upper()}')
        else:
            event_type = EventType.get(EventType.EVENT_GEOSERVER)

        if rd.get('queryString'):
            request_path = f"{rd['path']}?{rd['queryString']}"
        else:
            request_path = rd['path']
        data = {'created': start_time,
                'received': received,
                'host': rd['host'],
                'event_type': event_type,
                'service': service,
                'request_path': request_path,
                'request_method': rd['httpMethod'],
                'response_status': rd['responseStatus'],
                'response_size': rl[0] if isinstance(rl, list) else rl,
                'response_type': rd.get('responseContentType'),
                'response_time': rd['totalTime']}
        data.update(sensitive_data)

        inst = cls.objects.create(**data)
        resource_names = (rd.get('resources') or {}).get('string') or []
        if not isinstance(resource_names, (list, tuple)):
            resource_names = [resource_names]
        resources = cls._get_resources('layer', resource_names)
        if rd.get('error'):
            try:
                etype = rd[
                    'error'][
                        '@class'] if '@class' in rd[
                            'error'] else rd[
                                'error'][
                    'class']
                edata = '\n'.join(rd['error']['stackTrace']['trace'])
                emessage = rd['error']['detailMessage'] if 'detailMessage' in rd['error'] else str(rd['error'])
                ExceptionEvent.add_error(
                    service, etype, edata, message=emessage, request=inst)
            except Exception:
                emessage = rd['error']['detailMessage'] if 'detailMessage' in rd['error'] else str(rd['error'])
                ExceptionEvent.add_error(service, 'undefined',
                                         '\n'.join(
                                             rd['error']['stackTrace']['trace']),
                                         message=emessage, request=inst)
        if resources:
            inst.resources.add(*resources)
            inst.save()
        return inst


class ExceptionEvent(models.Model):
    created = models.DateTimeField(db_index=True, null=False)
    received = models.DateTimeField(db_index=True, null=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    error_type = models.CharField(max_length=255, null=False, db_index=True)
    error_message = models.TextField(null=False, default='')
    error_data = models.TextField(null=False, default='')
    request = models.ForeignKey(RequestEvent, related_name='exceptions', on_delete=models.CASCADE)

    @classmethod
    def add_error(cls, from_service, error_type, stack_trace,
                  request=None, created=None, message=None):
        received = datetime.utcnow().replace(tzinfo=pytz.utc)
        if not isinstance(error_type, str):
            _cls = error_type.__class__
            error_type = f'{_cls.__module__}.{_cls.__name__}'
        if not message:
            message = str(error_type)
        if isinstance(stack_trace, (list, tuple)):
            stack_trace = ''.join(stack_trace)

        if not isinstance(created, datetime):
            created = received
        return cls.objects.create(created=created,
                                  received=received,
                                  service=from_service,
                                  error_type=error_type,
                                  error_data=stack_trace,
                                  error_message=message or '',
                                  request=request)

    @property
    def url(self):
        return reverse('monitoring:api_exception', args=(self.id,))

    @property
    def service_data(self):
        return {'name': self.service.name,
                'type': self.service.service_type.name}

    def expose(self):
        e = self
        data = {'error_type': e.error_type,
                'error_data': e.error_data,
                'error_message': e.error_message,
                'created': e.created,
                'service': {'name': e.service.name,
                            'type': e.service.service_type.name},
                'request': {'request': {'created': e.request.created,
                                        'method': e.request.request_method,
                                        'path': e.request.request_path,
                                        'host': e.request.host,
                                        },
                            'event_type': e.request.event_type.name if e.request.event_type else None,
                            'resources': [{'name': str(r)} for r in e.request.resources.all()],
                            'client': {'ip': e.request.client_ip,
                                       'user_agent': e.request.user_agent,
                                       'user_agent_family': e.request.user_agent_family,
                                       'position': {'lat': e.request.client_lat,
                                                    'lon': e.request.client_lon,
                                                    'country': e.request.client_country,
                                                    'city': e.request.client_city}
                                       },
                            'response': {'size': e.request.response_size,
                                         'status': e.request.response_status,
                                         'time': e.request.response_time,
                                         'type': e.request.response_type}
                            }
                }
        return data


class MetricLabel(models.Model):

    name = models.TextField(null=False, blank=True, default='')
    user = models.CharField(
        max_length=150,
        default=None,
        null=True,
        blank=True)

    def __unicode__(self):
        return f"Metric Label: {self.name.encode('ascii', 'ignore')}"


class MetricValue(models.Model):
    valid_from = models.DateTimeField(db_index=True, null=False)
    valid_to = models.DateTimeField(db_index=True, null=False)
    service_metric = models.ForeignKey(ServiceTypeMetric, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    event_type = models.ForeignKey(
        EventType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='metric_values')
    resource = models.ForeignKey(
        MonitoredResource,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='metric_values')
    label = models.ForeignKey(MetricLabel, related_name='metric_values', on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=False, blank=False)
    value_num = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        default=None,
        blank=True)
    value_raw = models.TextField(null=True, default=None, blank=True)
    samples_count = models.PositiveIntegerField(
        null=False, default=0, blank=False)
    data = JSONField(null=False, default=dict)

    class Meta:
        unique_together = (
            ('valid_from',
             'valid_to',
             'service',
             'service_metric',
             'resource',
             'label',
             'event_type',
             ))

    def __str__(self):
        metric = self.service_metric.metric.name
        if self.label:
            _l = self.label.name
            metric = f'{metric} [{_l}]'
        if self.resource and self.resource.type:
            _s = f'{self.resource.type}={self.resource.name}'
            metric = f'{metric} for {_s}'
        return f'Metric Value: {metric}: [{self.value}] (since {self.valid_from} until {self.valid_to})'

    @classmethod
    def add(cls, metric, valid_from, valid_to, service, label,
            value_raw=None, resource=None,
            value=None, value_num=None,
            data=None, event_type=None, samples_count=None):
        """
        Create new MetricValue shortcut
        """

        if isinstance(metric, Metric):
            service_metric = ServiceTypeMetric.objects.get(
                service_type=service.service_type, metric=metric)
        else:
            service_metric = ServiceTypeMetric.objects.get(
                service_type=service.service_type, metric__name=metric)

        label_name = label
        label_user = None
        if label and isinstance(label, tuple):
            label_name = label[0]
            label_user = label[1]
        try:
            label, c = MetricLabel.objects.get_or_create(name=label_name or 'count')
        except MetricLabel.MultipleObjectsReturned:
            c = False
            label = MetricLabel.objects.filter(name=label_name).first()
        if c and label_user:
            label.user = label_user
            label.save()
        if event_type:
            if not isinstance(event_type, EventType):
                event_type = EventType.get(event_type)
        try:
            inst = cls.objects.filter(
                valid_from=valid_from,
                valid_to=valid_to,
                service=service,
                label=label,
                resource=resource,
                event_type=event_type,
                service_metric=service_metric).last()
            if inst:
                inst.value = abs(value) if value else 0
                inst.value_raw = abs(value_raw) if value_raw else 0
                inst.value_num = abs(value_num) if value_num else 0
                inst.samples_count = samples_count or 0
                inst.save()
                return inst
        except cls.DoesNotExist:
            pass
        return cls.objects.create(
            valid_from=valid_from,
            valid_to=valid_to,
            service=service,
            service_metric=service_metric,
            label=label,
            resource=resource,
            event_type=event_type,
            value=value_raw,
            value_raw=value_raw,
            value_num=value_num,
            samples_count=samples_count or 0,
            data=data or {})

    @classmethod
    def get_for(cls, metric, service=None, valid_on=None,
                resource=None, label=None, event_type=None):
        qparams = models.Q()
        if isinstance(metric, Metric):
            qparams = qparams & models.Q(service_metric__metric=metric)
        else:
            qparams = qparams & models.Q(service_metric__metric__name=metric)
        if service:
            if isinstance(service, Service):
                qparams = qparams & models.Q(
                    service_metric__service_type=service.service_type)
            elif isinstance(service, ServiceType):
                qparams = qparams & models.Q(
                    service_metric__service_type=service)
            else:
                qparams = qparams & models.Q(
                    service_metric__service_type__name=service)
        if valid_on:
            qwhen = models.Q(
                valid_from__lte=valid_on) & models.Q(
                valid_to__gte=valid_on)
            qparams = qparams & qwhen
        if label:
            if isinstance(label, MetricLabel):
                qparams = qparams & models.Q(label=label)
            else:
                qparams = qparams & models.Q(label__name=label)
        if resource:
            if isinstance(resource, MonitoredResource):
                qparams = qparams & models.Q(resource=resource)
            else:
                rtype, rname = resource.split('=')
                qparams = qparams & models.Q(
                    resource__type=rtype, resource__name=rname)
        if event_type:
            if isinstance(event_type, EventType):
                qparams = qparams & models.Q(event_type=event_type)
            else:
                qparams = qparams & models.Q(event_type__name=event_type)

        q = cls.objects.filter(qparams).order_by('-valid_to')
        return q


class NotificationCheck(models.Model):

    GRACE_PERIOD_1M = timedelta(seconds=60)
    GRACE_PERIOD_5M = timedelta(seconds=5 * 60)
    GRACE_PERIOD_10M = timedelta(seconds=10 * 60)
    GRACE_PERIOD_30M = timedelta(seconds=30 * 60)
    GRACE_PERIOD_1H = timedelta(seconds=60 * 60)
    GRACE_PERIODS = ((GRACE_PERIOD_1M, _("1 minute"),),
                     (GRACE_PERIOD_5M, _("5 minutes"),),
                     (GRACE_PERIOD_10M, _("10 minutes"),),
                     (GRACE_PERIOD_30M, _("30 minutes"),),
                     (GRACE_PERIOD_1H, _("1 hour"),),
                     )

    SEVERITY_WARNING = 'warning'
    SEVERITY_ERROR = 'error'
    SEVERITY_FATAL = 'fatal'

    SEVERITIES = ((SEVERITY_WARNING, _("Warning"),),
                  (SEVERITY_ERROR, _("Error"),),
                  (SEVERITY_FATAL, _("Fatal"),),
                  )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True)
    description = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Description of the alert")
    user_threshold = JSONField(default=dict, null=False, blank=False,
                               help_text=_("Expected min/max values for user configuration"))
    metrics = models.ManyToManyField(
        Metric,
        through='NotificationMetricDefinition',
        related_name='+')
    last_send = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Marker of last delivery"))
    grace_period = models.DurationField(
        null=False, default=GRACE_PERIOD_10M, choices=GRACE_PERIODS,
        help_text=_("Minimum time between subsequent notifications"))
    severity = models.CharField(max_length=32,
                                null=False,
                                default=SEVERITY_ERROR,
                                choices=SEVERITIES,
                                help_text=_("How severe would be error from this notification"))
    active = models.BooleanField(
        default=True,
        null=False,
        blank=False,
        help_text=_("Is it active"))

    def __str__(self):
        return f"Notification Check #{self.id}: {self.name}"

    @property
    def notification_subject(self):
        return _(f"{self.severity}: {self.name}")

    @property
    def is_warning(self):
        return self.severity == self.SEVERITY_WARNING

    @property
    def is_error(self):
        return self.severity == self.SEVERITY_ERROR

    @property
    def is_fatal(self):
        return self.severity == self.SEVERITY_FATAL

    @property
    def can_send(self):
        if self.last_send is None:
            return True
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.last_send = self.last_send.replace(tzinfo=pytz.utc)
        if (self.last_send + self.grace_period) > now:
            return False
        return True

    def mark_send(self):
        self.last_send = datetime.utcnow().replace(tzinfo=pytz.utc)
        self.save()

    @property
    def url(self):
        return reverse(
            'monitoring:api_user_notification_config', args=(self.id,))

    def get_users(self):
        return [r.user for r in self.receivers.exclude(
            user__isnull=True).select_related('user')]

    def get_emails(self):
        return [r.email for r in self.receivers.exclude(email__isnull=True)]

    @property
    def emails(self):
        return [u for u in self.get_emails() if u] + \
            [u.email for u in self.get_users() if u.email]

    def check_notifications(self, for_timestamp=None):
        checks = []
        for ch in self.checks.all():
            try:
                ch.check_metric(for_timestamp=for_timestamp)
            except MetricNotificationCheck.MetricValueError as err:
                checks.append(err)
            # no value available, ignoring
            except ValueError:
                pass
        return checks

    @classmethod
    def check_for(cls, for_timestamp=None, active=None):
        checked = []
        q = {}
        if active is None:
            q['active'] = True
        elif active is not None:
            q['active'] = active
        for n in cls.objects.filter(**q):
            checked.append(
                (n, n.check_notifications(
                    for_timestamp=for_timestamp),))
        return checked

    @classmethod
    def get_steps(cls, min_, max_, thresholds):
        if isinstance(thresholds, (int, float, Decimal)):
            if min_ is None or max_ is None:
                raise ValueError(
                    "Cannot use numeric threshold if one of min/max is None")
            step = (max_ - min_) / thresholds
            current = min_
            thresholds = []
            while current < max_:
                thresholds.append(current)
                current += step

        if isinstance(thresholds, (tuple, types.GeneratorType)):
            thresholds = list(thresholds)
        elif isinstance(thresholds, list) or thresholds is None:
            pass
        else:
            raise TypeError(
                f"Unsupported threshold type: {thresholds} ({type(thresholds)})")
        return thresholds

    @classmethod
    def create(cls, name, description, user_threshold, severity=None):
        inst, _ = cls.objects.get_or_create(name=name)
        inst.description = description
        user_thresholds = {}
        for (metric_name, field_opt, use_service,
             use_resource, use_label, use_event_type,
             minimum, maximum, thresholds, _description) in user_threshold:

            # metric_name is a string for metric.name
            # field opt is NotificationMetricDefinition.FIELD_OPTION* value
            # use_* are flags to set limitations on scope of alert
            # minimum, maximum are min/max for allowed values
            #   if one is None, that means there's no value limit in that direction
            # thresholds can be :
            #     * list of values between min and max or
            #     * one number of steps between min and max
            #     * None, then user can enter value manually
            #
            # example:
            # notfication: system overload
            #  ('request.count', 'min_value', True, True, True, True,
            #    0, None, (100, 200, 500, 1000,)

            metric, _ = Metric.objects.get_or_create(name=metric_name)
            steps = cls.get_steps(minimum, maximum, thresholds)
            nm, _ = NotificationMetricDefinition.objects.get_or_create(
                notification_check=inst,
                metric=metric,
                description=_description,
                min_value=minimum,
                max_value=maximum,
                steps=len(steps) if steps else None,
                field_option=field_opt)
            user_thresholds[nm.field_name] = {'min': minimum,
                                              'max': maximum,
                                              'metric': metric_name,
                                              'description': _description,
                                              'steps': steps}
        inst.user_threshold = user_thresholds
        if severity is not None:
            inst.severity = severity
        inst.save()
        return inst

    def get_user_threshold(self, notification_def):

        return self.user_threshold[notification_def.field_name]

    def get_user_form(self, *args_, **kwargs_):
        """
        Return form to validate metric thresholds input from user.
        """
        this = self

        defs = this.definitions.all()

        class F(forms.Form):
            emails = MultiEmailField(required=False)
            severity = forms.ChoiceField(
                choices=self.SEVERITIES, required=False)
            active = forms.BooleanField(required=False)
            grace_period = forms.DurationField(required=False)

            def __init__(self, *args, **kwargs):
                initial = {
                    'emails': list(this.get_emails()) + [u.email for u in this.get_users()],
                    'severity': this.severity,
                    'active': this.active,
                    'grace_period': this.grace_period}
                kwargs['initial'] = initial
                super().__init__(*args, **kwargs)
                fields = self.fields
                for d in defs:
                    # def.get_fields() can return several fields,
                    # especially when we have per-resource monitoring
                    _fields = d.get_fields()
                    for field in _fields:
                        fields[field.name] = field

        return F(*args_, **kwargs_)

    def process_user_form(self, data, is_json=False):
        """
        Process form data from user and create Notifica
        """

        inst = self
        current_checks = self.checks.all()
        if is_json:
            emails = data.pop('emails', None)
            if emails and isinstance(emails, list):
                emails = '\n'.join(emails)
                data['emails'] = emails

        f = self.get_user_form(data=data)
        if not f.is_valid():
            err = forms.ValidationError(f.errors)
            err.errors = f.errors
            raise err
        current_checks.delete()
        out = []
        fdata = f.cleaned_data
        emails = fdata.pop('emails')
        active = fdata.pop('active')
        severity = fdata.pop('severity', None)
        grace_period = fdata.pop('grace_period', None)
        if severity is not None:
            self.severity = severity
        if active is not None:
            self.active = active
        if grace_period is not None:
            self.grace_period = grace_period
        self.save()

        for key, val in fdata.items():
            # do not create notification check if check value is empty
            if val is None or val == '':
                continue
            _v = key.split('.')
            # syntax of field name:
            # field_id.metric.name.field_name
            mname, field = '.'.join(_v[:-1]), _v[-1]
            metric = Metric.objects.get(name=mname)
            if field == 'max_timeout':
                val = timedelta(seconds=int(val))
            ndef = self.get_definition_for(key)
            ncheck = MetricNotificationCheck.objects.create(
                notification_check=inst,
                metric=metric,
                definition=ndef,
                **{field: val})
            out.append(ncheck)
        U = get_user_model()
        self.receivers.all().delete()

        for email in emails:
            params = {'notification_check': self}
            try:
                params['user'] = U.objects.get(email=email)
            except U.DoesNotExist:
                params['email'] = email
            NotificationReceiver.objects.create(**params)
        return out

    def get_definition_for(self, def_name):
        _v = def_name.split('.')
        # syntax of field name:
        # field_id.metric.name.field_name
        mname, field = '.'.join(_v[:-1]), _v[-1]
        return self.definitions.get(metric__name=mname, field_option=field)


class NotificationReceiver(models.Model):
    notification_check = models.ForeignKey(
        NotificationCheck, related_name='receivers', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not (self.user or self.email):
            raise ValueError("Cannot save empty notification receiver")
        super().save(*args, **kwargs)


class NotificationMetricDefinition(models.Model):
    FIELD_OPTION_MIN_VALUE = 'min_value'
    FIELD_OPTION_MAX_VALUE = 'max_value'
    FIELD_OPTION_MAX_TIMEOUT = 'max_timeout'
    FIELD_OPTION_CHOICES = (
        (FIELD_OPTION_MIN_VALUE, _("Value must be above"),),
        (FIELD_OPTION_MAX_VALUE, _("Value must be below"),),
        (FIELD_OPTION_MAX_TIMEOUT, _("Last update must not be older than"),))

    notification_check = models.ForeignKey(
        NotificationCheck, related_name='definitions', on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, related_name='notification_checks', on_delete=models.CASCADE)
    use_service = models.BooleanField(null=False, default=False)
    use_resource = models.BooleanField(null=False, default=False)
    use_label = models.BooleanField(null=False, default=False)
    use_event_type = models.BooleanField(null=False, default=False)
    field_option = models.CharField(max_length=32,
                                    choices=FIELD_OPTION_CHOICES,
                                    null=False,
                                    default=FIELD_OPTION_MIN_VALUE)
    description = models.TextField(null=True)
    min_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        default=None,
        blank=True)
    max_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        default=None,
        blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True, default=None)

    @property
    def unit(self):
        return self.metric.unit if not self.metric.is_count else ''

    def is_min_val(self):
        return self.field_option == self.FIELD_OPTION_MIN_VALUE

    def is_max_val(self):
        return self.field_option == self.FIELD_OPTION_MAX_VALUE

    def is_max_timeout(self):
        return self.field_option == self.FIELD_OPTION_MAX_TIMEOUT

    @property
    def steps_calculated(self):
        min_, max_, steps = self.min_value, self.max_value, self.steps
        format = '{0:.3g}'
        if steps is not None and min_ is not None and max_ is not None:
            return [format.format(v) for v in NotificationCheck.get_steps(
                min_, max_, steps)]

    @property
    def is_enabled(self):
        return self.current_value is not None

    @property
    def current_value(self):
        try:
            m = self.metric_check
            if not m:
                return
            val = getattr(m, self.field_option)
            if isinstance(val, timedelta):
                val_ = val.total_seconds()
            else:
                val_ = val
            return {
                'class':
                    f'{val.__class__.__module__}.{val.__class__.__name__}',
                    'value': val_}
        except MetricNotificationCheck.DoesNotExist:
            return

    def get_fields(self):
        out = []
        fid_base = self.field_name
        min_, max_, steps = self.min_value, self.max_value, self.steps_calculated

        if steps is not None and min_ is not None and max_ is not None:
            field = forms.ChoiceField(
                choices=[(v, v,) for v in steps], required=False)
        else:
            fargs = {}
            if max_ is not None:
                fargs['max_value'] = max_
            if min_ is not None:
                fargs['min_value'] = min_
            field = forms.DecimalField(max_digits=20,
                                       decimal_places=4,
                                       required=False,
                                       **fargs)
        field.name = fid_base
        out.append(field)
        return out

    @property
    def field_name(self):
        return f'{self.metric.name}.{self.field_option}'

    def populate_min_max(self):
        notification = self.notification_check
        uthreshold = notification.get_user_threshold(self)
        self.min_value = uthreshold['min']
        self.max_value = uthreshold['max']
        self.steps = uthreshold['steps']
        try:
            self.metric_check
        except MetricNotificationCheck.DoesNotExist:
            try:
                mcheck = MetricNotificationCheck.objects\
                                                .filter(
                                                    notification_check=self.notification_check,
                                                    metric=self.metric,
                                                    **{f'{self.field_option}__isnull': False})\
                                                .get()
                if mcheck:
                    self.metric_check = mcheck
            except MetricNotificationCheck.DoesNotExist:
                pass

        self.save()


class MetricNotificationCheck(models.Model):
    notification_check = models.ForeignKey(
        NotificationCheck, related_name="checks", on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, related_name="checks", on_delete=models.CASCADE)
    service = models.ForeignKey(
        Service,
        related_name="checks",
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    resource = models.ForeignKey(MonitoredResource, null=True, blank=True, on_delete=models.CASCADE)
    label = models.ForeignKey(MetricLabel, null=True, blank=True, on_delete=models.CASCADE)
    event_type = models.ForeignKey(EventType, null=True, blank=True, on_delete=models.CASCADE)
    min_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        default=None,
        blank=True)
    max_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        default=None,
        blank=True)
    max_timeout = models.DurationField(null=True, blank=True,
                                       help_text=_(
                                           "Max timeout for given metric before error should be raised")
                                       )
    active = models.BooleanField(default=True, null=False, blank=False)

    definition = models.OneToOneField(
        NotificationMetricDefinition,
        null=True,
        related_name='metric_check',
        on_delete=models.CASCADE)

    def __str__(self):
        indicator = []
        if self.min_value is not None:
            indicator.append(f"value above {self.min_value}")
        if self.max_value is not None:
            indicator.append(f"value below {self.max_value}")
        if self.max_timeout is not None:
            indicator.append(
                f"value must be collected within {self.max_timeout}")
        indicator = ' and '.join(indicator)
        return f"MetricCheck({self.metric.name}@{(self.service.name if self.service else '')}: {indicator})"

    @property
    def field_option(self):
        field_option = None
        if self.min_value:
            field_option = 'min_value'
        elif self.max_value:
            field_option = 'max_value'
        elif self.max_timeout:
            field_option = 'max_timeout'

        if field_option is None:
            raise ValueError("Cannot establish field_option value")
        return field_option

    class MetricValueError(ValueError):

        def __init__(self, metric, check, message,
                     offending_value, threshold_value, description):
            self.metric = metric
            self.check = check
            self.message = message
            self.name = metric.service_metric.metric.name if hasattr(metric, 'service_metric') else str(metric)
            self.offending_value = offending_value
            self.threshold_value = threshold_value
            self.severity = check.notification_check.severity if hasattr(check, 'notification_check') else None
            self.check_url = check.notification_check.url if hasattr(check, 'notification_check') else None
            self.check_id = check.notification_check.id if hasattr(check, 'notification_check') else None
            self.spotted_at = datetime.utcnow().replace(tzinfo=pytz.utc)
            self.description = description
            self.valid_from = metric.valid_from if hasattr(metric, 'valid_from') else None
            self.valid_to = metric.valid_to if hasattr(metric, 'valid_to') else None

        def __str__(self):
            return f"MetricValueError({self.severity}: metric {self.metric} misses {self.check} check: {self.message})"

    def check_value(self, metric, valid_on):
        """
        Check specific metric if it's faulty or not.
        """
        v = metric.value_num
        m = metric.service_metric.metric
        metric_name = m.description or m.name
        unit_name = f' {m.unit}' if not m.is_count else ''
        had_check = False

        if self.definition:
            def_msg = self.definition.description
            msg_prefix = []
            if self.event_type:
                os = self.event_type
                if os.is_all or os.is_other:
                    msg_prefix.append(f"for {os.name} OWS")
                else:
                    msg_prefix.append(f"for {os.name} OWS")
            if self.service:
                msg_prefix.append(f"for {self.service.name} service")
            if self.resource:
                msg_prefix.append(
                    f"for {self.resource.name}[{self.resource.type}] resource")

            msg_prefix = ' '.join(msg_prefix)
            description_tmpl = (f"{msg_prefix} {metric_name} should be {{}} "
                                f"{{:0.0f}}{unit_name}, got {{:0.0f}}{unit_name} instead").strip()

            if v is not None and self.min_value is not None:
                had_check = True
                if float(v) < float(self.min_value):
                    msg = f"{def_msg} {int(self.min_value)} {unit_name}"
                    description = description_tmpl.format(
                        'at least', float(self.min_value), float(v))
                    raise self.MetricValueError(
                        metric, self, msg, v, self.min_value, description)
            if v is not None and self.max_value is not None:
                had_check = True
                if float(v) > float(self.max_value):
                    msg = f"{def_msg} {int(self.max_value)} {unit_name}"
                    description = description_tmpl.format(
                        'at most', float(self.max_value), float(v))
                    raise self.MetricValueError(
                        metric, self, msg, v, self.max_value, description)

            if self.max_timeout is not None:
                had_check = True

                # we have to check for now, because valid_on may be in the past,
                # metric may be at the valid_on point in time
                valid_on = datetime.utcnow().replace(tzinfo=pytz.utc)
                metric.valid_to = metric.valid_to.replace(tzinfo=pytz.utc)
                if (valid_on - metric.valid_to) > self.max_timeout:
                    total_seconds = self.max_timeout.total_seconds()
                    actual_seconds = (valid_on - metric.valid_to).total_seconds()
                    msg = f"{def_msg} {int(total_seconds)} seconds"
                    description = description_tmpl.format(
                        'recored at most ',
                        f'{total_seconds} seconds ago',
                        f'{actual_seconds} seconds')
                    raise self.MetricValueError(metric,
                                                self,
                                                msg,
                                                metric.valid_to,
                                                valid_on,
                                                description)
        if not had_check:
            raise self.MetricValueError(
                metric,
                self,
                "",
                None,
                None,
                f"Metric check {self} is not checking anything")

    def check_metric(self, for_timestamp=None):
        """
        """
        if not for_timestamp:
            for_timestamp = datetime.utcnow().replace(tzinfo=pytz.utc)
        qfilter = {'metric': self.metric}
        if self.service:
            qfilter['service'] = self.service
        if self.resource:
            qfilter['resource'] = self.resource
        if self.label:
            qfilter['label'] = self.label
        if self.event_type:
            qfilter['event_type'] = self.event_type
        if self.max_timeout is None:
            metrics = MetricValue.get_for(valid_on=for_timestamp, **qfilter)
        else:
            metrics = MetricValue.get_for(**qfilter)
        if not metrics:
            raise self.MetricValueError(
                self.metric,
                "",
                "",
                None,
                None,
                f"Cannot find metric values for {self.metric} on {for_timestamp}")
        for m in metrics:
            self.check_value(m, for_timestamp)
        return True


class BuiltIns:
    service_types = (ServiceType.TYPE_GEONODE, ServiceType.TYPE_GEOSERVER,)
    host_service_types = (ServiceType.TYPE_HOST_GN, ServiceType.TYPE_HOST_GS,)

    metrics_rate = ('response.time', 'response.size',)
    # metrics_count = ('request.count', 'request.method', 'request.

    geonode_metrics = (
        'request', 'request.count', 'request.users', 'request.ip', 'request.ua', 'request.path',
        'request.ua.family', 'request.method', 'response.error.count',
        'request.country', 'request.region', 'request.city',
        'response.time', 'response.status', 'response.size',
        'response.error.types',)
    host_metrics = ('load.1m', 'load.5m', 'load.15m',
                    'mem.free', 'mem.usage', 'mem.usage.percent', 'mem.buffers', 'mem.all',
                    'uptime', 'cpu.usage', 'cpu.usage.rate', 'cpu.usage.percent',
                    'storage.free', 'storage.total', 'storage.used',
                    # mountpoint is the label
                    'network.in', 'network.out', 'network.in.rate', 'network.out.rate',)

    rates = (
        'response.time', 'response.size', 'network.in.rate', 'network.out.rate', 'load.1m', 'load.5m',
        'load.15m', 'cpu.usage.rate', 'cpu.usage.percent', 'cpu.usage', 'mem.usage.percent',
        'storage.free', 'storage.total', 'storage.used',)

    values = ('request.ip', 'request.ua', 'request.ua.family', 'request.path',
              'request.method', 'request.country', 'request.region',
              'request.city', 'response.status', 'response.ereror.types', 'request.users',)

    values_numeric = (
        'storage.total', 'storage.used', 'storage.free', 'mem.free', 'mem.usage',
        'mem.buffers', 'mem.all',)
    counters = (
        'request.count',
        'network.in',
        'network.out',
        'response.error.count',
        'uptime',
    )

    unit_seconds = ('response.time', 'uptime', 'cpu.usage',)
    unit_bytes = ('response.size', 'network.in', 'network.out',
                  'mem.free', 'mem.usage', 'mem.buffers', 'mem.all',)
    unit_bps = ('network.in.rate', 'network.out.rate',)
    unit_rate = ('cpu.usage.rate', 'load.1m', 'load.5m', 'load.15m',)
    unit_percentage = ('cpu.usage.percent', 'mem.usage.percent',)

    descriptions = {'request.count': 'Number of requests',
                    'request.users': 'Number of users visiting',
                    'response.time': 'Time of making a response',
                    'request.ip': 'IP Address of source of request',
                    'request.ua': 'User Agent of source of request',
                    'request.path': 'Request URL',
                    'network.in.rate': 'Network incoming traffic rate',
                    'network.out.rate': 'Network outgoing traffic rate',
                    'network.out': 'Network outgoing traffic bytes',
                    'network.in': 'Network incoming traffic bytes',
                    }


def populate():
    for m in BuiltIns.geonode_metrics + BuiltIns.host_metrics:
        Metric.objects.get_or_create(name=m)
    for st in BuiltIns.service_types + BuiltIns.host_service_types:
        ServiceType.objects.get_or_create(name=st)

    for st in BuiltIns.service_types:
        for m in BuiltIns.geonode_metrics:
            _st = ServiceType.objects.get(name=st)
            _m = Metric.objects.get(name=m)
            ServiceTypeMetric.objects.get_or_create(
                service_type=_st, metric=_m)
    for st in BuiltIns.host_service_types:
        for m in BuiltIns.host_metrics:
            _st = ServiceType.objects.get(name=st)
            _m = Metric.objects.get(name=m)
            ServiceTypeMetric.objects.get_or_create(
                service_type=_st, metric=_m)
    Metric.objects.filter(
        name__in=BuiltIns.counters).update(
        type=Metric.TYPE_COUNT)
    Metric.objects.filter(
        name__in=BuiltIns.rates).update(
        type=Metric.TYPE_RATE)
    Metric.objects.filter(
        name__in=BuiltIns.values).update(
        type=Metric.TYPE_VALUE)
    Metric.objects.filter(
        name__in=BuiltIns.values_numeric).update(
        type=Metric.TYPE_VALUE_NUMERIC)

    for etype, etype_name in EventType.EVENT_TYPES:
        EventType.objects.get_or_create(name=etype)

    for attr_name in dir(BuiltIns):
        if not attr_name.startswith('unit_'):
            continue
        val = getattr(BuiltIns, attr_name)
        uname = getattr(Metric, attr_name.upper())
        for mname in val:
            m = Metric.objects.get(name=mname)
            m.unit = uname
            m.save()
    Metric.objects.filter(unit__isnull=True).update(unit=Metric.UNIT_COUNT)
    for m, d in BuiltIns.descriptions.items():
        metric = Metric.objects.get(name=m)
        metric.description = d
        metric.save()

    if not Service.objects.all():
        do_autoconfigure()


def do_autoconfigure():
    """
    Create configuration from geonode's settings:
     * extract all hosts
     * create geonode instances
      * create host-geonode instances (favor this instead of geoserver)

     * create geoserver instances
      * create host-geoserver instances if needed
    """
    # get list of services
    wsite = urlparse(settings.SITEURL)
    # default host
    try:
        _host_by_name = gethostbyname(wsite.hostname)
    except Exception:
        _host_by_name = '127.0.0.1'
    hosts = [(wsite.hostname, _host_by_name,)]
    # default geonode
    geonode_name = settings.MONITORING_SERVICE_NAME or f'{wsite.hostname}-geonode'
    geonodes = [(geonode_name, settings.SITEURL, hosts[0])]

    geoservers = []
    for k, val in settings.OGC_SERVER.items():
        if val.get('BACKEND') == 'geonode.geoserver':
            gname = f'{k}-geoserver'
            gsite = urlparse(val['LOCATION'])
            try:
                _host_by_name = gethostbyname(gsite.hostname)
            except Exception:
                _host_by_name = '127.0.0.1'
            ghost = (gsite.hostname, _host_by_name,)
            if ghost not in hosts:
                hosts.append(ghost)
            geoservers.append((gname, val['LOCATION'], ghost,))

    hosts_map = {}
    for host in hosts:
        try:
            h = Host.objects.get(name=host[0])
            # if h.ip != host[1]:
            #     log.warning("Different ip. got", h.ip, "instead of", host[1])
        except Host.DoesNotExist:
            h = Host.objects.create(name=host[0], ip=host[1])
        hosts_map[h.name] = h

    geonode_type = ServiceType.objects.get(name=ServiceType.TYPE_GEONODE)
    geoserver_type = ServiceType.objects.get(name=ServiceType.TYPE_GEOSERVER)

    hostgeonode_type = ServiceType.objects.get(name=ServiceType.TYPE_HOST_GN)
    hostgeoserver_type = ServiceType.objects.get(name=ServiceType.TYPE_HOST_GS)

    for geonode in geonodes:
        host_name = geonode[2][0]
        host_ip = geonode[2][1]
        host = hosts_map.get(host_name) or Host.objects.create(
            name=host_name, ip=host_ip)
        host.save()

        try:
            service = Service.objects.get(name=geonode[0])
        except Service.DoesNotExist:
            service = Service.objects.create(
                name=geonode[0],
                url=geonode[1],
                host=host,
                service_type=geonode_type)
        service.save()

        shost_name = f'{host.name}-hostgeonode'
        try:
            service = Service.objects.get(name=shost_name)
        except Service.DoesNotExist:
            service = Service.objects.create(
                host=host,
                service_type=hostgeonode_type,
                url=geonode[1],
                name=shost_name)
        service.save()

    for geoserver in geoservers:
        host_name = geoserver[2][0]
        host_ip = geoserver[2][1]
        host = hosts_map.get(host_name) or Host.objects.create(
            name=host_name, ip=host_ip)
        host.save()

        try:
            service = Service.objects.get(name=geoserver[0])
        except Service.DoesNotExist:
            service = Service.objects.create(
                name=geoserver[0],
                url=geoserver[1],
                host=host,
                service_type=geoserver_type)
        service.save()

        shost_name = f'{host.name}-hostgeoserver'
        try:
            service = Service.objects.get(name=shost_name)
        except Service.DoesNotExist:
            service = Service.objects.create(
                host=host,
                service_type=hostgeoserver_type,
                url=geoserver[1],
                name=shost_name)
        service.save()

    do_reload()


def do_reload():
    """
    This will reload uwsgi if it's available
    """
    try:
        import uwsgi
        uwsgi.reload()
        return
    except ImportError:
        pass
