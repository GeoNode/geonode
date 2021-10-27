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
from django.utils.timezone import now
from geonode.tests.base import (
    GeoNodeBaseTestSupport
)

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
            harvester=cls.harvester,
            session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING
        )
        for index in range(3):
            models.HarvestableResource.objects.create(
                unique_identifier=f"fake-identifier-{index}",
                title=f"fake-title-{index}",
                harvester=cls.harvester,
                remote_resource_type="fake-remote-resource-type",
                last_refreshed=now()
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
        tasks._handle_harvesting_error(None, harvester_id=self.harvester.id, harvesting_session_id=self.harvesting_session.id)
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
    def test_update_harvestable_resources_sends_batched_requests(self, mock_models, mock_chord, mock_batch, mock_finalizer, mock_error_handler):
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
