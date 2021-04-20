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

"""Additional celery tasks for the GeoNode harvester"""

import logging

from geonode.celery_app import app

from geonode.harvesting import models

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name='geonode.harvesting.harvesters.tasks.harvest_records',
    queue='geonode',
    acks_late=False,
)
def harvest_records(self, harvesting_session_id: int, start_index: int, page_size: int):
    harvesting_session = models.HarvestingSession.objects.get(pk=harvesting_session_id)
    harvester = harvesting_session.harvester
    worker = harvester.get_harvester_worker()
    worker.set_harvesting_session_id(harvesting_session_id)
    worker.harvest_record_batch(start_index, page_size)


@app.task(
    bind=True,
    name='geonode.harvesting.harvesters.tasks.finalize_harvesting_session',
    queue='geonode',
    acks_late=False,
)
def finalize_harvesting_session(harvesting_session_id: int):
    harvesting_session = models.HarvestingSession.objects.get(pk=harvesting_session_id)
    harvester = harvesting_session.harvester
    worker = harvester.get_harvester_worker()
    worker.set_harvesting_session_id(harvesting_session_id)
    worker.finish_harvesting_session()

