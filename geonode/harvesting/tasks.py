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
    name='geonode.harvesting.tasks.harvesting_session_dispatcher',
    queue='geonode',
    acks_late=False,
)
def harvesting_session_dispatcher(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    worker = harvester.get_harvester_worker()
    logger.debug(f"harvester running every {harvester.update_frequency!r} minutes")
    logger.debug(f"harvester worker: {worker}")
    logger.debug(f"harvester worker remote url: {worker.remote_url!r}")
    worker.perform_metadata_harvesting()
