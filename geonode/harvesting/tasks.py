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

import math
import logging
import typing

from celery import chord
from django.core.exceptions import ValidationError
from django.db.models import (
    F,
    Value,
)
from django.db.models.functions import Concat
from django.utils import timezone
from geonode.celery_app import app

from . import models
from .harvesters import base

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    queue="geonode",
    acks_late=False,
    ignore_result=False
)
def harvesting_scheduler(self):
    """Check whether any of the configured harvesters needs to be run or not.

    This function is called periodically by celery beat. It is configured to run every
    `HARVESTER_SCHEDULER_FREQUENCY_MINUTES` minutes. This can be configured in the GeoNode
    settings. The default value is 0.5, which means that this function is called every
    thirty seconds.

    """

    logger.debug("+++++ harvesting_dispatcher starting... +++++")
    for harvester in models.Harvester.objects.all():
        if harvester.is_availability_check_due():
            logger.debug(f"{harvester.name} - Updating availability...")
            available = harvester.update_availability()
            logger.debug(f"{harvester.name} - is {'not ' if not available else ''}available")
        else:
            logger.debug(f"{harvester.name} - No need to update availability yet")
        if harvester.scheduling_enabled:
            logger.debug(f"{harvester.name} - scheduling_enabled: {harvester.scheduling_enabled!r}")
            if harvester.is_harvestable_resources_refresh_due():
                logger.debug(f"{harvester.name} - Initiating update of harvestable resources...")
                try:
                    harvester.initiate_update_harvestable_resources()
                except RuntimeError:
                    logger.exception(msg=f"{harvester.name} - Could not initiate the update of harvestable resources")
            else:
                logger.debug(f"{harvester.name} - No need to update harvestable resources yet")
            if harvester.is_harvesting_due():
                logger.debug(f"{harvester.name} - initiating harvesting...")
                try:
                    harvester.initiate_perform_harvesting()
                except RuntimeError:
                    logger.exception(msg=f"{harvester.name} - Could not initiate harvesting")
            else:
                logger.debug(f"{harvester.name} - No need to harvest yet")
        else:
            logger.debug(f"{harvester.name} - Scheduling is disabled for this harvester, skipping...")
    logger.debug("+++++ harvesting_dispatcher ending... +++++")


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def harvesting_dispatcher(
        self,
        harvesting_session_id: int
):
    """Perform harvesting asynchronously.

    This function kicks-off a harvesting session for the input harvester id.
    It defines an async workflow that results in the harvestable resources being
    checked and harvested onto the local GeoNode.

    The implementation briefly consists of:

    - start a harvesting session
    - determine which of the known harvestable resources have to be harvested
    - schedule each harvestable resource to be harvested asynchronously
    - when all resources have been harvested, finish the harvesting session

    Internally, the code uses celery's `chord` workflow primitive. This is used to
    allow the harvesting of individual resources to be done in parallel (as much
    as the celery worker config allows for) and still have a final synchronization
    step, once all resources are harvested, that finalizes the harvesting session.

    """

    session = models.AsynchronousHarvestingSession.objects.get(pk=harvesting_session_id)
    harvester = session.harvester
    harvestable_resources = list(harvester.harvestable_resources.filter(
        should_be_harvested=True).values_list("id", flat=True))
    if len(harvestable_resources) > 0:
        harvest_resources.apply_async(args=(harvestable_resources, harvesting_session_id))
    else:
        message = "harvesting_dispatcher - Nothing to do"
        logger.debug(message)
        finish_asynchronous_session(
            harvesting_session_id,
            models.AsynchronousHarvestingSession.STATUS_FINISHED_ALL_OK,
            final_details=message
        )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def harvest_resources(
        self,
        harvestable_resource_ids: typing.List[int],
        harvesting_session_id: int
):
    """Harvest a list of remote resources that all belong to the same harvester."""
    session = models.AsynchronousHarvestingSession.objects.get(pk=harvesting_session_id)
    if session.status != session.STATUS_ABORTED:
        if len(harvestable_resource_ids) > 0:
            harvester = session.harvester
            if harvester.update_availability():
                harvester.status = harvester.STATUS_PERFORMING_HARVESTING
                harvester.save()
                session.status = session.STATUS_ON_GOING
                session.total_records_to_process = len(harvestable_resource_ids)
                session.save()
                resource_tasks = []
                for harvestable_resource_id in harvestable_resource_ids:
                    resource_tasks.append(
                        _harvest_resource.signature(
                            args=(harvestable_resource_id, harvesting_session_id)
                        )
                    )
                harvesting_finalizer = _finish_harvesting.signature(
                    args=(harvesting_session_id,),
                    immutable=True
                ).on_error(
                    _handle_harvesting_error.signature(
                        kwargs={
                            "harvesting_session_id": harvesting_session_id,
                        }
                    )
                )
                harvesting_workflow = chord(resource_tasks, body=harvesting_finalizer)
                harvesting_workflow.apply_async()
            else:
                message = (
                    f"Skipping harvesting for harvester {harvester.name!r} because the "
                    f"remote {harvester.remote_url!r} seems to be unavailable"
                )
                logger.warning(message)
                finish_asynchronous_session(
                    harvesting_session_id,
                    session.STATUS_FINISHED_ALL_FAILED,
                    final_details=message
                )
        else:
            message = "harvest_resources - Nothing to do..."
            logger.debug(message)
            finish_asynchronous_session(
                harvesting_session_id,
                models.AsynchronousHarvestingSession.STATUS_FINISHED_ALL_OK,
                final_details=message
            )
    else:
        logger.debug("Session has been aborted, skipping...")


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
    session = models.AsynchronousHarvestingSession.objects.get(pk=harvesting_session_id)
    if session.status != session.STATUS_ABORTING:
        harvestable_resource = models.HarvestableResource.objects.get(pk=harvestable_resource_id)
        worker: base.BaseHarvesterWorker = harvestable_resource.harvester.get_harvester_worker()
        harvested_resource_info = worker.get_resource(harvestable_resource)
        now_ = timezone.now()
        if harvested_resource_info is not None:
            if worker.should_copy_resource(harvestable_resource):
                copied_path = worker.copy_resource(harvestable_resource, harvested_resource_info)
                if copied_path is not None:
                    harvested_resource_info.copied_resources.append(copied_path)
            try:
                worker.update_geonode_resource(
                    harvested_resource_info,
                    harvestable_resource,
                )
                result = True
                details = ""
            except (RuntimeError, ValidationError) as exc:
                logger.error(msg="Unable to update geonode resource")
                result = False
                details = str(exc)
            harvesting_message = f"{harvestable_resource.title}({harvestable_resource_id}) - {'Success' if result else details}"
            update_asynchronous_session(
                harvesting_session_id,
                additional_processed_records=1 if result else 0,
                additional_details=harvesting_message
            )
            harvestable_resource.last_harvesting_message = f"{now_} - {harvesting_message}"
            harvestable_resource.last_harvesting_succeeded = result
        else:
            harvestable_resource.last_harvesting_message = f"{now_}Harvesting failed"
            harvestable_resource.last_harvesting_succeeded = False
        harvestable_resource.last_harvested = now_
        harvestable_resource.save()
    else:
        message = (
            f"Skipping harvesting of resource {harvestable_resource_id} since the "
            f"session has been aborted"
        )
        update_asynchronous_session(harvesting_session_id, additional_details=message)
        logger.debug(message)


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _finish_harvesting(self, harvesting_session_id: int):
    session = models.AsynchronousHarvestingSession.objects.get(pk=harvesting_session_id)
    harvester = session.harvester
    if session.status == session.STATUS_ABORTING:
        message = "Harvesting session aborted by user"
        final_status = session.STATUS_ABORTED
    else:
        message = "Harvesting completed successfully!"
        final_status = session.STATUS_FINISHED_ALL_OK
    finish_asynchronous_session(
        harvesting_session_id,
        final_status=final_status,
        final_details=message
    )
    logger.debug(
        f"(harvester: {harvester.pk!r} - session: {harvesting_session_id!r}) "
        f"{message}"
    )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _handle_harvesting_error(self, task_id, *args, **kwargs):
    """Ensure harvester status is set back to `ready` in case of an error."""
    # FIXME NOTE: Unfortunately, we don't seem to have a nice way of knowing what
    # caused the error of a harvesting session. Maybe I just don't understand how
    # this is supposed to work (quite possible) but apparently this is a bug with
    # celery (or maybe just a case of unclear documentation):
    #
    # https://github.com/celery/celery/issues/3709#issuecomment-695809092
    #
    # The celery docs do not match the code:
    #
    # https://docs.celeryproject.org/en/stable/userguide/canvas.html#error-handling
    #
    # Celery docs claim that the error handler receives `request, exc, traceback` as its
    # parameters. However, what we are indeed receiving is `self, task_id, args, kwargs`.
    #
    # Moreover, there does not seem to be a way to get the actual traceback of the failed task.
    # Below we are instantiating the result object, which is gotten from the input `task_id`,
    # However, when checking the result's `traceback` attribute, it shows up empty.
    #
    logger.debug("Inside handle_harvesting_error task ---------------------------------------------------------------------------------------------")
    logger.debug(f"locals before getting the result: {locals()}")
    result = self.app.AsyncResult(str(task_id))
    logger.debug(f"locals after getting the result: {locals()}")
    logger.debug(f"state: {result.state}")
    logger.debug(f"result: {result.result}")
    logger.debug(f"traceback: {result.traceback}")
    logger.debug(f"harvesting task with kwargs: {kwargs} has failed")
    session = models.AsynchronousHarvestingSession.objects.get(pk=kwargs["harvesting_session_id"])
    details = f"state: {result.state}\nresult: {result.result}\ntraceback: {result.traceback}"
    finish_asynchronous_session(
        kwargs["harvesting_session_id"],
        session.STATUS_FINISHED_SOME_FAILED,
        final_details=details
    )


@app.task(
    bind=True,
    # name='geonode.harvesting.tasks.check_harvester_available',
    queue='geonode',
    acks_late=False,
)
def check_harvester_available(self, harvester_id: int):
    harvester = models.Harvester.objects.get(pk=harvester_id)
    available = harvester.update_availability()
    logger.info(
        f"Harvester {harvester!r}: remote server is "
        f"{'' if available else 'not '}available"
    )


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def update_harvestable_resources(self, refresh_session_id: int):
    # NOTE: we are able to implement batch discovery of existing harvestable resources
    # because we want to know about all of them. We are not able to batch harvesting
    # of resources because these have potentially been individually selected by the
    # user, which means we are not interested in all of them
    session = models.AsynchronousHarvestingSession.objects.get(pk=refresh_session_id)
    if session.status != session.STATUS_ABORTED:
        session.status = session.STATUS_ON_GOING
        session.save()
        harvester = session.harvester
        if harvester.update_availability():
            harvester.status = harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
            harvester.save()
            worker = harvester.get_harvester_worker()
            try:
                num_resources = worker.get_num_available_resources()
            except (NotImplementedError, base.HarvestingException) as exc:
                _handle_harvestable_resources_update_error(
                    self.request.id, refresh_session_id=refresh_session_id, raised_exception=exc)
            else:
                harvester.num_harvestable_resources = num_resources
                harvester.save()
                session.total_records_to_process = num_resources
                session.save()
                page_size = 10
                total_pages = math.ceil(num_resources / page_size)
                batches = []
                for page in range(total_pages):
                    batches.append(
                        _update_harvestable_resources_batch.signature(
                            args=(refresh_session_id, page, page_size),
                        )
                    )
                update_finalizer = _finish_harvestable_resources_update.signature(
                    args=(refresh_session_id,),
                    immutable=True
                ).on_error(
                    _handle_harvestable_resources_update_error.signature(
                        kwargs={"refresh_session_id": refresh_session_id}
                    )
                )
                update_workflow = chord(batches, body=update_finalizer)
                update_workflow.apply_async()
        else:
            finish_asynchronous_session(
                refresh_session_id,
                session.STATUS_FINISHED_ALL_FAILED,
                final_details="Harvester is not available"
            )
    else:
        logger.debug("Session has been aborted, skipping...")


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _update_harvestable_resources_batch(
        self,
        refresh_session_id: int,
        page: int,
        page_size: int
):
    session = models.AsynchronousHarvestingSession.objects.get(pk=refresh_session_id)
    if session.status == session.STATUS_ON_GOING:
        harvester = session.harvester
        worker = harvester.get_harvester_worker()
        offset = page * page_size
        try:
            found_resources = worker.list_resources(offset)
        except base.HarvestingException:
            logger.exception("Could not retrieve list of remote resources.")
        else:
            processed = 0
            for remote_resource in found_resources:
                resource, created = models.HarvestableResource.objects.get_or_create(
                    harvester=harvester,
                    unique_identifier=remote_resource.unique_identifier,
                    title=remote_resource.title,
                    defaults={
                        "should_be_harvested": harvester.harvest_new_resources_by_default,
                        "remote_resource_type": remote_resource.resource_type,
                        "last_refreshed": timezone.now()
                    }
                )
                processed += 1
                # NOTE: make sure to save the resource because we need to have its
                # `last_updated` property be refreshed - this is done in order to be able
                # to compare when a resource has been found
                resource.last_refreshed = timezone.now()
                resource.save()
            update_asynchronous_session(refresh_session_id, additional_processed_records=processed)
    else:
        logger.info("The refresh session has been asked to abort, so skipping...")


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _finish_harvestable_resources_update(self, refresh_session_id: int):
    session = models.AsynchronousHarvestingSession.objects.get(pk=refresh_session_id)
    harvester = session.harvester
    if session.status == session.STATUS_ABORTING:
        message = "Refresh session aborted by user"
        finish_asynchronous_session(
            refresh_session_id, session.STATUS_ABORTED, final_details=message)
    else:
        message = "Harvestable resources successfully refreshed"
        finish_asynchronous_session(
            refresh_session_id, session.STATUS_FINISHED_ALL_OK, final_details=message)
        if harvester.last_checked_harvestable_resources is not None:
            _delete_stale_harvestable_resources(harvester)
    now_ = timezone.now()
    harvester.refresh_from_db()
    harvester.last_checked_harvestable_resources = now_
    harvester.last_check_harvestable_resources_message = f"{now_} - {message}"
    harvester.save()


@app.task(
    bind=True,
    queue='geonode',
    acks_late=False,
    ignore_result=False,
)
def _handle_harvestable_resources_update_error(self, task_id, *args, **kwargs):
    logger.debug("Inside _handle_harvestable_resources_update_error -----------------------------------------")
    result = self.app.AsyncResult(str(task_id))
    logger.debug(f"locals: {locals()}")
    logger.debug(f"state: {result.state}")
    logger.debug(f"result: {result.result}")
    logger.debug(f"traceback: {result.traceback}")
    result = self.app.AsyncResult(str(task_id))
    session = models.AsynchronousHarvestingSession.objects.get(pk=kwargs["refresh_session_id"])
    harvester = session.harvester
    now_ = timezone.now()
    harvester.last_checked_harvestable_resources = now_
    harvester.last_check_harvestable_resources_message = (
        f"{now_} - There was an error retrieving information on available "
        f"resources: {result.traceback} - {args} {kwargs}"
        f"Please check the logs"
    )
    harvester.save()
    details = f"state: {result.state}\nresult: {result.result}\ntraceback: {result.traceback}"
    finish_asynchronous_session(
        kwargs["refresh_session_id"],
        final_status=models.AsynchronousHarvestingSession.STATUS_FINISHED_SOME_FAILED,
        final_details=details
    )


def _delete_stale_harvestable_resources(harvester: models.Harvester):
    """Delete harvestable resources that haven't been found on the current refresh.

    If a harvestable resource was not refreshed since the last check, it this means
    it has not been found this time around - maybe it is not available anymore, or
    maybe the user just changed the harvester parameters. Either way, the harvestable
    resource is no longer relevant, and therefore can be deleted.

    When a harvestable resource is deleted, it may leave a corresponding GeoNode
    resource orphan. The corresponding GeoNode resource is the one that had been
    created locally as a result of harvesting information of the HarvestableResource
    on the remote server by the harvester worker. Depending on the value of the
    corresponding `models.Harvester.delete_orphan_resources_automatically`, the GeoNode
    resource may also be deleted as a result of running this method.

    """

    previously_checked_at = harvester.last_checked_harvestable_resources
    logger.debug(f"last checked at: {previously_checked_at}")
    logger.debug(f"now: {timezone.now()}")
    to_remove = models.HarvestableResource.objects.filter(
        harvester=harvester, last_refreshed__lte=previously_checked_at)
    for harvestable_resource in to_remove:
        # NOTE: Iterating on each resource and calling its `delete()` method instead of
        # just calling `delete()` on the queryset because this way we can be sure that
        # the instance's `delete()` method is called (django may not call
        # `instance.delete()` when using the queryset directly, for performance
        # reasons). This is because `HarvestableResource.delete()` has the custom logic
        # to check whether the related GeoNode resource should also be deleted or not
        harvestable_resource.delete()


def finish_asynchronous_session(
        session_id: int,
        final_status: str,
        final_details: typing.Optional[str] = None,
        additional_processed_records: typing.Optional[int] = None
) -> None:
    """Finish the asynchronous session and also reset the harvester status."""
    update_kwargs = {
        "ended": timezone.now(),
        "status": final_status,
    }
    if additional_processed_records is not None:
        update_kwargs["records_done"] = F("records_done") + additional_processed_records
    if final_details is not None:
        update_kwargs["details"] = Concat("details", Value(f"\n{final_details}"))
    models.AsynchronousHarvestingSession.objects.filter(id=session_id).update(**update_kwargs)
    models.Harvester.objects.filter(sessions__pk=session_id).update(
        status=models.Harvester.STATUS_READY)


def update_asynchronous_session(
        session_id: int,
        total_records_to_process: typing.Optional[int] = None,
        additional_processed_records: typing.Optional[int] = None,
        additional_details: typing.Optional[str] = None,
) -> None:
    update_kwargs = {}
    if total_records_to_process is not None:
        update_kwargs["total_records_to_process"] = total_records_to_process
    if additional_processed_records is not None:
        update_kwargs["records_done"] = F("records_done") + additional_processed_records
    if additional_details is not None:
        update_kwargs["details"] = Concat("details", Value(f"\n{additional_details}"))
    models.AsynchronousHarvestingSession.objects.filter(id=session_id).update(**update_kwargs)
