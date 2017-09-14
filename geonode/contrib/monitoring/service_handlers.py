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

import requests
from geonode.contrib.monitoring.utils import GeoServerMonitorClient
from geonode.contrib.monitoring.probes import get_probe
from geonode.contrib.monitoring.models import RequestEvent, ExceptionEvent

log = logging.getLogger(__name__)


class BaseServiceExpose(object):
    NAME = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def setup(self):
        pass

    def expose(self):
        raise NotImplemented

    @classmethod
    def get_name(cls):
        if cls.NAME:
            return cls.NAME
        n = cls.__name__
        return n[:len('serviceexpose')].lower()


class HostGeoNodeServiceExpose(BaseServiceExpose):

    NAME = 'hostgeonode'

    def expose(self, *args, **kwargs):
        probe = get_probe()
        uptime = probe.get_uptime()
        disks = probe.get_disk()
        load = probe.get_loadavg()
        mem = probe.get_mem()
        uname = probe.get_uname()
        cpu = probe.get_cpu()
        network = probe.get_network()
        data = {'uptime': uptime,
                'uname': uname,
                'load': load,
                'cpu': cpu,
                'disks': disks,
                'network': network,
                'memory': mem}
        return data


class GeoNodeServiceExpose(BaseServiceExpose):

    NAME = 'geonode'

    def expose(self, *args, **kwargs):
        data = {}
        exceptions = []
        since = datetime.now() - timedelta(minutes=10)
        for e in ExceptionEvent.objects.filter(created__gte=since, service__service_type__name=self.NAME):
            exceptions.append(e.expose())
        data['exceptions'] = exceptions
        return data


class BaseServiceHandler(object):

    def __init__(self, service, force_check=False):
        self.service = service
        self.check_since = service.last_check
        self.now = datetime.now()
        self.force_check = force_check
        self.setup()

    def setup(self):
        pass

    def get_last_request(self):
        s = self.service
        return RequestEvent.objects.filter(service=s).order_by('-created').first()

    def get_last_request_timestamp(self):
        r = self.get_last_request()
        if r:
            return r.created

    def collect(self, since=None, until=None, **kwargs):
        now = self.now

        if since is None:
            since = self.service.last_check
        if until is None:
            until = now
        if self.service.last_check and not self.force_check:
            if self.service.last_check + self.service.check_interval > now:
                log.warning("Next check too soon")
                return
        _collected = self._collect(since, until, **kwargs)
        return self.handle_collected(_collected)

    def _collect(self, since, until, *args, **kwargs):
        raise NotImplemented()

    def handle_collected(self):
        raise NotImplemented()

    def mark_as_checked(self):
        self.service.last_check = self.now
        self.service.save()

    @classmethod
    def get_name(cls):
        n = cls.__name__
        return n[:-len('service')].lower()


class GeoNodeService(BaseServiceHandler):

    def _get_collected_set(self, since=None, until=None):
        filter_kwargs = {'service': self.service}
        if since:
            filter_kwargs = {'created__gt': since}
        return RequestEvent.objects.filter(**filter_kwargs)

    def _collect(self, since=None, until=None, **kwargs):
        return self._get_collected_set(since=since, until=until)

    def handle_collected(self, requests, *args, **kwargs):
        return requests


class GeoServerService(BaseServiceHandler):

    def setup(self):
        if not self.service.url:
            raise ValueError("Monitoring is not configured to fetch from %s" % self.service.name)
        self.gs_monitor = GeoServerMonitorClient(self.service.url)

    def _collect(self, since, until, format=None, **kwargs):
        format = format or 'json'
        requests = list(self.gs_monitor.get_requests(format=format, since=since, until=until))
        return requests

    def handle_collected(self, requests):
        now = datetime.now()
        for r in requests:
            RequestEvent.from_geoserver(self.service, r, received=now)
        return RequestEvent.objects.filter(service=self.service, received=now)


class HostGeoServerService(BaseServiceHandler):

    PATH = '/rest/about/monitoring.json'

    def _collect(self, *args, **kwargs):
        base_url = self.service.url
        if not base_url:
            raise ValueError("Service {} should have url provided".format(self.service.name))

        url = '{}{}'.format(base_url.rstrip('/'), self.PATH)

        rdata = requests.get(url)
        if rdata.status_code != 200:
            raise ValueError("Error response from api: ({}) {}".format(url, rdata))
        data = rdata.json()['metrics']['metric']
        return data

    def handle_collected(self, data, *args, **kwargs):

        return data


class HostGeoNodeService(BaseServiceHandler):

    def _collect(self, since, until, *args, **kwargs):
        base_url = self.service.url
        if not base_url:
            raise ValueError("Service {} should have url provided".format(self.service.name))
        url = '{}/monitoring/api/beacon/{}/'.format(base_url.rstrip('/'), self.service.service_type.name)
        rdata = requests.get(url)
        if rdata.status_code != 200:
            raise ValueError("Error response from api: ({}) {}".format(url, rdata))
        data = rdata.json()
        return data

    def handle_collected(self, data, *args, **kwargs):

        return data


services = dict(
    (c.get_name(), c,)
    for c in (
            GeoNodeService,
            GeoServerService,
            HostGeoNodeService,
            HostGeoServerService,))


def get_for_service(sname):
    return services[sname]


exposes = dict((c.get_name(), c) for c in (GeoNodeServiceExpose, HostGeoNodeServiceExpose,))


def exposes_for_service(sname):
    return exposes[sname]
