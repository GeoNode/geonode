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
import shutil
import socket

import requests
from django.apps import apps
from geonode.celery_app import app
from requests.exceptions import HTTPError


from geonode.layers.models import Layer
from geonode.layers.utils import create_thumbnail
from geonode.maps.models import Map
from geonode.qgis_server.helpers import map_thumbnail_url, layer_thumbnail_url
from geonode.qgis_server.models import QGISServerLayer

from geonode import qgis_server
from geonode.compat import ensure_string
from geonode.decorators import on_ogc_backend

logger = logging.getLogger(__name__)


@app.task(
    name='geonode.qgis_server.tasks.update.create_qgis_server_thumbnail',
    queue='update',
    autoretry_for=(QGISServerLayer.DoesNotExist, ),
    retry_kwargs={'max_retries': 5, 'countdown': 5})
@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def create_qgis_server_thumbnail(model_path, object_id, overwrite=False, bbox=None):
    """Task to update thumbnails.

    This task will formulate OGC url to generate thumbnail and then pass it
    to geonode

    :param instance: Resource instance, can be a layer or map
    :type instance: Layer, Map

    :param overwrite: set True to overwrite
    :type overwrite: bool

    :param bbox: Bounding box of thumbnail in 4 tuple format
        [xmin,ymin,xmax,ymax]
    :type bbox: list(float)

    :return:
    """
    thumbnail_remote_url = None
    instance = apps.get_model(model_path).objects.get(id=object_id)
    try:
        # to make sure it is executed after the instance saved
        if isinstance(instance, Layer):
            thumbnail_remote_url = layer_thumbnail_url(
                instance, bbox=bbox, internal=False)
        elif isinstance(instance, Map):
            thumbnail_remote_url = map_thumbnail_url(
                instance, bbox=bbox, internal=False)
        else:
            # instance type does not have associated thumbnail
            return True
        if not thumbnail_remote_url:
            return True
        logger.debug(f'Create thumbnail for {thumbnail_remote_url}')

        if overwrite:
            # if overwrite, then delete existing thumbnail links
            instance.link_set.filter(
                resource=instance.get_self_resource(),
                name="Remote Thumbnail").delete()
            instance.link_set.filter(
                resource=instance.get_self_resource(),
                name="Thumbnail").delete()

        create_thumbnail(
            instance, thumbnail_remote_url,
            overwrite=overwrite, check_bbox=False)
        return True
    # if it is socket exception, we should raise it, because there is
    # something wrong with the url
    except socket.error as e:
        logger.error(f'Thumbnail url not accessed {thumbnail_remote_url}')
        logger.exception(e)
        # reraise exception with original traceback
        raise
    except QGISServerLayer.DoesNotExist as e:
        logger.exception(e)
        # reraise exception with original traceback
        raise
    except Exception as e:
        logger.exception(e)
        return False


@app.task(
    name='geonode.qgis_server.tasks.update.cache_request',
    queue='update')
@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def cache_request(self, url, cache_file):
    """Cache a given url request to a file.

    On some rare occasions, QGIS Server url request is taking too long to
    complete. This could be a problem if user is requesting something like
    a tile or legend from Web interface and when it takes too long, the
    connection will reset. This case will make the request never be completed
    because the request died with user connection.

    For this kind of request, it is better to register the request as celery
    task. This will make the task to keep running, even if connection is
    reset.

    :param url: The target url to request
    :type url: str

    :param cache_file: The target file path to save the cache
    :type cache_file: str

    :return: True if succeeded
    :rtype: bool
    """
    logger.debug(f'Requesting url: {url}')
    response = requests.get(url, stream=True)

    if not response.status_code == 200:
        # Failed to fetch request. Abort with error message
        msg = (
            'Failed to fetch requested url: {url}\n'
            'With HTTP status code: {status_code}\n'
            'Content: {content}')
        msg = msg.format(
            url=url,
            status_code=response.status_code,
            content=ensure_string(response.content))
        raise HTTPError(msg)

    with open(cache_file, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)

    del response

    return True
