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
"""Celery tasks for geonode.services"""
import time
import logging
from hashlib import md5

from django.template.defaultfilters import slugify

from . import models
from . import enumerations
from .serviceprocessors import base, get_service_handler

from geonode.celery_app import app
from geonode.layers.models import Layer
from geonode.tasks.tasks import AcquireLock

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name='geonode.services.tasks.harvest_resource',
    queue='upload',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def harvest_resource(self, harvest_job_id):
    harvest_job = models.HarvestJob.objects.get(pk=harvest_job_id)
    harvest_job.update_status(
        status=enumerations.IN_PROCESS, details="Harvesting resource...")
    result = False
    details = ""
    try:
        handler = get_service_handler(
            base_url=harvest_job.service.base_url,
            proxy_base=harvest_job.service.proxy_base,
            service_type=harvest_job.service.type
        )
        logger.debug("harvesting resource...")
        handler.harvest_resource(
            harvest_job.resource_id, harvest_job.service)
        logger.debug("Resource harvested successfully")
        workspace = base.get_geoserver_cascading_workspace(create=False)
        _cnt = 0
        while _cnt < 5 and not result:
            try:
                layer = None
                if Layer.objects.filter(alternate=f"{harvest_job.resource_id}").count():
                    layer = Layer.objects.get(
                        alternate=f"{harvest_job.resource_id}")
                else:
                    layer = Layer.objects.get(
                        alternate=f"{workspace.name}:{harvest_job.resource_id}")
                layer.save(notify=True)
                result = True
            except Exception as e:
                _cnt += 1
                logger.error(
                    f"Notfiy resource {workspace.name}:{harvest_job.resource_id} tentative {_cnt}: {e}")
                try:
                    layer = Layer.objects.get(
                        alternate=f"{slugify(harvest_job.service.base_url)}:{harvest_job.resource_id}")
                    layer.save(notify=True)
                    result = True
                except Exception as e:
                    logger.error(
                        "Notfiy resource "
                        f"{slugify(harvest_job.service.base_url)}:{harvest_job.resource_id} "
                        f"tentative {_cnt}: {e}")
                    time.sleep(1.0)
    except Exception as err:
        logger.exception(msg=f"An error has occurred while harvesting resource {harvest_job.resource_id!r}")
        details = str(err)  # TODO: pass more context about the error
    finally:
        if not details:
            result = True
        harvest_job.update_status(
            status=enumerations.PROCESSED if result else enumerations.FAILED,
            details=details
        )


@app.task(
    bind=True,
    name='geonode.services.tasks.probe_services',
    queue='geonode',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 1, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def probe_services(self):
    # The cache key consists of the task name and the MD5 digest
    # of the name.
    name = b'probe_services'
    hexdigest = md5(name).hexdigest()
    lock_id = f'{name.decode()}-lock-{hexdigest}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            for service in models.Service.objects.all():
                try:
                    service.probe = service.probe_service()
                    service.save()
                except Exception as e:
                    logger.error(e)
