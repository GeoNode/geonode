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
import logging
from datetime import datetime

from pydash import services as pydash
from geonode.contrib.monitoring.utils import GeoServerMonitorClient
from geonode.contrib.monitoring.models import RequestEvent

log = logging.getLogger(__name__)


def get_mem():
    """
    Get memory usage
    """
    try:
        pipe = os.popen(
            "free -tm | " + "tail -n 3 | head -n 1 | " + "awk '{print $2,$4,$6,$7}'")
        data = pipe.read().strip().split()
        pipe.close()
        allmem = int(data[0])
        freemem = int(data[1])
        buffers = int(data[2])
        # Memory in buffers + cached is actually available, so we count it
        # as free. See http://www.linuxatemyram.com/ for details
        freemem += buffers
        percent = (100 - ((freemem * 100) / allmem))
        usage = (allmem - freemem)

        mem_usage = {'all': allmem,
                     'usage': usage,
                     'buffers': buffers,
                     'free': freemem,
                     'percent': percent}
        data = mem_usage

    except Exception as err:
        data = str(err)
    return data


def get_disk():
    """
    Get disk usage
    """
    try:
        pipe = os.popen(
            "df -Ph | tail -n +2 | awk '{print $1, $2, $3, $4, $5, $6}'")
        data = pipe.read().strip().split('\n')
        pipe.close()

        data = [i.split(None, 6) for i in data]

    except Exception as err:
        data = str(err)

    return data


class BaseServiceExpose(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def setup(self):
        pass

    def expose(self):
        raise NotImplemented

    @classmethod
    def get_name(cls):
        n = cls.__name__
        return n[:len('serviceexpose')].lower()


class HostGeoNodeServiceExpose(BaseServiceExpose):

    def expose(self, *args, **kwargs):
        uptime = pydash.get_uptime()
        ips = pydash.get_ipaddress()
        df = get_disk()
        io = pydash.get_disk_rw()
        cpu = pydash.get_cpu_usage()
        try:
            load = os.getloadavg()
        except (AttributeError, OSError,):
            load = []
        mem = get_mem()

        data = {'uptime': uptime,
                'network': [],
                'disks': {'df': df,
                          'io': io},
                'cpu': {'usage': cpu,
                        'load': load},
                'memory': mem}
        for ipidx, ip in enumerate(ips['interface']):
            data['network'].append({'ip': ips['itfip'][ipidx][2],
                                    'mac': ips['itfip'][ipidx][1],
                                    'name': ip,
                                    'traffic': pydash.get_traffic(ip)})
        return data


class GeoNodeServiceExpose(BaseServiceExpose):

    def expose(self, *args, **kwargs):
        pass


class BaseServiceHandler(object):

    def __init__(self, service, force_check=False):
        self.service = service
        self.check_since = service.last_check
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
        now = datetime.now()

        if since is None:
            since = self.service.last_check
        if until is None:
            until = now
        if self.service.last_check and not self.force_check:
            if self.service.last_check + self.service.check_interval > now:
                log.warning("Next check too soon")
                return
        self.service.last_check = now
        self.service.save()
        _collected = self._collect(since, until, **kwargs)
        return self.handle_collected(_collected)

    def _collect(self, since, until):
        raise NotImplemented()

    def handle_collected(self):
        raise NotImplemented()

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

    def _collect(self):
        pass


services = dict((c.get_name(), c,) for c in (GeoNodeService, GeoServerService,))


def get_for_service(sname):
    return services[sname]
