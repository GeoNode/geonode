# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from geonode.layers.models import Layer
from geonode.maps.models import Map
from celery.task import task


@task(name='geonode.tasks.deletion.delete_layer', queue='cleanup')
def delete_layer(object_id):
    """
    Deletes a layer.
    """
    try:
        layer = Layer.objects.get(id=object_id)
    except Layer.DoesNotExist:
        return

    layer.delete()


@task(name='geonode.tasks.deletion.delete_map', queue='cleanup', expires=300)
def delete_map(object_id):
    """
    Deletes a map and the associated map layers.
    """

    try:
        map_obj = Map.objects.get(id=object_id)
    except Map.DoesNotExist:
        return

    map_obj.layer_set.all().delete()
    map_obj.delete()


@task(name='geonode.tasks.deletion.delete_orphaned_document_files', queue='cleanup')
def delete_orphaned_document_files():
    from geonode.documents.utils import delete_orphaned_document_files
    delete_orphaned_document_files()


@task(name='geonode.tasks.deletion.delete_orphaned_thumbs', queue='cleanup')
def delete_orphaned_thumbnails():
    from geonode.documents.utils import delete_orphaned_thumbs
    delete_orphaned_thumbs()
