#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from geonode.celery_app import app

from . import models

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    #name='geonode.harvesting.tasks.harvesting_session_dispatcher',
    queue='geonode',
    acks_late=False,
)
def harvesting_session_dispatcher(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    worker = harvester.get_harvester_worker()
    remote_available = worker.update_availability()
    if remote_available:
        worker.perform_metadata_harvesting()
    else:
        logger.warning(
            f"Skipping harvesting session for harvester {harvester.name!r} because the "
            f"remote {harvester.remote_url!r} seems to be unavailable"
        )


@app.task(
    bind=True,
    #name='geonode.harvesting.tasks.check_harvester_available',
    queue='geonode',
    acks_late=False,
)
def check_harvester_available(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    worker = harvester.get_harvester_worker()
    available = worker.update_availability()
    logger.info(
        f"Harvester {harvester!r}: remote server is "
        f"{'' if available else 'not'} available"
    )
