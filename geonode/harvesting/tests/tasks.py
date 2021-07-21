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

import datetime
from mock import patch
from django.contrib.auth import get_user_model
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.harvesting.models import (
    Harvester, HarvestingSession, HarvestableResource
)
from geonode.harvesting.tasks import (
    harvesting_dispatcher, _harvest_resource, _finish_harvesting,
    check_harvester_available, update_harvestable_resources,
    _update_harvestable_resources_batch, _finish_harvestable_resources_update
)
from geonode.harvesting.tests.harvesters.test_harvester import TestHarvester
from geonode.harvesting.tests.factories import resource_info_example


class TestTaskHarvester(GeoNodeBaseTestSupport):
    """
    Tests for the harvester model.
    """
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = 'geonode.harvesting.tests.harvesters.test_harvester.TestHarvester'

    def setUp(self):
        super().setUp()
        self.harvester = Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type
        )

    def test_harvesting_dispatcher(self):
        """
        Call harvesting_dispatcher create sessions
        """
        harvesting_dispatcher(self.harvester.id)
        self.assertIsNotNone(self.harvester.harvesting_sessions.first())

    def test_harvest_resource_failed(self):
        """
        Call _harvest_resource when the resource is not found
        """
        harvestable_resource = HarvestableResource.objects.create(
            unique_identifier='id',
            title='Test',
            harvester=self.harvester,
            last_refreshed=datetime.datetime.now()
        )
        harvesting_session = HarvestingSession.objects.create(
            harvester=self.harvester
        )
        _harvest_resource(harvestable_resource.id, harvesting_session.id)
        harvestable_resource.refresh_from_db()
        self.assertFalse(harvestable_resource.last_harvesting_succeeded)
        self.assertTrue('Harvesting failed' in harvestable_resource.last_harvesting_message)

    def test_harvest_resource_success(self):
        """
        Call _harvest_resource when the resource is found
        """
        with patch.object(TestHarvester, 'get_resource', return_value=resource_info_example):
            harvestable_resource = HarvestableResource.objects.create(
                unique_identifier='id',
                title='Test',
                harvester=self.harvester,
                last_refreshed=datetime.datetime.now()
            )
            harvesting_session = HarvestingSession.objects.create(
                harvester=self.harvester
            )
            _harvest_resource(harvestable_resource.id, harvesting_session.id)
            harvestable_resource.refresh_from_db()
            self.assertTrue(harvestable_resource.last_harvesting_succeeded)
            self.assertIsNotNone(harvestable_resource.geonode_resource)

    def test_finish_harvesting(self):
        """
        Call _finish_harvesting make status ready
        """
        self.harvester.status = Harvester.STATUS_CHECKING_AVAILABILITY
        self.harvester.save()
        self.assertEqual(self.harvester.status, Harvester.STATUS_CHECKING_AVAILABILITY)

        harvesting_session = HarvestingSession.objects.create(
            harvester=self.harvester
        )
        _finish_harvesting(self.harvester.id, harvesting_session.id)
        self.harvester.refresh_from_db()
        self.assertEqual(self.harvester.status, Harvester.STATUS_READY)

    def test_check_harvester_available(self):
        """
        Call check_harvester_available
        """
        check_harvester_available(self.harvester.id)
        self.harvester.refresh_from_db()
        self.assertEqual(self.harvester.status, Harvester.STATUS_READY)
        self.assertIsNotNone(self.harvester.last_checked_availability)
        self.assertTrue(self.harvester.remote_available)

    def test_update_harvestable_resources(self):
        """
        Call update_harvestable_resources
        """
        update_harvestable_resources(self.harvester.id)
        self.harvester.refresh_from_db()
        self.assertEqual(self.harvester.status, Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES)

    def test_update_harvestable_resources_batch(self):
        """
        Call _update_harvestable_resources_batch
        """
        _update_harvestable_resources_batch(self.harvester.id, 0, 1)
        self.harvester.refresh_from_db()
        self.assertEqual(
            self.harvester.harvestable_resources.count(), 1)

    def test_finish_harvestable_resources_update(self):
        """
        Call _finish_harvestable_resources_update
        """
        _finish_harvestable_resources_update(self.harvester.id)
        self.harvester.refresh_from_db()
        self.assertIsNotNone(self.harvester.last_checked_harvestable_resources)
        self.assertTrue(
            'Harvestable resources successfully checked' in self.harvester.last_check_harvestable_resources_message
        )
