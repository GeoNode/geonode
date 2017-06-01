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

import time
import threading
import traceback
import Queue
import logging

from geonode.contrib.monitoring.models import RequestEvent, ExceptionEvent

class MonitoringHandler(logging.Handler):

    def __init__(self, service, *args, **kwargs):
        super(MonitoringHandler, self).__init__(*args, **kwargs)
        self.service = service

    def emit(self, record):
        exc_info = record.exc_info
        req = record.request
        resp = record.response
        if not req._monitoring.get('processed'):
            re = RequestEvent.from_geonode(self.service, req, resp)
            req._monitoring['processed'] = re
        re = req._monitoring.get('processed')

        if exc_info:
            tb = traceback.format_exception(*exc_info)
            ExceptionEvent.add_error(self.service, exc_info[1], tb, request=re)


class RequestToMonitoringThread(threading.Thread):
    q = Queue.Queue()

    def __init__(self, service, *args, **kwargs):
        super(RequestToMonitoring, self).__init__(*args, **kwargs)
        self.service = service

    def add(self, req, resp):
        item = (req, resp,)
        RequestToMonitoring.q.put(item)

    def run(self):
        q = RequestToMonitoring.q
        while True:
            if not q.empty():
                item = q.get()
                req, resp = item
                re = RequestEvent.from_geonode(self.service, req, resp)
