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

from geonode.celery_app import app
from celery.utils.log import get_task_logger

from .helpers import gs_slurp, cascading_delete

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_update_layers',
    queue='update',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def geoserver_update_layers(self, *args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_cascading_delete',
    queue='cleanup',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def geoserver_cascading_delete(self, *args, **kwargs):
    """
    Runs cascading_delete.
    """
    return cascading_delete(*args, **kwargs)
