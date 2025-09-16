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

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils.timezone import now
from geonode.tests.base import GeoNodeBaseTestSupport

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
    def test_harvest_resource_updates_geonode_when_remote_resource_exists(self, mock_update_asynchronous_session):
        """Test that `worker.get_resource()` is called by the `_harvest_resource()` task and that the related workflow is called too.

        Verify that `worker.get_resource()` is always called. Then verify that if the result of `worker.get_resource()` is
        not `None`, the `worker.update_geonode_resource()` is called and `worker.update_harvesting_session()` is called too.

        """

        harvestable_resource_id = "fake id"
        with mock.patch("geonode.harvesting.tasks.models") as mock_models:
            mock_worker = mock.MagicMock()
            mock_worker.get_resource.return_value = "fake_gotten_resource"
            mock_worker.should_copy_resource.return_value = False
            mock_harvestable_resource = mock.MagicMock(models.HarvestableResource)
            mock_harvestable_resource.harvester.get_harvester_worker.return_value = mock_worker
            mock_models.HarvestableResource.objects.get.return_value = mock_harvestable_resource

            tasks._harvest_resource(harvestable_resource_id, self.harvesting_session.id)

            mock_models.HarvestableResource.objects.get.assert_called_with(pk=harvestable_resource_id)
            mock_worker.get_resource.assert_called()
            mock_worker.update_geonode_resource.assert_called()
            mock_update_asynchronous_session.assert_called()

    def test_harvest_resource_does_not_update_geonode_when_remote_resource_does_not_exist(self):
        """Test that the worker does not try to update existing GeoNode resources when the remote resource cannot be harvested."""

        harvestable_resource_id = "fake id"
        with mock.patch("geonode.harvesting.tasks.models") as mock_models:
            mock_worker = mock.MagicMock()
            mock_worker.get_resource.return_value = None  # this means the remote resource was not harvested
            mock_worker.should_copy_resource.return_value = False
            mock_harvestable_resource = mock.MagicMock(models.HarvestableResource)
            mock_harvestable_resource.harvester.get_harvester_worker.return_value = mock_worker
            mock_models.HarvestableResource.objects.get.return_value = mock_harvestable_resource

            tasks._harvest_resource(harvestable_resource_id, self.harvesting_session.id)

            mock_models.HarvestableResource.objects.get.assert_called_with(pk=harvestable_resource_id)
            mock_worker.get_resource.assert_called()
            mock_worker.update_geonode_resource.assert_not_called()

    def test_finish_harvesting_updates_harvester_status(self):
        tasks._finish_harvesting(self.harvesting_session.id)
        self.harvester.refresh_from_db()
        self.harvesting_session.refresh_from_db()
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        self.assertIsNotNone(self.harvesting_session.ended)

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
        mock_harvester = mock.MagicMock(spec=models.Harvester).return_value
        mock_harvester_model.objects.get.return_value = mock_harvester
        tasks.check_harvester_available(1000)
        mock_harvester.update_availability.assert_called()

    @mock.patch("geonode.harvesting.tasks._handle_harvestable_resources_update_error")
    @mock.patch("geonode.harvesting.tasks._finish_harvestable_resources_update")
    @mock.patch("geonode.harvesting.tasks._update_harvestable_resources_batch")
    @mock.patch("geonode.harvesting.tasks.chord")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_update_harvestable_resources_sends_batched_requests(
        self, mock_models, mock_chord, mock_batch, mock_finalizer, mock_error_handler
    ):
        """Verify that the `update_harvestable_resources` task creates a celery chord with the batched task, a finalizer and an error handler."""
        mock_worker = mock.MagicMock()
        mock_worker.get_num_available_resources.return_value = 1
        mock_harvester = mock.MagicMock(models.Harvester)
        mock_models.Harvester.objects.get.return_value = mock_harvester
        mock_harvester.get_harvester_worker.return_value = mock_worker

        tasks.update_harvestable_resources("fake harvester id")

        mock_batch.signature.assert_called()
        mock_finalizer.signature.assert_called()
        mock_error_handler.signature.assert_called()
        mock_chord.assert_called()
        mock_chord.return_value.apply_async.assert_called()

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
    @mock.patch("geonode.harvesting.tasks.models")
    def test_harvest_resources_with_chunks(
        self,
        mock_models,
        mock_on_commit,
    ):
        mock_session = mock.MagicMock()
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_session.harvester.update_availability.return_value = True
        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        harvestable_resource_ids = list(range(5))

        with mock.patch("geonode.harvesting.tasks.queue_next_chunk_batch.apply_async") as mock_apply_async:
            with override_settings(CHUNK_SIZE=2, MAX_PARALLEL_QUEUE_CHUNKS=2):
                tasks.harvest_resources(harvestable_resource_ids, self.harvesting_session.id)

                # Simulate transaction.on_commit callback being run
                assert mock_on_commit.called
                callback = mock_on_commit.call_args[0][0]
                callback()

            # Now apply_async should have been called
            mock_apply_async.assert_called_once()
            _, kwargs = mock_apply_async.call_args

            expected_expires = 5 * 20 + 300  # 5 resources * 20 + 300 buffer = 400
            expected_time_limit = 2 * 2 * 20 + 300  # CHUNK_SIZE * MAX_PARALLEL_QUEUE_CHUNKS * 20 + 300 = 380

            self.assertEqual(kwargs["expires"], expected_expires)
            self.assertEqual(kwargs["time_limit"], expected_time_limit)

    @mock.patch("geonode.harvesting.tasks.transaction.on_commit")
    @mock.patch("geonode.harvesting.tasks.models")
    def test_harvest_resources_without_chunks(self, mock_models, mock_on_commit):
        mock_session = mock.MagicMock()
        mock_session.status = mock_session.STATUS_ON_GOING
        mock_session.harvester.update_availability.return_value = True
        mock_models.AsynchronousHarvestingSession.objects.get.return_value = mock_session

        harvestable_resource_ids = list(range(5))

        with mock.patch("geonode.harvesting.tasks.chord") as mock_chord:
            mock_workflow = mock.MagicMock()
            mock_chord.return_value = mock_workflow

            with override_settings(CHUNK_SIZE=100, MAX_PARALLEL_QUEUE_CHUNKS=2):
                tasks.harvest_resources(harvestable_resource_ids, self.harvesting_session.id)

                # Check that transaction.on_commit was called
                self.assertTrue(mock_on_commit.called)
                callback = mock_on_commit.call_args[0][0]

                # Simulate the transaction commit
                callback()

            # Check that chord was built with correct number of subtasks
            self.assertTrue(mock_chord.called)
            subtasks = mock_chord.call_args[0][0]  # This is the list of resource tasks
            self.assertEqual(len(subtasks), len(harvestable_resource_ids))

            # Check that apply_async was called on the workflow
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
        dynamic_expiration = 900
        dynamic_time_limit = 1800

        mock_chord_obj = mock.Mock()
        mock_chord.return_value = mock_chord_obj

        tasks.queue_next_chunk_batch(
            chunk_groups=chunk_groups,
            harvesting_session_id=session_id,
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
        self.assertEqual(next_batch.args[2], 1)

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
        dynamic_expiration = 900
        dynamic_time_limit = 1800

        mock_chord_obj = mock.Mock()
        mock_chord.return_value = mock_chord_obj

        tasks.queue_next_chunk_batch(
            chunk_groups=chunk_groups,
            harvesting_session_id=session_id,
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
