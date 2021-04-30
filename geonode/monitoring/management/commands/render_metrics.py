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

import pytz
import logging
import timeout_decorator

from datetime import timedelta
from six import string_types

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_noop as _

from geonode.utils import parse_datetime
from geonode.monitoring.collector import CollectorAPI
from geonode.monitoring.utils import TypeChecks

LOCAL_TIMEOUT = 8600

TIMESTAMP_OUTPUT = '%Y-%m-%d %H:%M:%S'

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Run collecting for monitoring
    """

    def add_arguments(self, parser):
        parser.add_argument('-m', '--list-metrics', dest='list_metrics', action='store_true', default=False,
                            help=_("Show list of metrics"))
        parser.add_argument('-l', '--list-labels', dest='list_labels', action='store_true', default=False,
                    help=_("Show list of labels for metric"))

        parser.add_argument('-r', '--list-resources', dest='list_resources', action='store_true', default=False,
                    help=_("Show list of resources for metric"))

        parser.add_argument('-s', '--since', dest='since', default=None, type=parse_datetime,
                            help=_("Process data since specific timestamp (YYYY-MM-DD HH:MM:SS format). If not provided, last sync will be used."))
        parser.add_argument('-u', '--until', dest='until', default=None, type=parse_datetime,
                            help=_("Process data until specific timestamp (YYYY-MM-DD HH:MM:SS format). If not provided, now will be used."))

        parser.add_argument('-i', '--interval', dest='interval', default=60, type=int,
                            help=_("Data aggregation interval in seconds (default: 60)"))
        parser.add_argument('metric_name', default=None, nargs="?", help=_("Metric name"))

        parser.add_argument('-rr', '--for-resource', dest='resource', type=TypeChecks.resource_type,
                            help=_("Show data for specific resource in resource_type=resource_name format"))

        parser.add_argument('-ss', '--service', dest='service', type=TypeChecks.service_type,
                            help=_("Show data for specific resource"))

        parser.add_argument('-ll', '--label', dest='label', type=TypeChecks.label_type,
                            help=_("Show data for specific label"))


    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def handle(self, *args, **options):
        self.collector = CollectorAPI()
        if options['list_metrics']:
            self.list_metrics()
            return

        interval = timedelta(seconds=options['interval'])
        metric_names = options['metric_name']
        resource = options['resource']
        # service = options['service']
        label = options['label']
        if not metric_names:
            raise CommandError("No metric name")
        if isinstance(metric_names, string_types):
            metric_names = [metric_names]
        for m in metric_names:
            #def get_metrics_for(self, metric_name, valid_from=None, valid_to=None, interval=None, service=None, label=None, resource=None):
            if options['list_labels']:
                self.list_labels(m)
            elif options['list_resources']:
                self.list_resources(m)
            else:
                self.show_metrics(m, options['since'], options['until'], interval, resource=resource, label=label)

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def list_labels(self, metric, resource=None):
        labels = self.collector.get_labels_for_metric(metric, resource=resource)
        print(f'Labels for metric {metric}')
        for label in labels:
            print(' ', *label)

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def list_resources(self, metric):
        resources = self.collector.get_resources_for_metric(metric)
        print(f'Resources for metric {metric}')
        for res in resources:
            print(' ', '='.join(res))

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def show_metrics(self, metric, since, until, interval, resource=None, label=None, service=None):
        print(f'Monitoring Metric values for {metric}')
        if service:
            print(f' for service: {service} ')
        if resource:
            print(f' for resource: {resource.type}={resource.name} ')
        if label:
            print(f' for label: {label.name} label')

        utc = pytz.utc
        since = since.replace(tzinfo=utc) if since else None
        until = until.replace(tzinfo=utc) if until else None

        data = self.collector.get_metrics_for(metric,
                                              valid_from=since,
                                              valid_to=until,
                                              interval=interval,
                                              resource=resource,
                                              label=label,
                                              service=service)
        print(' since {} until {}\n'.format(data['input_valid_from'].strftime(TIMESTAMP_OUTPUT),
                                          data['input_valid_to'].strftime(TIMESTAMP_OUTPUT)))

        for row in data['data']:
            val = None
            if row['data']:
                val = row['data'][0]['val']
            print(' ', row['valid_to'].strftime(TIMESTAMP_OUTPUT), '->', '' if not val else val)


    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def list_metrics(self):
        _metrics = self.collector.get_metric_names()
        for stype, metrics in _metrics:
            print('service type', stype.name)
            for m in metrics:
                print(f' {m.name}[{m.type}]')
