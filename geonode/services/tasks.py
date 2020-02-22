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

import logging

from django.db import transaction

from . import enumerations
from . import models
from .serviceprocessors import get_service_handler

from geonode.celery_app import app
from geonode.layers.models import Layer
from geonode.catalogue.models import catalogue_post_save

logger = logging.getLogger(__name__)


@app.task(bind=True,
          name='geonode.services.tasks.update.harvest_resource',
          queue='update',)
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
        with transaction.atomic():
            logger.debug("harvesting resource...")
            handler.harvest_resource(
                harvest_job.resource_id, harvest_job.service)
            result = True
        logger.debug("Resource harvested successfully")

        logger.debug("Updating Layer Metadata ...")
        try:
            layer = Layer.objects.get(alternate=harvest_job.resource_id)
            catalogue_post_save(instance=layer, sender=layer.__class__)
        except Exception:
            logger.error("Remote Layer [%s] couldn't be updated" % (harvest_job.resource_id))
    except Exception as err:
        logger.exception(msg="An error has occurred while harvesting "
                             "resource {!r}".format(harvest_job.resource_id))
        details = str(err)  # TODO: pass more context about the error
    finally:
        harvest_job.update_status(
            status=enumerations.PROCESSED if result else enumerations.FAILED,
            details=details
        )
