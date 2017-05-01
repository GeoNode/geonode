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
import time
from urlparse import urljoin

from celery.task import task
from django.conf import settings
from django.core.urlresolvers import reverse

from geonode.layers.models import Layer
from geonode.layers.utils import create_thumbnail
from geonode.maps.models import Map

logger = logging.getLogger(__name__)


@task(
    name='geonode.qgis_server.tasks.update.create_qgis_server_thumbnail',
    queue='update')
def create_qgis_server_thumbnail(instance, overwrite=False):
    try:
        # to make sure it is executed after the instance saved
        time.sleep(5)
        base_url = settings.SITEURL
        if isinstance(instance, Layer):
            thumbnail_remote_url = reverse(
                'qgis-server-thumbnail', kwargs={'layername': instance.name})
        elif isinstance(instance, Map):
            thumbnail_remote_url = reverse(
                'qgis-server-map-thumbnail', kwargs={'map_id': instance.id})
        else:
            # instance type does not have associated thumbnail
            return True
        thumbnail_remote_url = urljoin(base_url, thumbnail_remote_url)
        logger.debug(thumbnail_remote_url)
        logger.debug('Create thumbnail for %s' % thumbnail_remote_url)
        create_thumbnail(instance, thumbnail_remote_url, overwrite=overwrite)
        return True
    except Exception as e:
        logger.exception(e)
        return False
