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
from celery.app import shared_task
from celery.utils.log import get_task_logger
from .helpers import gs_slurp

logger = get_task_logger(__name__)


@shared_task(bind=True, queue='update')
def geoserver_update_layers(self, *args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@shared_task(bind=True)
def thumbnail_task(self,
                   instance_id,
                   instance_type,
                   overwrite=False,
                   check_bbox=False):
    if instance_type == 'Layer':
        from geonode.layers.models import Layer
        instance = Layer.objects.get(id=instance_id)
    elif instance_type == 'Map':
        from geonode.maps.models import Map
        instance = Map.objects.get(id=instance_id)
    elif instance_type == 'Document':
        from geonode.documents.models import Document
        instance = Document.objects.get(id=instance_id)
    else:
        from geonode.base.models import ResourceBase
        instance = ResourceBase.objects.get(id=instance_id)
    from .helpers import create_gs_thumbnail
    create_gs_thumbnail(instance, overwrite, check_bbox)
