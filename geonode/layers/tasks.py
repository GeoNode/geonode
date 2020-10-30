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

"""celery tasks for geonode.layers."""
from geonode.celery_app import app
from celery.utils.log import get_task_logger
from django.db import IntegrityError, transaction

from geonode.layers.models import Layer

logger = get_task_logger(__name__)


@app.task(
    bind=True,
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
def delete_layer(self, layer_id):
    """
    Deletes a layer.
    """
    try:
        layer = Layer.objects.get(id=layer_id)
    except Layer.DoesNotExist:
        return
    logger.debug('Deleting Layer {0}'.format(layer))
    try:
        with transaction.atomic():
            layer.delete()
    except IntegrityError:
        raise
