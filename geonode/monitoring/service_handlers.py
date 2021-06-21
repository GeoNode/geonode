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
import pytz
from datetime import datetime, timedelta

import requests
from geonode.monitoring.utils import GeoServerMonitorClient
from geonode.monitoring.probes import get_probe
from geonode.monitoring.models import RequestEvent, ExceptionEvent

log = logging.getLogger(__name__)


class BaseServiceExpose:

    NAME = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def setup(self):
        pass

    def expose(self):
        raise NotImplementedError

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
        utc = pytz.utc
        data = {}
        exceptions = []
        since = datetime.utcnow().replace(tzinfo=utc) - timedelta(minutes=10)
        for e in ExceptionEvent.objects.filter(created__gte=since, service__service_type__name=self.NAME):
            exceptions.append(e.expose())
        data['exceptions'] = exceptions
        return data


class BaseServiceHandler:

    def __init__(self, service, force_check=False):
        utc = pytz.utc
        self.service = service
        self.now = datetime.utcnow().replace(tzinfo=utc)
        self.check_since = service.last_check.astimezone(utc) if service.last_check else self.now
        self.force_check = force_check

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
        utc = pytz.utc
        now = self.now or datetime.utcnow().replace(tzinfo=utc)
        if since is None:
            since = self.service.last_check.astimezone(utc) if self.service.last_check else now
        if until is None:
            until = now
        if not self.service.last_check:
            self.service.last_check = self.now
            self.service.save()
        if self.service.last_check and not self.force_check:
            last_check = self.service.last_check.astimezone(utc) if self.service.last_check else now
            if last_check + self.service.check_interval > now:
                log.warning("Next check too soon")
                return
        _collected = self._collect(since.astimezone(utc), until.astimezone(utc), **kwargs)
        return self.handle_collected(_collected)

    def _collect(self, since, until, *args, **kwargs):
        raise NotImplementedError

    def handle_collected(self):
        raise NotImplementedError

    def mark_as_checked(self):
        self.service.last_check = self.now
        self.service.save()

    @classmethod
    def get_name(cls):
        n = cls.__name__
        return n[:-len('service')].lower()


class GeoNodeService(BaseServiceHandler):

    def __init__(self, service, force_check=False):
        BaseServiceHandler.__init__(self, service, force_check)

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

    def __init__(self, service, force_check=False):
        BaseServiceHandler.__init__(self, service, force_check)
        self.setup()

    def setup(self):
        if not self.service.url:
            raise ValueError(f"Monitoring is not configured to fetch from {self.service.name}")
        self.gs_monitor = GeoServerMonitorClient(self.service.url)

    def _collect(self, since, until, format=None, **kwargs):
        format = format or 'json'
        requests = list(self.gs_monitor.get_requests(format=format, since=since, until=until))
        return requests

    def handle_collected(self, requests):
        utc = pytz.utc
        now = datetime.utcnow().replace(tzinfo=utc)
        for r in requests:
            RequestEvent.from_geoserver(self.service, r, received=now)
        return RequestEvent.objects.filter(service=self.service, received=now)


class HostGeoServerService(BaseServiceHandler):

    PATH = '/rest/about/system-status.json'

    def __init__(self, service, force_check=False):
        BaseServiceHandler.__init__(self, service, force_check)

    def _collect(self, *args, **kwargs):
        base_url = self.service.url
        if not base_url:
            raise ValueError(f"Service {self.service.name} should have url provided")
        url = f"{base_url.rstrip('/')}{self.PATH}"
        rdata = requests.get(url, timeout=10, verify=False)
        if rdata.status_code != 200:
            raise ValueError(f"Error response from api: ({url}) {rdata}")
        data = rdata.json()['metrics']['metric']
        return data

    def handle_collected(self, data, *args, **kwargs):
        return data


class HostGeoNodeService(BaseServiceHandler):

    def __init__(self, service, force_check=False):
        BaseServiceHandler.__init__(self, service, force_check)

    def _collect(self, since, until, *args, **kwargs):
        base_url = self.service.url
        if not base_url:
            raise ValueError(f"Service {self.service.name} should have url provided")
        url = f"{base_url.rstrip('/')}/monitoring/api/beacon/{self.service.service_type.name}/"
        rdata = requests.get(url, timeout=10, verify=False)
        if rdata.status_code != 200:
            raise ValueError(f"Error response from api: ({url}) {rdata}")
        data = rdata.json()
        return data

    def handle_collected(self, data, *args, **kwargs):
        return data


services = {
    c.get_name(): c
    for c in (
        GeoNodeService,
        GeoServerService,
        HostGeoNodeService,
        HostGeoServerService,)}


def get_for_service(sname):
    return services[sname]


exposes = {c.get_name(): c for c in (GeoNodeServiceExpose, HostGeoNodeServiceExpose,)}


def exposes_for_service(sname):
    return exposes[sname]
