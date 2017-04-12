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

from celery.task import task

from geonode.layers.utils import create_thumbnail


logger = logging.getLogger(__name__)


@task(
    name='geonode.qgis_server.tasks.update.create_qgis_server_thumbnail',
    queue='update')
def create_qgis_server_thumbnail(instance, thumbnail_remote_url, ogc_client):
    try:
        # to make sure it is executed after the instance saved
        time.sleep(5)
        logger.debug('Create thumbnail for %s' % thumbnail_remote_url)
        create_thumbnail(instance, thumbnail_remote_url, ogc_client=ogc_client)
        return True
    except Exception as e:
        logger.exception(e)
        return False
