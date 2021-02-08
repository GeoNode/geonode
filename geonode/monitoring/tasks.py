# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from celery import shared_task
from django.core.management import call_command


@shared_task(
    bind=True,
    name='geonode.monitoring.tasks.collect_metrics',
    queue='geoserver.events',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 1, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def collect_metrics(self):
    """
    Collect metrics events data
    """
    return call_command('collect_metrics', '-n', '-t', 'xml')
