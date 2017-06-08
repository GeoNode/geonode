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
import types
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_noop as _

from geonode.utils import parse_datetime
from geonode.contrib.monitoring.models import Service
from geonode.contrib.monitoring.service_handlers import get_for_service
from geonode.contrib.monitoring.collector import CollectorAPI

log = logging.getLogger(__name__)

TIMESTAMP_OUTPUT = '%Y-%m-%d %H:%M:%S'
class Command(BaseCommand):
    """
    Run collecting for monitoring
    """

    def add_arguments(self, parser):
        parser.add_argument('-l', '--list-metrics', dest='list_metrics', action='store_true', default=False,
                            help=_("Show list of metrics"))
        parser.add_argument('-n', '--list-labels', dest='list_labels', action='store_true', default=False,
                    help=_("Show list of labels for metric"))

        parser.add_argument('-r', '--list-resources', dest='list_resources', action='store_true', default=False,
                    help=_("Show list of resources for metric"))

        parser.add_argument('-s', '--since', dest='since', default=None, type=parse_datetime,
                            help=_("Process data since specific timestamp (YYYY-MM-DD HH:MM:SS format). If not provided, last sync will be used."))
        parser.add_argument('-u', '--until', dest='until', default=None, type=parse_datetime,
                            help=_("Process data until specific timestamp (YYYY-MM-DD HH:MM:SS format). If not provided, now will be used."))

        parser.add_argument('metric_name', default=None, nargs="?", help=_("Metric name"))

    def handle(self, *args, **options):
        self.collector = CollectorAPI()
        if options['list_metrics']:
            self.list_metrics()

        metric_names = options['metric_name']
        if not metric_names:
            raise CommandError("No metric name")
        if isinstance(metric_names, types.StringTypes):
            metric_names = [metric_names]
        for m in metric_names:
            #def get_metrics_for(self, metric_name, valid_from=None, valid_to=None, interval=None, service=None, label=None, resource=None):
            if options['list_labels']:
                self.list_labels(m)
            elif options['list_resources']:
                self.list_resources(m)
            else:
                self.show_metrics(m, options['since'], options['until'])

    def list_labels(self, metric):
        labels = self.collector.get_labels_for_metric(metric)
        print('Labels for metric {}'.format(metric))
        for label in labels:
            print(' ', *label)

    def list_resources(self, metric):
        resources = self.collector.get_resources_for_metric(metric)
        print('Resources for metric {}'.format(metric))
        for res in resources:
            print(' ', *res)

    def show_metrics(self, metric, since, until):
        data = self.collector.get_metrics_for(metric, valid_from=since, valid_to=until)
        print('Monitoring Metric values for {}'.format(metric))
        print(' since {} until {}\n'.format(data['input_valid_from'].strftime(TIMESTAMP_OUTPUT),
                                          data['input_valid_to'].strftime(TIMESTAMP_OUTPUT)))

        for row in data['data']:
            val = row['data'][0]['val']
            print(' ', row['valid_to'].strftime(TIMESTAMP_OUTPUT), '->', '' if not val else val)


    def list_metrics(self):
        _metrics = self.collector.get_metric_names()
        for stype, metrics in _metrics:
            print('service type', stype.name)
            for m in metrics:
                print(' {}[{}]'.format(m.name, m.type))
