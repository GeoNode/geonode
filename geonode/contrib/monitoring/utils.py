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
import time
import threading
import traceback
import Queue
import logging

from xml.etree import ElementTree as etree
from bs4 import BeautifulSoup as bs
import requests

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

    def get_requests(self, format=None):
        """
        Returns list of requests from monitoring
        """
        rest_url = '{}rest/monitor/requests/'.format(self.base_url)
        resp = requests.get(rest_url)
        doc = bs(resp.content)
        links = doc.find_all('a')
        for l in links:
            if l.get('href').startswith(self.base_url):
                href = self.get_href(l, format)
                yield self.get_request(href) 

    def get_request(self, href):
        r = requests.get(href)
        try:
            return r.json()
        except ValueError, TypeError:
            try:
                return etree.fromstring(r.content)
            except Exception:
                return bs(r.content)
