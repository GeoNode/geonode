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

from datetime import datetime
from django.conf import settings
from geonode.contrib.monitoring.models import Service, Host
from geonode.contrib.monitoring.utils import MonitoringHandler, MonitoringFilter
from django.http import HttpResponse


FILTER_URLS = (settings.MEDIA_URL, settings.STATIC_URL, '/admin/jsi18n/',)


class MonitoringMiddleware(object):

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        self.log = logging.getLogger('{}.catcher'.format(__name__))
        self.log.propagate = False
        self.log.setLevel(logging.DEBUG)
        self.log.handlers = []
        self.service = self.get_service()
        self.handler = MonitoringHandler(self.service)
        self.handler.setLevel(logging.DEBUG)
        self.filter = MonitoringFilter(self.service, FILTER_URLS)
        self.handler.addFilter(self.filter)
        self.log.addHandler(self.handler)

    def get_service(self):
        hname = getattr(settings, 'MONITORING_HOST_NAME', None) or 'localhost'
        sname = getattr(settings, 'MONITORING_SERVICE_NAME', None) or 'geonode'
        try:
            host = Host.objects.get(name=hname)
        except Host.DoesNotExist:
            host = None
        if host:
            try:
                service = Service.objects.get(host=host, name=sname)
                return service
            except Service.DoesNotExist:
                service = None

    @staticmethod
    def add_resource(request, resource_type, name):
        m = getattr(request, '_monitoring', None)
        if not m:
            return
        res = m['resources']
        res_list = res.get(resource_type) or []
        res_list.append(name)
        res[resource_type] = res_list

    def register_request(self, request, response):
        if self.service:
            self.log.info('request', extra={'request': request, 'response': response})

    def register_exception(self, request, exception):
        if self.service:
            response = HttpResponse('')
            self.log.info('request', exc_info=exception, extra={'request': request, 'response': response})

    def process_view(self, request, view_func, view_args, view_kwargs):
        m = request.resolver_match
        if m.namespace in ('admin', 'monitoring',):
            request._monitoring = None
            del request._monitoring

    def process_request(self, request):
        now = datetime.now()
        meta = {'started': now,
                'resources': {},
                'finished': None}
        request._monitoring = meta

        def add_resource(resource_type, name):
            return self.add_resource(request, resource_type, name)

        request.add_resource = add_resource

    def process_response(self, request, response):
        m = getattr(request, '_monitoring', None)
        if m is None:
            return response
        now = datetime.now()
        m['finished'] = now
        self.register_request(request, response)
        return response

    def process_exception(self, request, exception):
        m = getattr(request, '_monitoring', None)
        if m is None:
            return
        now = datetime.now()
        m['finished'] = now
        self.register_exception(request, exception)
