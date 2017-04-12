# coding=utf-8
import logging
import time

from celery.task import task
from geonode.layers.utils import create_thumbnail

__author__ = 'Rizky Maulana Nugraha <lana.pcfre@gmail.com>'
__date__ = '8/29/16'


logger = logging.getLogger(__name__)


@task(
    name='geonode_qgis_server.tasks.update.create_qgis_server_thumbnail',
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
