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
import pytz
from datetime import datetime
from dateutil.tz import tzlocal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

from geonode.utils import parse_datetime
from geonode.contrib.monitoring.models import Service
from geonode.contrib.monitoring.service_handlers import get_for_service
from geonode.contrib.monitoring.collector import CollectorAPI
from geonode.contrib.monitoring.utils import TypeChecks

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Run collecting for monitoring
    """

    def add_arguments(self, parser):
        parser.add_argument('-l', '--list', dest='list_services', action='store_true', default=False,
                            help=_("Show list of services"))
        parser.add_argument('-s', '--since', dest='since', default=None, type=parse_datetime,
                            help=_("Process data since specific timestamp (YYYY-MM-DD HH:MM:SS format). "
                                   "If not provided, last sync will be used."))
        parser.add_argument('-u', '--until', dest='until', default=None, type=parse_datetime,
                            help=_("Process data until specific timestamp (YYYY-MM-DD HH:MM:SS format). "
                                   "If not provided, now will be used."))
        parser.add_argument('-f', '--force', dest='force_check', action='store_true', default=False,
                            help=_("Force check"))
        parser.add_argument('-t', '--format', default=TypeChecks.AUDIT_TYPE_JSON, type=TypeChecks.audit_format,
                            help=_("Format of audit log (xml, json)"))
        parser.add_argument('-k', '--do-not-clear', default=False, action='store_true', dest='do_not_clear',
                            help=_("Should old data be preserved (default: no, "
                                   "data older than settings.MONITORING_DATA_TTL will be removed)"))
        parser.add_argument('-e', '--halt', default=False, action='store_true', dest='halt_on_errors',
                            help=_("Should stop on first error occured (default: no)"))
        parser.add_argument('-n', '--emit_notifications', default=False, action='store_true', dest='emit_notifications',
                            help=_("Should process and send notifications as well (default: no)"))
        parser.add_argument('service', type=TypeChecks.service_type, nargs="?",
                            help=_("Collect data from this service only"))

    def handle(self, *args, **options):
        oservice = options['service']
        if not oservice:
            services = Service.objects.all()
        else:
            services = [oservice]
        if options['list_services']:
            print('available services')
            for s in services:
                print('  ', s.name, '(', s.url, ')')
                print('   type', s.service_type.name)
                print('   running on', s.host.name, s.host.ip)
                print('   active:', s.active)
                if s.last_check:
                    print('    last check:', s.last_check)
                else:
                    print('    not checked yet')
                print(' ')
            return
        c = CollectorAPI()
        for s in services:
            try:
                self.run_check(s, collector=c,
                               since=options['since'],
                               until=options['until'],
                               force_check=options['force_check'],
                               format=options['format'])
            except Exception, err:
                log.error("Cannot collect from %s: %s", s, err, exc_info=err)
                if options['halt_on_errors']:
                    raise
        if not options['do_not_clear']:
            log.info("Clearing old data")
            c.clear_old_data()
        if options['emit_notifications']:
            log.info("Processing notifications for %s", options['until'])
            s = Service.objects.first()
            interval = s.check_interval
            now = datetime.utcnow().replace(tzinfo=pytz.utc)
            notifications_check = now - interval
            c.emit_notifications() #notifications_check)

    def run_check(self, service, collector, since=None, until=None, force_check=None, format=None):
        utc = pytz.utc
        try:
            local_tz = pytz.timezone(datetime.now(tzlocal()).tzname())
        except:
            local_tz = pytz.timezone(settings.TIME_ZONE)
        now = datetime.utcnow().replace(tzinfo=utc)
        Handler = get_for_service(service.service_type.name)
        try:
            service.last_check = service.last_check.astimezone(utc)
        except:
            service.last_check = service.last_check.replace(tzinfo=utc) if service.last_check else now
        last_check = local_tz.localize(since).astimezone(utc).replace(tzinfo=utc) if since else service.last_check
        if not last_check or last_check > now:
            last_check = (now - service.check_interval)
            service.last_check = last_check

        if not until:
            until = now
        else:
            until = local_tz.localize(until).astimezone(utc).replace(tzinfo=utc)

        print('[',now ,'] checking', service.name, 'since', last_check, 'until', until)
        data_in = None
        h = Handler(service, force_check=force_check)
        data_in = h.collect(since=last_check, until=until, format=format)
        if data_in:
            try:
                return collector.process(service, data_in, last_check, until)
            finally:
                h.mark_as_checked()

