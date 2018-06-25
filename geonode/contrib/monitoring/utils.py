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

import os
import pytz
import threading
import traceback
import Queue
import logging
import xmljson
import types
import re
from urllib import urlencode
from datetime import datetime, timedelta
from math import floor, ceil

from xml.etree import ElementTree as etree
from bs4 import BeautifulSoup as bs
from requests.auth import HTTPBasicAuth
import requests

from django.conf import settings
from django.db.models.fields.related import RelatedField

from geonode.contrib.monitoring.models import RequestEvent, ExceptionEvent


GS_FORMAT = '%Y-%m-%dT%H:%M:%S'  # 2010-06-20T2:00:00

log = logging.getLogger(__name__)


class MonitoringFilter(logging.Filter):
    def __init__(self, service, skip_urls=tuple(), *args, **kwargs):
        super(MonitoringFilter, self).__init__(*args, **kwargs)
        self.service = service
        self.skip_urls = skip_urls

    def filter(self, record):
        fp = record.request.get_full_path()
        for skip_url in self.skip_urls:
            if isinstance(skip_url, types.StringTypes):
                if fp.startswith(skip_url):
                    return False
            elif isinstance(skip_url, re.RegexObject):
                if skip_url.match(fp):
                    return False
        return record


class MonitoringHandler(logging.Handler):

    def __init__(self, service, *args, **kwargs):
        super(MonitoringHandler, self).__init__(*args, **kwargs)
        self.service = service

    def emit(self, record):
        exc_info = record.exc_info
        req = record.request
        resp = record.response
        if not req._monitoring.get('processed'):
            try:
                re = RequestEvent.from_geonode(self.service, req, resp)
                req._monitoring['processed'] = re
            except BaseException:
                req._monitoring['processed'] = None
        re = req._monitoring.get('processed')

        if re and exc_info:
            tb = traceback.format_exception(*exc_info)
            ExceptionEvent.add_error(self.service, exc_info[1], tb, request=re)


class RequestToMonitoringThread(threading.Thread):
    q = Queue.Queue()

    def __init__(self, service, *args, **kwargs):
        super(RequestToMonitoringThread, self).__init__(*args, **kwargs)
        self.service = service

    def add(self, req, resp):
        item = (req, resp,)
        RequestToMonitoringThread.q.put(item)

    def run(self):
        q = RequestToMonitoringThread.q
        while True:
            if not q.empty():
                item = q.get()
                req, resp = item
                RequestEvent.from_geonode(self.service, req, resp)


class GeoServerMonitorClient(object):

    REPORT_FORMATS = ('html', 'xml', 'json',)

    def __init__(self, base_url):
        self.base_url = base_url

    def get_href(self, link, format=None):
        href = link['href']
        if format is None:
            return href
        if format in self.REPORT_FORMATS:
            href, ext = os.path.splitext(href)
            return '{}.{}'.format(href, format)
        return format

    def get_requests(self, format=None, since=None, until=None):
        """
        Returns list of requests from monitoring
        """
        rest_url = '{}rest/monitor/requests.html'.format(self.base_url)
        qargs = {}
        if since:
            # since = since.astimezone(utc)
            qargs['from'] = since.strftime(GS_FORMAT)
        if until:
            # until = until.astimezone(utc)
            qargs['to'] = until.strftime(GS_FORMAT)
        if qargs:
            rest_url = '{}?{}'.format(rest_url, urlencode(qargs))

        print('checking', rest_url)
        username = settings.OGC_SERVER['default']['USER']
        password = settings.OGC_SERVER['default']['PASSWORD']
        resp = requests.get(rest_url, auth=HTTPBasicAuth(username, password))
        doc = bs(resp.content)
        links = doc.find_all('a')
        for l in links:
            # we're skipping this check, as gs can generate
            # url with other base url
            # if l.get('href').startswith(self.base_url):
            href = self.get_href(l, format)
            data = self.get_request(href, format=format)
            if data:
                yield data
            else:
                print("Skipping payload for {}".format(href))

    def get_request(self, href, format=format):
        username = settings.OGC_SERVER['default']['USER']
        password = settings.OGC_SERVER['default']['PASSWORD']
        r = requests.get(href, auth=HTTPBasicAuth(username, password))
        if r.status_code != 200:
            log.warning('Invalid response for %s: %s', href, r)
            return
        data = None
        try:
            data = r.json()
        except (ValueError, TypeError,):
            # traceback.print_exc()
            try:
                data = etree.fromstring(r.content)
            except Exception as err:
                log.debug("Cannot parse xml contents for %s: %s", href, err, exc_info=err)
                data = bs(r.content)
        if data and format != 'json':
            return self.to_json(data, format)
        return data

    def _from_xml(self, val):
        try:
            return xmljson.yahoo.data(val)
        except BaseException:
            # raise ValueError("Cannot convert from val %s" % val)
            pass

    def _from_html(self, val):
        raise ValueError("Cannot convert from html")

    def to_json(self, data, from_format):
        h = getattr(self, '_from_{}'.format(from_format), None)
        if not h or not data:
            raise ValueError(
                "Cannot convert from {} - no handler".format(from_format))
        return h(data)


def align_period_end(end, interval):
    utc = pytz.utc
    day_end = datetime(*end.date().timetuple()[:6]).replace(tzinfo=utc)
    # timedelta
    diff = (end - day_end)
    # seconds
    diff_s = diff.total_seconds()
    int_s = interval.total_seconds()
    # rounding to last lower full period
    interval_num = ceil(diff_s / float(int_s))

    return day_end + \
        timedelta(seconds=(interval_num * interval.total_seconds()))


def align_period_start(start, interval):
    utc = pytz.utc
    day_start = datetime(*start.date().timetuple()[:6]).replace(tzinfo=utc)
    # timedelta
    diff = (start.replace(tzinfo=utc) - day_start)
    # seconds
    diff_s = diff.total_seconds()
    int_s = interval.total_seconds()
    # rounding to last lower full period
    interval_num = floor(diff_s / float(int_s))

    return day_start + \
        timedelta(seconds=(interval_num * interval.total_seconds()))


def generate_periods(since, interval, end=None, align=True):
    """
    Generator of periods: tuple of [start, end).
    since parameter will be aligned to closest interval before since.1
    """
    utc = pytz.utc
    end = end or datetime.utcnow().replace(tzinfo=utc)
    if align:
        since_aligned = align_period_start(since, interval)
    else:
        since_aligned = since

    full_interval = (end - since).total_seconds()
    _periods = divmod(full_interval, interval.total_seconds())
    periods_count = _periods[0]
    if _periods[1]:
        periods_count += 1

    end = since_aligned + \
        timedelta(seconds=(periods_count * interval.total_seconds()))

    while since_aligned < end:
        yield (since_aligned, since_aligned + interval,)
        since_aligned = since_aligned + interval


class TypeChecks(object):
    AUDIT_TYPE_JSON = 'json'
    AUDIT_TYPE_XML = 'xml'
    AUDIT_FORMATS = (AUDIT_TYPE_JSON, AUDIT_TYPE_XML,)

    @classmethod
    def audit_format(cls, val):
        if val not in cls.AUDIT_FORMATS:
            raise ValueError("Invalid value for audit format: {}".format(val))
        return val

    @staticmethod
    def host_type(val):
        from geonode.contrib.monitoring.models import Host
        try:
            return Host.objects.get(name=val)
        except Host.DoesNotExist:
            raise ValueError("Host {} does not exist".format(val))

    @staticmethod
    def resource_type(val):
        from geonode.contrib.monitoring.models import MonitoredResource
        try:
            val = int(val)
            return MonitoredResource.objects.get(id=val)
        except (ValueError, TypeError,):
            try:
                rtype, rname = val.split('=')
            except (ValueError, IndexError,):
                raise ValueError(
                    "{} is not valid resource description".format(val))
        return MonitoredResource.objects.get(type=rtype, name=rname)

    @staticmethod
    def resource_type_type(val):
        from geonode.contrib.monitoring.models import MonitoredResource
        if val in MonitoredResource._TYPES:
            return val
        raise ValueError("Invalid monitored resource type: {}".format(val))

    @staticmethod
    def metric_name_type(val):
        from geonode.contrib.monitoring.models import Metric
        try:
            return Metric.objects.get(name=val)
        except Metric.DoesNotExist:
            raise ValueError("Metric {} doesn't exist".format(val))

    @staticmethod
    def service_type(val):
        from geonode.contrib.monitoring.models import Service
        try:
            return Service.objects.get(name=val)
        except Service.DoesNotExist:
            raise ValueError("Service {} does not exist".format(val))

    @staticmethod
    def service_type_type(val):
        from geonode.contrib.monitoring.models import ServiceType
        try:
            return ServiceType.objects.get(name=val)
        except ServiceType.DoesNotExist:
            raise ValueError("Service Type {} does not exist".format(val))

    @staticmethod
    def label_type(val):
        from geonode.contrib.monitoring.models import MetricLabel
        try:
            return MetricLabel.objects.get(id=val)
        except (ValueError, TypeError, MetricLabel.DoesNotExist,):
            try:
                return MetricLabel.objects.get(name=val)
            except MetricLabel.DoesNotExist:
                pass
        raise ValueError("Invalid label value: {}".format(val))

    @staticmethod
    def ows_service_type(val):
        from geonode.contrib.monitoring.models import OWSService
        try:
            return OWSService.objects.get(name=val)
        except OWSService.DoesNotExist:
            raise ValueError("OWS Service {} doesn't exist".format(val))


def dump(obj, additional_fields=tuple()):
    if hasattr(obj, '_meta'):
        fields = obj._meta.fields
    else:
        fields = []
    out = {}
    for field in fields:
        fname = field.name
        val = getattr(obj, fname)
        if isinstance(field, RelatedField):
            if val is not None:
                v = val
                val = {'class': '{}.{}'.format(val.__class__.__module__, val.__class__.__name__),
                       'id': val.pk}
                if hasattr(v, 'name'):
                    val['name'] = v.name
        if isinstance(val, timedelta):
            val = {'class': 'datetime.timedelta',
                   'seconds': val.total_seconds()}
        out[fname] = val
    for fname in additional_fields:
        val = getattr(obj, fname, None)
        if isinstance(val, timedelta):
            val = {'class': 'datetime.timedelta',
                   'seconds': val.total_seconds()}
        out[fname] = val
    return out
