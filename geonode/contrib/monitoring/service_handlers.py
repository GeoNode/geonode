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

import requests
from pydash import services as pydash
from geonode.contrib.monitoring.utils import GeoServerMonitorClient

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
        return cls[:len('serviceexpose')].lower()

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
    
    def __init__(self, service):
        self.service = service
        self.setup()

    def setup(self):
        pass

    def collect(self):
        raise NotImplemented()

    @classmethod
    def get_name(cls):
        n = cls.__name__
        return n[:-len('service')].lower()

class GeoNodeService(BaseServiceHandler):

    def collect(self):
        return
     

class GeoServerService(BaseServiceHandler):

    def setup(self):
        if not self.service.url:
            raise ValueError("Monitoring is not configured to fetch from %s" % self.service.name)
        self.gs_monitor = GeoServerMonitorClient(self.service.url)

    def collect(self):
        requests = list(self.gs_monitor.get_requests(format='json'))
        return requests

class HostGeoServerService(BaseServiceHandler):
    
    def collect(self):
        pass


services = dict((c.get_name(), c,) for c in (GeoNodeService, GeoServerService,))

def get_for_service(sname):
    return services[sname]
