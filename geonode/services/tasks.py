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

from __future__ import absolute_import

import logging

from celery import shared_task
from django.db import transaction

from . import enumerations
from . import models
from .serviceprocessors import get_service_handler

logger = logging.getLogger(__name__)


@shared_task(bind=True)
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
    except Exception as err:
        logger.exception(msg="An error has occurred while harvesting "
                             "resource {!r}".format(harvest_job.resource_id))
        details = str(err)  # TODO: pass more context about the error
    finally:
        harvest_job.update_status(
            status=enumerations.PROCESSED if result else enumerations.FAILED,
            details=details
        )
