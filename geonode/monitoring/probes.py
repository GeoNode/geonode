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

import psutil


class BaseProbe:
    @staticmethod
    def get_loadavg():
        try:
            return os.getloadavg()
        except (
            AttributeError,
            OSError,
        ):
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
            return val

        return {
            "all": m(vm.total),
            # 'usage': m(vm.used),
            "used": m(vm.used),
            "free": m(vm.available),
            "usage": vm.used,
            "usage.percent": ((vm.used * 100.0) / vm.total),
        }

    @staticmethod
    def get_cpu():
        cpu = psutil.cpu_times()
        return {"usage": cpu.user + cpu.system, "usage.percent": psutil.cpu_percent()}

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
            dev_name = dev.split("/")[-1]
            part = p.mountpoint
            du = psutil.disk_usage(part)
            _dusage = usage.get(dev_name)
            dusage = {"write": 0, "read": 0}
            if _dusage:
                dusage["write"] = _dusage.write_bytes
                dusage["read"] = _dusage.read_bytes

            out.append(
                {
                    "device": dev,
                    "total": du.total,
                    "used": du.used,
                    "free": du.free,
                    "percent": du.percent,
                    "usage": dusage,
                    "mountpoint": part,
                }
            )
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
        for ifname, ifdata in psutil.net_if_addrs().items():
            ifstats = iostats.get(ifname)
            if not ifstats:
                continue
            mac = None
            if len(ifdata) == 2:
                mac = ifdata[1].address
            ip = ifdata[0].address

            out[ifname] = {"ip": ip, "mac": mac, "traffic": {"in": ifstats.bytes_recv, "out": ifstats.bytes_sent}}
        return out


def get_probe():
    return BaseProbe()
