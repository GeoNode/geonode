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
from django.core.management import call_command

from geonode.celery_app import app


@app.task(
    bind=True,
    name='geonode.monitoring.tasks.collect_metrics',
    queue='update',
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5, 'countdown': 180})
def collect_metrics(self):
    """
    Collect metrics events data
    """
    return call_command('collect_metrics', '-n', '-t', 'xml')
