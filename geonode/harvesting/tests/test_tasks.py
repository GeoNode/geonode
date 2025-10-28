##############################################
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
from unittest import mock
import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils.timezone import now
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.models import ExecutionRequest

from .. import (
    models,
    tasks,
)


class TasksTestCase(GeoNodeBaseTestSupport):
    harvester: models.Harvester
    harvester_remote_url = "fake url"
    harvester_name = "harvester1"
    harvester_owner = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

    @classmethod
    def setUpTestData(cls):
        cls.harvester = models.Harvester.objects.create(
            remote_url=cls.harvester_remote_url,
            name=cls.harvester_name,
            status=models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES,
            default_owner=cls.harvester_owner,
            harvester_type=cls.harvester_type,
        )
        cls.harvesting_session = models.AsynchronousHarvestingSession.objects.create(
            harvester=cls.harvester, session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING
        )
        for index in range(3):
            models.HarvestableResource.objects.create(
                unique_identifier=f"fake-identifier-{index}",
                title=f"fake-title-{index}",
                harvester=cls.harvester,
                remote_resource_type="fake-remote-resource-type",
                last_refreshed=now(),
            )

    @mock.patch("geonode.harvesting.tasks.update_asynchronous_session")
    @mock.patch("geonode.resource.models.ExecutionRequest.objects.get")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    @mock.patch("geonode.harvesting.tasks.models.HarvestableResource.objects.get")
    def test_harvest_resource_updates_geonode_when_remote_resource_exists(
        self, mock_get_resource, mock_get_session, mock_get_exec_req, mock_update_asynchronous_session
    ):
        """Test that get_resource, update_geonode_resource and update_asynchronous_session are called."""

        harvestable_resource_id = 123
        fake_execution_id = str(uuid.uuid4())

        # Mock session
        mock_session = mock.MagicMock()
        mock_session.status = "running"
        mock_session.STATUS_ABORTING = "aborting"
        mock_get_session.return_value = mock_session

        # Mock ExecutionRequest
        mock_exec_req = mock.MagicMock()
        mock_exec_req.output_params = {}
        mock_get_exec_req.return_value = mock_exec_req

        # Mock worker
        mock_worker = mock.MagicMock()
        mock_worker.get_resource.return_value = "fake_gotten_resource"
        mock_worker.update_geonode_resource.return_value = None

        # Mock resource
        mock_resource = mock.MagicMock()
        mock_resource.title = "Fake Title"
        mock_resource.harvester.get_harvester_worker.return_value = mock_worker
        mock_get_resource.return_value = mock_resource

        # Run the task
        result = tasks._harvest_resource(harvestable_resource_id, mock_session.pk, fake_execution_id)

        # Assert
        mock_get_resource.assert_called_with(pk=harvestable_resource_id)
        mock_worker.get_resource.assert_called_once_with(mock_resource)
        mock_worker.update_geonode_resource.assert_called_once()
        mock_update_asynchronous_session.assert_called()
        assert result["status"] == "success"

    @mock.patch("geonode.harvesting.tasks.ExecutionRequest.objects.select_for_update")
    @mock.patch("geonode.harvesting.tasks.update_asynchronous_session")
    @mock.patch("geonode.resource.models.ExecutionRequest.objects.get")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    @mock.patch("geonode.harvesting.tasks.models.HarvestableResource.objects.get")
    def test_harvest_resource_does_not_update_geonode_when_remote_resource_does_not_exist(
        self,
        mock_get_resource,
        mock_get_session,
        mock_get_exec_req,
        mock_update_asynchronous_session,
        mock_select_for_update,
    ):
        """Test that GeoNode is not updated if remote resource cannot be harvested."""

        harvestable_resource_id = 123
        fake_execution_id = str(uuid.uuid4())

        # Mock session
        mock_session = mock.MagicMock()
        mock_session.status = "running"
        mock_session.STATUS_ABORTING = "aborting"
        mock_get_session.return_value = mock_session

        # Mock ExecutionRequest
        mock_exec_req = mock.MagicMock()
        mock_exec_req.output_params = {}
        mock_get_exec_req.return_value = mock_exec_req
        mock_select_for_update.return_value.get.return_value = mock_exec_req

        # Mock worker with None returned from get_resource
        mock_worker = mock.MagicMock()
        mock_worker.get_resource.return_value = None

        # Mock harvestable resource
        mock_resource = mock.MagicMock()
        mock_resource.title = "Fake Title"
        mock_resource.harvester.get_harvester_worker.return_value = mock_worker
        mock_get_resource.return_value = mock_resource

        # Call the task
        result = tasks._harvest_resource(harvestable_resource_id, mock_session.pk, fake_execution_id)

        # Assertions
        mock_get_resource.assert_called_with(pk=harvestable_resource_id)
        mock_worker.get_resource.assert_called_once_with(mock_resource)
        mock_worker.update_geonode_resource.assert_not_called()
        mock_update_asynchronous_session.assert_called()
        assert result["status"] == "failed"
        assert "no resource info returned" in result["details"].lower()

    def test_finish_harvesting_updates_harvester_status(self):
        fake_execution_id = str(uuid.uuid4())
        exec_req = ExecutionRequest.objects.create(
            exec_id=fake_execution_id,
            status=ExecutionRequest.STATUS_READY,
            output_params={},  # no failures
        )

        tasks._finish_harvesting.apply(args=(self.harvesting_session.id, fake_execution_id))

        # Refresh from DB
        self.harvester.refresh_from_db()
        self.harvesting_session.refresh_from_db()
        exec_req.refresh_from_db()

        # Assert Harvester is ready (only if `finish_asynchronous_session()` sets this)
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)

        # Assert session ended timestamp is set
        self.assertIsNotNone(self.harvesting_session.ended)

        # Assert execution request was finalized
        self.assertEqual(exec_req.status, ExecutionRequest.STATUS_FINISHED)
        self.assertIn("completed successfully", exec_req.log)

    def test_handle_harvesting_error_cleans_up_harvest_execution(self):
        tasks._handle_harvesting_error(
            None, harvester_id=self.harvester.id, harvesting_session_id=self.harvesting_session.id
        )
        self.harvester.refresh_from_db()
        self.harvesting_session.refresh_from_db()
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        self.assertIsNotNone(self.harvesting_session.ended)

    @mock.patch("geonode.harvesting.tasks.models.Harvester")
    def test_check_harvester_available(self, mock_harvester_model):

        mock_harvester = mock_harvester_model
        mock_harvester_model.objects.get.return_value = mock_harvester
        tasks.check_harvester_available(1000)
        mock_harvester.update_availability.assert_called()

    @mock.patch("geonode.harvesting.tasks.calculate_dynamic_expiration")
    @mock.patch("geonode.harvesting.tasks._handle_harvestable_resources_update_error")
    @mock.patch("geonode.harvesting.tasks._finish_harvestable_resources_update")
    @mock.patch("geonode.harvesting.tasks._update_harvestable_resources_batch")
    @mock.patch("geonode.harvesting.tasks.chord")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_update_harvestable_resources_sends_batched_requests(
        self,
        mock_models,
        mock_chord,
        mock_batch,
        mock_finalizer,
        mock_error_handler,
        mock_calculate_expiration,
    ):
        """Verify that `update_harvestable_resources` creates a celery chord with expiration."""

        # Set up mock harvester and session
        mock_worker = mock.MagicMock()
        mock_worker.get_num_available_resources.return_value = 1

        mock_harvester = mock.MagicMock()
        mock_harvester.get_harvester_worker.return_value = mock_worker
        mock_harvester.update_availability.return_value = True

        mock_session = mock.MagicMock()
        mock_session.status = models.AsynchronousHarvestingSession.STATUS_ON_GOING
        mock_session.harvester = mock_harvester

        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        mock_calculate_expiration.return_value = 123

        # Setup the finalizer signature and its chained call
        mock_finalizer_sig = mock.MagicMock(name="finalizer_signature")
        mock_finalizer_on_error = mock.MagicMock(name="finalizer_on_error")
        mock_finalizer_sig.on_error.return_value = mock_finalizer_on_error
        mock_finalizer.signature.return_value = mock_finalizer_sig

        # Run the task
        tasks.update_harvestable_resources("fake_session_id")

        # Assert expiration was calculated
        mock_calculate_expiration.assert_called_once_with(1)

        # Assert batch task had expiration set
        mock_batch.signature.return_value.set.assert_any_call(expires=123)

        # Assert finalizer had expiration set via the on_error chain
        mock_finalizer_on_error.set.assert_called_once_with(expires=123)

        # Assert chord was called with expiration
        mock_chord.return_value.apply_async.assert_called_once_with(args=(), expires=123)

    def test_harvesting_scheduler(self):
        mock_harvester = mock.MagicMock(spec=models.Harvester).return_value
        mock_harvester.scheduling_enabled = True
        mock_harvester.is_harvestable_resources_refresh_due.return_value = True
        mock_harvester.is_harvesting_due.return_value = True
        with mock.patch("geonode.harvesting.tasks.models.Harvester.objects") as mock_qs:
            mock_qs.all.return_value = [mock_harvester]
            tasks.harvesting_scheduler()
            mock_harvester.is_availability_check_due.assert_called()
            mock_harvester.is_harvestable_resources_refresh_due.assert_called()
            mock_harvester.initiate_update_harvestable_resources.assert_called()
            mock_harvester.is_harvesting_due.assert_called()
            mock_harvester.initiate_perform_harvesting.assert_called()

    @mock.patch("geonode.harvesting.tasks.transaction.on_commit")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_harvest_resources_with_chunks(self, mock_get, mock_on_commit):
        mock_session = mock.MagicMock(
            spec=[
                "status",
                "STATUS_ON_GOING",
                "STATUS_ABORTING",
                "STATUS_ABORTED",
                "harvester",
                "started_at",
                "save",
                "id",
            ]
        )
        mock_session.STATUS_ON_GOING = "ON_GOING"
        mock_session.STATUS_ABORTING = "ABORTING"
        mock_session.STATUS_ABORTED = "ABORTED"
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_session.harvester = mock.MagicMock()
        mock_session.harvester.update_availability.return_value = True
        mock_session.started_at = datetime.now()
        mock_session.id = 123

        mock_get.side_effect = lambda *_, **__: mock_session

        harvestable_resource_ids = list(range(5))

        with mock.patch("geonode.harvesting.tasks.queue_next_chunk_batch.apply_async") as mock_apply_async:
            with override_settings(CHUNK_SIZE=2, MAX_PARALLEL_QUEUE_CHUNKS=2):
                tasks.harvest_resources(harvestable_resource_ids, mock_session.id)

                assert mock_on_commit.called
                callback = mock_on_commit.call_args[0][0]
                callback()

            mock_apply_async.assert_called_once()
            _, kwargs = mock_apply_async.call_args

            expected_expires = 5 * 20 + 600  # adjust to match production logic
            expected_time_limit = 2 * 2 * 20 + 300

            self.assertEqual(kwargs["expires"], expected_expires)
            self.assertEqual(kwargs["time_limit"], expected_time_limit)

    @mock.patch("geonode.harvesting.tasks.transaction.on_commit")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_harvest_resources_without_chunks(self, mock_get, mock_on_commit):
        # Mock session with explicit spec and STATUS constants
        mock_session = mock.MagicMock(
            spec=[
                "status",
                "STATUS_ON_GOING",
                "STATUS_ABORTING",
                "STATUS_ABORTED",
                "harvester",
                "started_at",
                "save",
                "id",
            ]
        )
        mock_session.STATUS_ON_GOING = "ON_GOING"
        mock_session.STATUS_ABORTING = "ABORTING"
        mock_session.STATUS_ABORTED = "ABORTED"
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_session.harvester = mock.MagicMock()
        mock_session.harvester.update_availability.return_value = True
        mock_session.started_at = datetime.now()
        mock_session.id = 456
        mock_session.save.return_value = None

        mock_get.side_effect = lambda *_, **__: mock_session

        harvestable_resource_ids = list(range(5))

        with mock.patch("geonode.harvesting.tasks.chord") as mock_chord:
            mock_workflow = mock.MagicMock()
            mock_chord.return_value = mock_workflow

            # Large CHUNK_SIZE disables chunking logic
            with override_settings(CHUNK_SIZE=100, MAX_PARALLEL_QUEUE_CHUNKS=2):
                tasks.harvest_resources(harvestable_resource_ids, mock_session.id)

                # Simulate post-commit callback
                self.assertTrue(mock_on_commit.called)
                callback = mock_on_commit.call_args[0][0]
                callback()

            # Validate that chord was built correctly
            self.assertTrue(mock_chord.called)
            subtasks = mock_chord.call_args[0][0]
            self.assertEqual(len(subtasks), len(harvestable_resource_ids))

            # Verify final workflow trigger
            mock_workflow.apply_async.assert_called_once()

    @mock.patch("geonode.harvesting.tasks.logger")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_harvest_resources_aborted_session(self, mock_models, mock_logger):
        mock_session = mock.MagicMock()
        mock_session.status = mock_session.STATUS_ABORTED
        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        tasks.harvest_resources([1, 2, 3], self.harvesting_session.id)

        mock_logger.debug.assert_any_call("Session has been aborted, skipping...")
        # Ensure nothing else happened
        mock_session.harvester.update_availability.assert_not_called()

    @mock.patch("geonode.harvesting.tasks.finish_asynchronous_session")
    @mock.patch("geonode.harvesting.tasks.logger")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_harvest_resources_no_ids(self, mock_models, mock_logger, mock_finish):
        mock_session = mock.MagicMock()
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        tasks.harvest_resources([], self.harvesting_session.id)

        mock_logger.debug.assert_any_call("harvest_resources - Nothing to do...")
        mock_finish.assert_called_once_with(
            self.harvesting_session.id,
            mock_models.AsynchronousHarvestingSession.STATUS_FINISHED_ALL_OK,
            final_details="No resources to harvest",
        )

    @mock.patch("geonode.harvesting.tasks.finish_asynchronous_session")
    @mock.patch("geonode.harvesting.tasks.logger")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_harvest_resources_harvester_unavailable(self, mock_models, mock_logger, mock_finish):
        mock_session = mock.MagicMock()
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_session.harvester.name = "TestHarvester"
        mock_session.harvester.remote_url = "http://remote"
        mock_session.harvester.update_availability.return_value = False
        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        tasks.harvest_resources([1, 2, 3], self.harvesting_session.id)

        mock_logger.warning.assert_called_once_with(
            "Skipping harvesting for harvester 'TestHarvester' because remote 'http://remote' is unavailable"
        )
        mock_finish.assert_called_once_with(
            self.harvesting_session.id,
            mock_session.STATUS_FINISHED_ALL_FAILED,
            final_details=mock_logger.warning.call_args[0][0],
        )

    @mock.patch("geonode.harvesting.tasks.chord")
    def test_queue_next_chunk_batch_schedules_next_batch(self, mock_chord):
        chunk_groups = [[[1, 2], [3]], [[4, 5]]]
        session_id = 42
        batch_index = 0
        fake_execution_id = str(uuid.uuid4())
        dynamic_expiration = 900
        dynamic_time_limit = 1800

        mock_chord_obj = mock.Mock()
        mock_chord.return_value = mock_chord_obj

        tasks.queue_next_chunk_batch(
            chunk_groups=chunk_groups,
            harvesting_session_id=session_id,
            execution_id=fake_execution_id,
            batch_index=batch_index,
            dynamic_expiration=dynamic_expiration,
            dynamic_time_limit=dynamic_time_limit,
        )

        # Check that chord() was called
        self.assertEqual(mock_chord.call_count, 3)
        chords_args, chords_kwargs = mock_chord.call_args

        chords_in_batch = chords_args[0]
        next_batch = chords_kwargs["body"]

        # Expect 2 chunks in batch 0 → 2 chords
        self.assertEqual(len(chords_in_batch), 2)

        # Check next_batch is queue_next_chunk_batch task for batch 1
        self.assertEqual(next_batch.args[3], 1)

        # Final: check apply_async was called
        mock_chord.return_value.apply_async.assert_called_once()

    @mock.patch("geonode.harvesting.tasks.chord")
    @mock.patch("geonode.harvesting.tasks._finish_harvesting")
    @mock.patch("geonode.harvesting.tasks._handle_harvesting_error")
    def test_queue_next_chunk_batch_adds_global_finalizer_on_last_batch(
        self, mock_handle_error, mock_finish_harvesting, mock_chord
    ):
        chunk_groups = [[[1, 2], [3]], [[4, 5]]]
        session_id = 42
        batch_index = 1
        fake_execution_id = str(uuid.uuid4())
        dynamic_expiration = 900
        dynamic_time_limit = 1800

        mock_chord_obj = mock.Mock()
        mock_chord.return_value = mock_chord_obj

        tasks.queue_next_chunk_batch(
            chunk_groups=chunk_groups,
            harvesting_session_id=session_id,
            execution_id=fake_execution_id,
            batch_index=batch_index,
            dynamic_expiration=dynamic_expiration,
            dynamic_time_limit=dynamic_time_limit,
        )

        # Ensure global finalizer was built and passed to chords_in_batch
        self.assertTrue(mock_finish_harvesting.s.called)
        self.assertTrue(mock_handle_error.s.called)

        chord_args, chord_kwargs = mock_chord.call_args
        chords_in_batch = chord_args[0]

        # Expect 1 chunk + 1 global finalizer = 2 entries in chords_in_batch
        self.assertEqual(len(chords_in_batch), 2)
        self.assertIn(mock_finish_harvesting.s.return_value.on_error.return_value.set.return_value, chords_in_batch)

        # Final: check apply_async was called
        mock_chord.return_value.apply_async.assert_called_once()

    def test_harvest_resource_sets_status_in_execution_request(self):
        harvesting_session = self.harvesting_session
        harvester = self.harvester

        # Create the shared ExecutionRequest object
        exec_req = ExecutionRequest.objects.create(
            exec_id=uuid.uuid4(),
            status="running",
            log="",
            output_params={},
        )

        harvesting_session.execution_request = exec_req
        harvesting_session.save()

        execution_id = str(exec_req.exec_id)

        # Failure case
        resource_fail = models.HarvestableResource.objects.create(
            unique_identifier="fail-identifier",
            title="Fail Resource",
            harvester=harvester,
            remote_resource_type="fake-remote-resource-type",
            last_refreshed=now(),
        )

        mock_worker_fail = mock.MagicMock()
        mock_worker_fail.get_resource.return_value = "fake_gotten_resource"
        mock_worker_fail.update_geonode_resource.side_effect = RuntimeError("Test failure")
        resource_fail.harvester.get_harvester_worker = mock.MagicMock(return_value=mock_worker_fail)

        with (
            mock.patch("geonode.harvesting.tasks.models.HarvestableResource.objects.get", return_value=resource_fail),
            mock.patch(
                "geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get",
                return_value=harvesting_session,
            ),
        ):
            result = tasks._harvest_resource(resource_fail.pk, harvesting_session.pk, execution_id)
            assert result["status"] == "failed"
            assert "Test failure" in result["details"] or "Test failure" in result.get("error", "")

            exec_req.refresh_from_db()
            failures = exec_req.output_params.get("failures", [])
            assert any(f["resource_id"] == resource_fail.pk and f["status"] == "failed" for f in failures)

        # Success case
        resource_success = models.HarvestableResource.objects.create(
            unique_identifier="success-identifier",
            title="Success Resource",
            harvester=harvester,
            remote_resource_type="fake-remote-resource-type",
            last_refreshed=now(),
        )

        mock_worker_success = mock.MagicMock()
        mock_worker_success.get_resource.return_value = "fake_gotten_resource"
        mock_worker_success.update_geonode_resource.return_value = None
        resource_success.harvester.get_harvester_worker = mock.MagicMock(return_value=mock_worker_success)

        with (
            mock.patch(
                "geonode.harvesting.tasks.models.HarvestableResource.objects.get", return_value=resource_success
            ),
            mock.patch(
                "geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get",
                return_value=harvesting_session,
            ),
        ):
            result = tasks._harvest_resource(resource_success.pk, harvesting_session.pk, execution_id)
            assert result["status"] == "success"

            exec_req.refresh_from_db()
            failures = exec_req.output_params.get("failures", [])
            assert all(f["resource_id"] != resource_success.pk for f in failures)

    @mock.patch("geonode.harvesting.tasks.logger")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_finish_harvesting_handles_exception(self, mock_get_session, mock_logger):
        harvesting_session_id = self.harvesting_session.pk
        execution_id = str(uuid.uuid4())

        # Simulate DB lookup failure
        mock_get_session.side_effect = Exception("Database error")

        tasks._finish_harvesting(harvesting_session_id=harvesting_session_id, execution_id=execution_id)

        # Check logger.exception was called with the expected error
        mock_logger.exception.assert_called_once()
        assert f"Failed to finalize harvesting session {harvesting_session_id}" in mock_logger.exception.call_args[0][0]

    @mock.patch("geonode.harvesting.tasks.finish_asynchronous_session")
    @mock.patch("geonode.resource.models.ExecutionRequest.objects.get")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_finish_harvesting_some_tasks_failed(self, mock_get_session, mock_get_exec_req, mock_finish_session):
        harvesting_session_id = self.harvesting_session.pk
        execution_id = str(uuid.uuid4())

        # Prepare mock session
        mock_session = mock.MagicMock()
        mock_session.pk = harvesting_session_id
        mock_session.status = "some_status"
        mock_session.STATUS_ABORTING = "aborting"
        mock_session.STATUS_ABORTED = "aborted"
        mock_session.STATUS_FINISHED_SOME_FAILED = "some_failed"
        mock_session.STATUS_FINISHED_ALL_OK = "all_ok"
        mock_session.harvester.pk = 42
        mock_get_session.return_value = mock_session

        # Prepare mock execution request
        mock_exec_req = mock.MagicMock()
        mock_exec_req.output_params = {
            "failures": [
                {"resource_id": 1, "status": "failed"},
                {"resource_id": 2, "status": "failed"},
            ]
        }
        mock_exec_req.log = ""
        mock_get_exec_req.return_value = mock_exec_req

        # Run the task
        tasks._finish_harvesting(harvesting_session_id=harvesting_session_id, execution_id=execution_id)

        # Assert session finalization was triggered
        mock_finish_session.assert_called_once_with(
            harvesting_session_id,
            final_status=mock_session.STATUS_FINISHED_SOME_FAILED,
            final_details="Harvesting completed with errors: 2 task(s) failed.",
        )

        # Assert ExecutionRequest updated
        mock_exec_req.save.assert_called_once()
        updated_log = mock_exec_req.log
        assert "Harvesting completed with errors" in updated_log
        assert mock_exec_req.status == ExecutionRequest.STATUS_FINISHED

    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_monitor_exits_when_not_ongoing(self, mock_get):
        mock_session = mock.MagicMock()
        mock_session.status = "FINISHED"
        mock_session.STATUS_ON_GOING = "ON_GOING"
        mock_session.STATUS_ABORTING = "ABORTING"
        mock_get.return_value = mock_session

        tasks.harvesting_session_monitor(1, 60)
        mock_get.assert_called_once()

    @mock.patch("geonode.harvesting.tasks.harvesting_session_monitor.apply_async")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_monitor_reschedules_itself(self, mock_get, mock_apply_async):
        current_time = now()
        mock_session = mock.MagicMock()
        mock_session.status = "ON_GOING"
        mock_session.STATUS_ON_GOING = "ON_GOING"
        mock_session.STATUS_ABORTING = "ABORTING"
        mock_session.started = current_time
        mock_get.return_value = mock_session

        tasks.harvesting_session_monitor(1, 3600, delay=5)
        mock_apply_async.assert_called_once()

    @mock.patch("geonode.harvesting.tasks._finish_harvesting.apply_async")
    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_monitor_triggers_finalizer_if_stuck(self, mock_get, mock_apply_async):
        mock_session = mock.MagicMock()
        mock_session.status = "ON_GOING"
        mock_session.STATUS_ON_GOING = "ON_GOING"
        mock_session.STATUS_ABORTING = "ABORTING"
        mock_session.started = now() - timedelta(hours=1)
        mock_get.return_value = mock_session

        # Call your monitor
        tasks.harvesting_session_monitor(harvesting_session_id=1, workflow_time=60, delay=0)

        # Check that apply_async was called with correct args
        mock_apply_async.assert_called_once()
        args, kwargs = mock_apply_async.call_args

    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_monitor_session_does_not_exist(self, mock_get):
        mock_get.side_effect = models.AsynchronousHarvestingSession.DoesNotExist

        # Capture logs from the correct logger
        with self.assertLogs("geonode.harvesting.tasks", level="WARNING") as log_cm:
            tasks.harvesting_session_monitor(999, 60)

        # Check that the warning about non-existing session was logged
        self.assertTrue(
            any(
                "Session 999 does not exist. Harvesting session monitor exiting." in message
                for message in log_cm.output
            )
        )

        # Ensure the get() was called
        mock_get.assert_called_once_with(pk=999)

    @mock.patch("geonode.harvesting.tasks.models.AsynchronousHarvestingSession.objects.get")
    def test_monitor_handles_exception(self, mock_get):
        # Force an exception
        mock_get.side_effect = RuntimeError("boom")

        # Capture logs from the correct logger
        with self.assertLogs("geonode.harvesting.tasks", level="ERROR") as log_cm:
            tasks.harvesting_session_monitor(1, 60)

        # Check that the exception was logged
        self.assertTrue(
            any("Harvesting session monitor failed for session 1: boom" in message for message in log_cm.output)
        )
