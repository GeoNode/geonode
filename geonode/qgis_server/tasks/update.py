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

import logging
import socket

from celery.task import task

from geonode.layers.models import Layer
from geonode.layers.utils import create_thumbnail
from geonode.maps.models import Map
from geonode.qgis_server.helpers import map_thumbnail_url, layer_thumbnail_url

logger = logging.getLogger(__name__)


@task(
    name='geonode.qgis_server.tasks.update.create_qgis_server_thumbnail',
    queue='update')
def create_qgis_server_thumbnail(instance, overwrite=False):
    thumbnail_remote_url = None
    try:
        # to make sure it is executed after the instance saved
        if isinstance(instance, Layer):
            thumbnail_remote_url = layer_thumbnail_url(instance)
        elif isinstance(instance, Map):
            thumbnail_remote_url = map_thumbnail_url(instance)
        else:
            # instance type does not have associated thumbnail
            return True
        if not thumbnail_remote_url:
            return True
        logger.debug('Create thumbnail for %s' % thumbnail_remote_url)
        create_thumbnail(instance, thumbnail_remote_url, overwrite=overwrite)
        return True
    # if it is socket exception, we should raise it, because there is
    # something wrong with the url
    except socket.error as e:
        logger.error('Thumbnail url not accessed {url}'.format(
            url=thumbnail_remote_url))
        logger.exception(e)
        # reraise exception with original traceback
        raise
    except Exception as e:
        logger.exception(e)
        return False
