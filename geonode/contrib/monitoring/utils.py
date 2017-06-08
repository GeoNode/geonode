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
import types
import re
from datetime import date, datetime, timedelta
from math import floor

from xml.etree import ElementTree as etree
from bs4 import BeautifulSoup as bs
import requests

from geonode.contrib.monitoring.models import RequestEvent, ExceptionEvent


class MonitoringFilter(logging.Filter):
    def __init__(self, service, skip_urls = tuple, *args, **kwargs):
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
                return skip_url.match(fp)
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


def align_period_start(start, interval):
    day_start = datetime(*start.date().timetuple()[:6])
    # timedelta
    diff = (start - day_start)
    # seconds
    diff_s = diff.total_seconds()
    int_s = interval.total_seconds()
    # rounding to last lower full period
    interval_num = floor(diff_s / float(int_s))

    return day_start + timedelta(seconds=(interval_num * interval.total_seconds()))


def generate_periods(since, interval, end=None):
    """
    Generator of periods: tuple of [start, end). 
    since parameter will be aligned to closest interval before since.
    """
    end = end or datetime.now()
    since_aligned = align_period_start(since, interval)
    while since_aligned < end:
        yield (since_aligned, since_aligned + interval,)
        since_aligned = since_aligned + interval
