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
import json
import logging

from celery import chord
from celery.result import allow_join_result
from gsimporter.api import NotFound

from django.conf import settings
from django.utils.timezone import timedelta, now

from geonode.celery_app import app
from geonode.geoserver.helpers import gs_uploader

from geonode.upload.models import Upload
from geonode.upload.views import final_step_view
from geonode.upload.utils import next_step_response

from geonode.tasks.tasks import (
    AcquireLock,
    FaultTolerantTask)

logger = logging.getLogger(__name__)

UPLOAD_SESSION_EXPIRY_HOURS = getattr(settings, 'UPLOAD_SESSION_EXPIRY_HOURS', 24)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    queue='upload',
    acks_late=False,
    ignore_result=True)
def finalize_incomplete_session_uploads(self, *args, **kwargs):
    """The task periodically checks for pending and stale Upload sessions.
    It runs every 600 seconds (see the PeriodTask on geonode.upload._init_),
    checks first for expired stale Upload sessions and schedule them for cleanup.
    We have to make sure To NOT Delete those Unprocessed Ones,
    which are in live sessions.
    After removing the stale ones, it collects all the unprocessed and runs them
    in parallel."""

    _upload_ids = []
    _upload_tasks = []
    _upload_ids_expired = []

    # Check first if we need to delete stale sessions
    expiry_time = now() - timedelta(hours=UPLOAD_SESSION_EXPIRY_HOURS)
    for _upload in Upload.objects.exclude(state=Upload.STATE_PROCESSED).exclude(date__gt=expiry_time):
        _upload.set_processing_state(Upload.STATE_INVALID)
        _upload_ids_expired.append(_upload.id)
        _upload_tasks.append(
            _upload_session_cleanup.signature(
                args=(_upload.id,)
            )
        )

    upload_workflow_finalizer = _upload_workflow_finalizer.signature(
        args=('_upload_session_cleanup', _upload_ids_expired,),
        immutable=True
    ).on_error(
        _upload_workflow_error.signature(
            args=('_upload_session_cleanup', _upload_ids_expired,),
            immutable=True
        )
    )
    upload_workflow = chord(_upload_tasks, body=upload_workflow_finalizer)
    upload_workflow.apply_async()

    # Let's finish the valid ones
    session = None
    for _upload in Upload.objects.exclude(state__in=[Upload.STATE_PROCESSED, Upload.STATE_INVALID]).exclude(id__in=_upload_ids_expired):
        try:
            if not _upload.import_id:
                raise NotFound
            session = _upload.get_session.import_session if _upload.get_session else None
            if not session or session.state != Upload.STATE_COMPLETE:
                session = gs_uploader.get_session(_upload.import_id)
        except (NotFound, Exception) as e:
            logger.exception(e)
            session = None

        if session:
            _upload_ids.append(_upload.id)
            _upload_tasks.append(
                _update_upload_session_state.signature(
                    args=(_upload.id,)
                )
            )
        elif _upload.state not in (Upload.STATE_READY, Upload.STATE_COMPLETE, Upload.STATE_RUNNING):
            if session and session.state == Upload.STATE_COMPLETE and _upload.layer and _upload.layer.processed:
                _upload.set_processing_state(Upload.STATE_PROCESSED)

    upload_workflow_finalizer = _upload_workflow_finalizer.signature(
        args=('_update_upload_session_state', _upload_ids,),
        immutable=True
    ).on_error(
        _upload_workflow_error.signature(
            args=('_update_upload_session_state', _upload_ids,),
            immutable=True
        )
    )

    upload_workflow = chord(_upload_tasks, body=upload_workflow_finalizer)
    result = upload_workflow.apply_async()
    if result.ready():
        with allow_join_result():
            return result.get()
    return result.state


@app.task(
    bind=True,
    base=FaultTolerantTask,
    queue='upload',
    acks_late=False,
    ignore_result=False)
def _upload_workflow_finalizer(self, task_name: str, upload_ids: list):
    """Task invoked at 'upload_workflow.chord' end in the case everything went well.
    """
    if upload_ids:
        logger.info(f"Task {task_name} upload ids: {upload_ids} finished successfully!")


@app.task(
    bind=True,
    base=FaultTolerantTask,
    queue='upload',
    acks_late=False,
    ignore_result=False,
)
def _upload_workflow_error(self, task_name: str, upload_ids: list):
    """Task invoked at 'upload_workflow.chord' end in the case some error occurred.
    """
    logger.error(f"Task {task_name} upload ids: {upload_ids} did not finish correctly!")
    for _upload in Upload.objects.filter(id__in=upload_ids):
        _upload.set_processing_state(Upload.STATE_INVALID)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    queue='upload',
    acks_late=False,
    ignore_result=False)
def _update_upload_session_state(self, upload_session_id: int):
    """Task invoked by 'upload_workflow.chord' in order to process all the 'PENDING' Upload tasks."""
    lock_id = f'_update_upload_session_state-{upload_session_id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            _upload = Upload.objects.get(id=upload_session_id)
            session = _upload.get_session.import_session
            if not session or session.state != Upload.STATE_COMPLETE:
                session = gs_uploader.get_session(_upload.import_id)

            if session:
                try:
                    _response = next_step_response(None, _upload.get_session)
                    _upload.refresh_from_db()
                    _content = _response.content
                    if isinstance(_content, bytes):
                        _content = _content.decode('UTF-8')
                    _response_json = json.loads(_content)
                    _success = _response_json.get('success', False)
                    _redirect_to = _response_json.get('redirect_to', '')

                    _tasks_ready = any([_task.state in ["READY"] for _task in session.tasks])
                    _tasks_failed = any([_task.state in ["BAD_FORMAT", "ERROR", "CANCELED"] for _task in session.tasks])
                    _tasks_waiting = any([_task.state in ["NO_CRS", "NO_BOUNDS", "NO_FORMAT"] for _task in session.tasks])

                    if _success:
                        if _tasks_failed:
                            # GeoNode Layer creation errored!
                            _upload.set_processing_state(Upload.STATE_INVALID)
                        elif 'upload/final' not in _redirect_to and 'upload/check' not in _redirect_to and (_tasks_waiting or _upload.get_session.time):
                            _upload.set_resume_url(_redirect_to)
                            _upload.set_processing_state(Upload.STATE_WAITING)
                        elif session.state in (Upload.STATE_PENDING, Upload.STATE_RUNNING) and not (_tasks_waiting or _tasks_ready):
                            if _upload.layer and not _upload.layer.processed:
                                # GeoNode Layer updating...
                                _upload.set_processing_state(Upload.STATE_RUNNING)
                            elif session.state == Upload.STATE_RUNNING and _upload.layer and _upload.layer.processed:
                                # GeoNode Layer successfully processed...
                                _upload.set_processing_state(Upload.STATE_PROCESSED)
                        elif (session.state == Upload.STATE_COMPLETE and _upload.state in (
                                Upload.STATE_COMPLETE, Upload.STATE_PENDING) and not _tasks_waiting) or (
                                session.state == Upload.STATE_PENDING and _tasks_ready):
                            if not _upload.layer:
                                _response = final_step_view(None, _upload.get_session)
                                if _response:
                                    _upload.refresh_from_db()
                                    if _upload.state not in (Upload.STATE_PROCESSED, Upload.STATE_RUNNING) and not _upload.layer:
                                        # GeoNode Layer still updating...
                                        _upload.set_processing_state(Upload.STATE_RUNNING)
                        logger.debug(f"Upload {upload_session_id} updated with state {_upload.state}.")
                except (NotFound, Exception) as e:
                    logger.exception(e)
                    if _upload.state not in (Upload.STATE_COMPLETE, Upload.STATE_PROCESSED):
                        _upload.set_processing_state(Upload.STATE_INVALID)
                        logger.error(f"Upload {upload_session_id} deleted with state {_upload.state}.")
            elif _upload.state != Upload.STATE_PROCESSED:
                _upload.set_processing_state(Upload.STATE_INVALID)
                logger.error(f"Unable to find the Importer Session - Upload {upload_session_id} deleted with state {_upload.state}.")


@app.task(
    bind=True,
    base=FaultTolerantTask,
    queue='upload',
    acks_late=False,
    ignore_result=False)
def _upload_session_cleanup(self, upload_session_id: int):
    """Task invoked by 'upload_workflow.chord' in order to remove and cleanup all the 'INVALID' stale Upload tasks."""
    try:
        _upload = Upload.objects.get(id=upload_session_id)
        if _upload.layer:
            _upload.layer.delete()
        _upload.delete()
        logger.debug(f"Upload {upload_session_id} deleted with state {_upload.state}.")
    except Exception as e:
        logger.error(f"Upload {upload_session_id} errored with exception {e}.")
