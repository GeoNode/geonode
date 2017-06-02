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
from __future__ import print_function
import logging
import argparse

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

from geonode.contrib.monitoring.models import Service
from geonode.contrib.monitoring.service_handlers import get_for_service

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Run collecting for monitoring
    """

    def add_arguments(self, parser):
        parser.add_argument('-l', '--list', dest='list_services', action='store_true', default=False,
                            help=_("Show list of services"))

    def handle(self, *args, **options):
        services = Service.objects.all()
        if options['list_services']:
            print('available services')
            for s in services:
                print('  ', s.name, '(', s.url, ')')
                print('   running on', s.host.name, s.host.ip)
                print('   active:', s.active)
                if s.last_check:
                    print('    last check:', s.last_check)
                else:
                    print('    not checked yet')
                print(' ')
            return
        for s in services:
            self.run_check(s)

    def run_check(self, service):
        print('checking', service.name)
        Handler = get_for_service(service.service_type.name)
        h = Handler(service)
        h.collect()
