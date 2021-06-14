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
import math

from celery import chord
from django.utils.timezone import now
from geonode.celery_app import app

from . import (
    models,
    utils,
)

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def harvesting_dispatcher(self, harvester_id: int):
    """Perform harvesting asynchronously.

    This function kicks-off a harvesting session for the input harvester id.
    It defines an async workflow that results in the harvestable resources being
    checked and harvested onto the local GeoNode.

    The implementation briefly consists of:

    - start a harvesting session
    - determine which of the known harvestable resources are to be harvested
    - schedule each harvestable resource to be harvested asynchronously
    - when all resources have been harvested, finish the harvesting session

    The code uses celery's chord workflow primitive. This is used to allow the
    harvesting of individual resources to be done in parallel (as much as the celery
    worker config allows for) and still have a final synchronization step, once all
    resources are harvested, that finalizes the harvesting session.

    """

    harvester = models.Harvester.objects.get(pk=harvester_id)
    available = utils.update_harvester_availability(harvester)
    if available:
        harvester.status = harvester.STATUS_PERFORMING_HARVESTING
        harvester.save()
        harvesting_session = models.HarvestingSession.objects.create(
            harvester=harvester)
        harvestable_resources = harvester.harvestable_resources.filter(
            should_be_harvested=True)
        resource_tasks = []
        for harvestable_resource in harvestable_resources:
            resource_tasks.append(
                _harvest_resource.signature(
                    args=(harvestable_resource.id, harvesting_session.id)
                )
            )
        harvesting_finalizer = _finish_harvesting.signature(
            args=(harvester_id, harvesting_session.id),
            immutable=True
        ).on_error(
            _handle_harvesting_error.signature(
                kwargs={
                    "harvester_id": harvester_id,
                    "harvesting_session_id": harvesting_session.id,
                }
            )
        )
        harvesting_workflow = chord(resource_tasks, body=harvesting_finalizer)
        harvesting_workflow.apply_async()
    else:
        logger.warning(
            f"Skipping harvesting for harvester {harvester.name!r} because the "
            f"remote {harvester.remote_url!r} seems to be unavailable"
        )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _harvest_resource(
        self,
        harvestable_resource_id: int,
        harvesting_session_id: int
):
    """Harvest a single resource from the input harvestable resource id"""
    logger.debug(f"Inside _harvest_resource")
    harvestable_resource = models.HarvestableResource.objects.get(
        pk=harvestable_resource_id)
    worker = harvestable_resource.harvester.get_harvester_worker()
    resource_descriptor = worker.get_resource(
        harvestable_resource.unique_identifier,
        harvestable_resource.remote_resource_type,
        harvesting_session_id=harvesting_session_id)
    worker.update_geonode_resource(resource_descriptor)


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _finish_harvesting(self, harvester_id: int, harvesting_session_id: int):
    logger.debug("Inside _finish_harvesting")
    harvester = models.Harvester.objects.get(pk=harvester_id)
    harvester.status = harvester.STATUS_READY
    harvester.save()
    worker = harvester.get_harvester_worker()
    worker.finish_harvesting_session(harvesting_session_id)


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _handle_harvesting_error(self, task_id, *args, **kwargs):
    logger.debug("Inside the handle_harvesting_error task ---------------------------------------------------------------------------------------------")
    result = self.app.AsyncResult(str(task_id))
    print(f"locals: {locals()}")
    print(f"state: {result.state}")
    print(f"result: {result.result}")
    print(f"traceback: {result.traceback}")
    harvester = models.Harvester.objects.get(pk=kwargs["harvester_id"])
    harvester.status = harvester.STATUS_READY
    # now_ = now()
    # harvester.last_checked_harvestable_resources = now_
    # harvester.last_check_harvestable_resources_message = (
    #     f"{now_} - There was an error retrieving information on available resources. "
    #     f"Please check the logs"
    # )
    harvester.save()
    worker = harvester.get_harvester_worker()
    worker.finish_harvesting_session(kwargs["harvesting_session_id"])


@app.task(
    bind=True,
    #name='geonode.harvesting.tasks.check_harvester_available',
    queue='geonode',
    acks_late=False,
)
def check_harvester_available(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    available = utils.update_harvester_availability(harvester)
    logger.info(
        f"Harvester {harvester!r}: remote server is "
        f"{'' if available else 'not'} available"
    )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def update_harvestable_resources(self, harvester_id: int):
    # NOTE: we are able to implement batch discovery of existing harvestable resources
    # because we want to know about all of them. We are not able to batch harvesting
    # of resources because these have potentially been individually selected by the
    # user, which means we are not interested in all of them
    # TODO: implement removal of harvestable_resources that are not available anymore
    harvester = models.Harvester.objects.get(pk=harvester_id)
    harvester.status = harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
    harvester.save()
    worker = harvester.get_harvester_worker()
    try:
        num_resources = worker.get_num_available_resources()
    except NotImplementedError:
        _handle_harvestable_resources_update_error(
            self.request.id, harvester_id=harvester_id)
    page_size = 10
    total_pages = math.ceil(num_resources / page_size)
    batches = []
    for page in range(total_pages):
        batches.append(
            _update_harvestable_resources_batch.signature(
                args=(harvester_id, page, page_size),
            )
        )
    update_finalizer = _finish_harvestable_resources_update.signature(
        args=(harvester_id,),
        immutable=True
    ).on_error(
        _handle_harvestable_resources_update_error.signature(
            kwargs={"harvester_id": harvester_id}
        )
    )
    update_workflow = chord(batches, body=update_finalizer)
    update_workflow.apply_async()


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _update_harvestable_resources_batch(
        self, harvester_id: int, page: int, page_size: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    worker = harvester.get_harvester_worker()
    offset = page * page_size
    found_resources = worker.list_resources(offset)
    for remote_resource in found_resources:
        resource, created = models.HarvestableResource.objects.get_or_create(
            harvester=harvester,
            unique_identifier=remote_resource.unique_identifier,
            title=remote_resource.title,
            available=True,
            defaults={
                "should_be_harvested": harvester.harvest_new_resources_by_default,
                "remote_resource_type": remote_resource.resource_type
            }
        )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _finish_harvestable_resources_update(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    harvester.status = harvester.STATUS_READY
    now_ = now()
    harvester.last_checked_harvestable_resources = now_
    harvester.last_check_harvestable_resources_message = (
        f"{now_} - Harvestable resources successfully checked")
    harvester.save()


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _handle_harvestable_resources_update_error(self, task_id, *args, **kwargs):
    logger.debug("Inside the handle_harvestable_resources_update_error task ---------------------------------------------------------------------------------------------")
    result = self.app.AsyncResult(str(task_id))
    print(f"locals: {locals()}")
    print(f"state: {result.state}")
    print(f"result: {result.result}")
    print(f"traceback: {result.traceback}")
    harvester = models.Harvester.objects.get(pk=kwargs["harvester_id"])
    harvester.status = harvester.STATUS_READY
    now_ = now()
    harvester.last_checked_harvestable_resources = now_
    harvester.last_check_harvestable_resources_message = (
        f"{now_} - There was an error retrieving information on available resources. "
        f"Please check the logs"
    )
    harvester.save()