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
import sys
import time
import socket
import logging
from datetime import datetime, timedelta

import requests
import psutil

class PosixProbe(object):

    @staticmethod
    def get_uname():
        return os.uname()

    @staticmethod
    def get_uptime():
        """
        Get uptime
        """
        try:
            with open('/proc/uptime', 'r') as f:
                data = float(f.readline().split()[0])
        except Exception as err:
            data = str(err)

        return data

    @staticmethod
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

    @staticmethod
    def get_disk():
        """
        Get disk usage
        """
        try:
            pipe = os.popen(
                "df -P | tail -n +2 | awk '{print $1, $2, $3, $4, $5, $6}'")
            data = pipe.read().strip().split('\n')
            pipe.close()

            data = [i.split(None, 6) for i in data]

        except Exception as err:
            data = str(err)

        return data

    @staticmethod
    def get_ipaddress():
        return pydash.get_ipaddress()

    @staticmethod
    def get_disk_rw():
        return pydash.get_disk_rw()

    @staticmethod
    def get_cpu_usage():
        cpu = pydash.get_cpu_usage()

    @staticmethod
    def get_loadavg():
        return os.getloadavg()

    @staticmethod
    def get_traffic(ip):
        return pydash.get_traffic(ip)


class BaseProbe(object):

    @staticmethod
    def get_loadavg():
        try:
            return os.getloadavg()
        except (AttributeError, OSError,):
            return []

    @staticmethod
    def get_uname():
        """
        returns list similar to https://docs.python.org/2/library/os.html#os.uname
        """
        try:
            return os.uname()
        except Exception:
            return [sys.platform, socket.gethostbyaddr(socket.gethostname()), None, None, None]
    
    @staticmethod
    def get_uptime():
        """
        Get uptime in seconds
        """
        return time.time() - psutil.boot_time()

    @staticmethod
    def get_mem():
        """
        Returns dictionary with memory information (in MB) with keys:
            all
            usage
            buffers
            free
            percent
        """
        vm = psutil.virtual_memory()
        def m(val):
            return val/1024
        return {'all': m(vm.total),
                'usage': m(vm.used),
                #'buffers': 
                'free': m(vm.free),
                'percent': (vm.used/vm.total)/100
                }

    @staticmethod
    def get_disk():
        """
        Returns list of drives with capacity and utilization
        list item contains:
            block device (/dev/sXX)
            total capacity (in bytes)
            used space
            free space
            utilization (as a percent)
            mount point
        """
        partitions = psutil.disk_partitions()
        out = []
        usage = psutil.disk_io_counters(True)
        for p in partitions:
            dev = p.device
            dev_name = dev.split('/')[-1]
            part = p.mountpoint
            du = psutil.disk_usage(part)
            _dusage = usage.get(dev_name)
            dusage = {'write': 0, 
                      'read': 0}
            if _dusage:
                dusage['write'] = _dusage.write_bytes
                dusage['read'] = _dusage.read_bytes

            out.append({'device': dev, 
                        'total': du.total, 
                        'used': du.used, 
                        'free': du.free, 
                        'percent': du.percent, 
                        'usage': dusage,
                        'mountpoint': part})
        return out

    @staticmethod
    def get_network():
        """
        returns dictionary with ip information:
        {ifname: {'mac': mac,
                  'ip': ip,
                  'traffic': {'in': txin,
                              'out': txout}
                  }
        }
        """
        out = {}
        iostats = psutil.net_io_counters(True)
        for ifname, ifdata in psutil.net_if_addrs().iteritems():
            ifstats = iostats.get(ifname)
            if not ifstats:
                continue
            mac = None
            if len(ifdata) == 2:
                mac = ifdata[1].address
            ip = ifdata[0].address
            
            out[ifname] = {'ip': ip,
                           'mac': mac,
                           'traffic': {'in': ifstats.bytes_recv,
                                       'out': ifstats.bytes_sent}}
        return out


def get_probe():
    return BaseProbe()
