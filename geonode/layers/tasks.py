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

from celery import shared_task
from celery.utils.log import get_task_logger

from geonode.layers.models import Layer

logger = get_task_logger(__name__)


@shared_task(bind=True,
             name='geonode.layers.tasks.update.delete_layer',
             queue='cleanup',
             autoretry_for=(Layer.DoesNotExist, ),
             retry_kwargs={'max_retries': 5, 'countdown': 5})
def delete_layer(self, layer_id):
    """
    Deletes a layer.
    """
    layer = Layer.objects.get(id=layer_id)
    logger.info('Deleting Layer {0}'.format(layer))
    layer.delete()
    return True
