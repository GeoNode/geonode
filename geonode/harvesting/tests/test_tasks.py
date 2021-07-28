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
import collections
import datetime
import mock
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from geonode.tests.base import (
    GeoNodeBaseSimpleTestSupport,
    GeoNodeBaseTestSupport
)

from .. import (
    models,
    tasks,
)
from .harvesters.test_harvester import TestHarvester
from .factories import resource_info_example


class TasksTestCase(GeoNodeBaseTestSupport):

    @classmethod
    def setUpTestData(cls):
        cls.harvester_remote_url = "fake url"
        cls.harvester_name = "harvester1"
        cls.harvester_owner = get_user_model().objects.get(username="AnonymousUser")
        cls.harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"
        cls.harvester = models.Harvester.objects.create(
            remote_url=cls.harvester_remote_url,
            name=cls.harvester_name,
            status=models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES,
            default_owner=cls.harvester_owner,
            harvester_type=cls.harvester_type,
        )
        cls.harvesting_session = models.HarvestingSession.objects.create(harvester=cls.harvester)

    @mock.patch("geonode.harvesting.tasks.models")
    @mock.patch("geonode.harvesting.tasks.utils")
    @mock.patch("geonode.harvesting.tasks.chord")
    def test_harvesting_dispatcher_creates_harvesting_session_when_harvester_available(
            self,
            mock_harvesting_chord,
            mock_harvesting_utils,
            mock_harvesting_models
    ):
        """Test that, when the remote server is available, the dispatcher proceeds to create a harvesting session
        and to call the celery chord that set harvesting in motion

        """

        mock_harvesting_models.HarvestingSession.objects.create.return_value.id.return_value = "fake_session_id"
        mock_harvesting_chord.return_value.apply_async.return_value = None
        mock_harvesting_utils.update_harvester_availability.return_value = True

        tasks.harvesting_dispatcher(self.harvester.id)

        mock_harvesting_models.HarvestingSession.objects.create.assert_called()
        mock_harvesting_chord.assert_called()

    @mock.patch("geonode.harvesting.tasks.models")
    @mock.patch("geonode.harvesting.tasks.utils")
    @mock.patch("geonode.harvesting.tasks.chord")
    def test_harvesting_dispatcher_does_not_create_harvesting_session_when_harvester_not_available(
            self,
            mock_harvesting_chord,
            mock_harvesting_utils,
            mock_harvesting_models
    ):
        """Test that, when the remote server is not available, no harvesting session is created
        and no celery chord is called .

        """

        mock_harvesting_models.HarvestingSession.objects.create.return_value.id.return_value = "fake_session_id"
        mock_harvesting_chord.return_value.apply_async.return_value = None
        mock_harvesting_utils.update_harvester_availability.return_value = False

        tasks.harvesting_dispatcher(self.harvester.id)

        mock_harvesting_models.HarvestingSession.objects.create.assert_not_called()
        mock_harvesting_chord.assert_not_called()

    def test_harvest_resource_updates_geonode_when_remote_resource_exists(self):
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
            mock_worker.update_harvesting_session.assert_called()

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
        tasks._finish_harvesting(self.harvester.id, self.harvesting_session.id)
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

    @mock.patch("geonode.harvesting.tasks.utils")
    def test_check_harvester_available(self, mock_harvesting_utils):
        tasks.check_harvester_available(self.harvester.id)
        mock_harvesting_utils.update_harvester_availability.assert_called_with(self.harvester)

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

    def test_update_harvestable_resources_batch(self):
        pass


# class TestTaskHarvester(GeoNodeBaseTestSupport):
#     """
#     Tests for the harvester model.
#     """
#     remote_url = 'test.com'
#     name = 'This is geonode harvester'
#     user = get_user_model().objects.get(username='AnonymousUser')
#     harvester_type = 'geonode.harvesting.tests.harvesters.test_harvester.TestHarvester'
#
#     def setUp(self):
#         super().setUp()
#         self.harvester = models.Harvester.objects.create(
#             remote_url=self.remote_url,
#             name=self.name,
#             default_owner=self.user,
#             harvester_type=self.harvester_type
#         )
#
#     def test_harvesting_dispatcher(self):
#         """
#         Call harvesting_dispatcher create sessions
#         """
#         tasks.harvesting_dispatcher(self.harvester.id)
#         self.assertIsNotNone(self.harvester.harvesting_sessions.first())
#
#     def test_harvest_resource_failed(self):
#         """
#         Call _harvest_resource when the resource is not found
#         """
#         harvestable_resource = models.HarvestableResource.objects.create(
#             unique_identifier='id',
#             title='Test',
#             harvester=self.harvester,
#             last_refreshed=datetime.datetime.now()
#         )
#         harvesting_session = models.HarvestingSession.objects.create(
#             harvester=self.harvester
#         )
#         tasks._harvest_resource(harvestable_resource.id, harvesting_session.id)
#         harvestable_resource.refresh_from_db()
#         self.assertFalse(harvestable_resource.last_harvesting_succeeded)
#         self.assertTrue('Harvesting failed' in harvestable_resource.last_harvesting_message)
#
#     def test_harvest_resource_success(self):
#         """
#         Call _harvest_resource when the resource is found
#         """
#         with mock.patch.object(TestHarvester, 'get_resource', return_value=resource_info_example):
#             harvestable_resource = models.HarvestableResource.objects.create(
#                 unique_identifier='id',
#                 title='Test',
#                 harvester=self.harvester,
#                 last_refreshed=datetime.datetime.now()
#             )
#             harvesting_session = models.HarvestingSession.objects.create(
#                 harvester=self.harvester
#             )
#             tasks._harvest_resource(harvestable_resource.id, harvesting_session.id)
#             harvestable_resource.refresh_from_db()
#             self.assertTrue(harvestable_resource.last_harvesting_succeeded)
#             self.assertIsNotNone(harvestable_resource.geonode_resource)
#
#     def test_finish_harvesting(self):
#         """
#         Call _finish_harvesting make status ready
#         """
#         self.harvester.status = models.Harvester.STATUS_CHECKING_AVAILABILITY
#         self.harvester.save()
#         self.assertEqual(self.harvester.status, models.Harvester.STATUS_CHECKING_AVAILABILITY)
#
#         harvesting_session = models.HarvestingSession.objects.create(
#             harvester=self.harvester
#         )
#         tasks._finish_harvesting(self.harvester.id, harvesting_session.id)
#         self.harvester.refresh_from_db()
#         self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
#
#     def test_check_harvester_available(self):
#         """
#         Call check_harvester_available
#         """
#         tasks.check_harvester_available(self.harvester.id)
#         self.harvester.refresh_from_db()
#         self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
#         self.assertIsNotNone(self.harvester.last_checked_availability)
#         self.assertTrue(self.harvester.remote_available)
#
#     def test_update_harvestable_resources(self):
#         """
#         Call update_harvestable_resources
#         """
#         tasks.update_harvestable_resources(self.harvester.id)
#         self.harvester.refresh_from_db()
#         self.assertEqual(self.harvester.status, models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES)
#
#     def test_update_harvestable_resources_batch(self):
#         """
#         Call _update_harvestable_resources_batch
#         """
#         tasks._update_harvestable_resources_batch(self.harvester.id, 0, 1)
#         self.harvester.refresh_from_db()
#         self.assertEqual(
#             self.harvester.harvestable_resources.count(), 1)
#
#     def test_finish_harvestable_resources_update(self):
#         """
#         Call _finish_harvestable_resources_update
#         """
#         tasks._finish_harvestable_resources_update(self.harvester.id)
#         self.harvester.refresh_from_db()
#         self.assertIsNotNone(self.harvester.last_checked_harvestable_resources)
#         self.assertTrue(
#             'Harvestable resources successfully checked' in self.harvester.last_check_harvestable_resources_message
#         )
