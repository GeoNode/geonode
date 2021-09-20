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

from django.contrib.auth import get_user_model
from geonode.tests.base import GeoNodeBaseTestSupport

from .. import models


class HarvesterTestCase(GeoNodeBaseTestSupport):
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"

    def setUp(self):
        super().setUp()
        self.harvester = models.Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type
        )

    def test_get_worker_works(self):
        worker = self.harvester.get_harvester_worker()
        self.assertEqual(worker.remote_url, self.remote_url)

    def test_setup_periodic_tasks(self):
        self.assertIsNotNone(self.harvester.periodic_task)
        self.assertIsNotNone(self.harvester.availability_check_task)
        self.assertEqual(self.harvester.periodic_task.name, self.harvester.name)
        self.assertEqual(self.harvester.periodic_task.interval.every, self.harvester.update_frequency)
        self.assertEqual(self.harvester.availability_check_task.name, f"Check availability of {self.name}")
        self.assertEqual(self.harvester.availability_check_task.interval.every, self.harvester.check_availability_frequency)


class HarvesterSessionTestCase(GeoNodeBaseTestSupport):
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"

    def setUp(self):
        super().setUp()
        self.harvester = models.Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type
        )
        self.harvesting_session = models.HarvestingSession.objects.create(
            harvester=self.harvester
        )

    def test_check_attributes(self):
        """
        Test attributes of harvester_session after created.
        """
        self.assertIsNotNone(self.harvesting_session.pk)
        self.assertEqual(self.harvesting_session.harvester, self.harvester)
        self.assertEqual(self.harvesting_session.records_harvested, 0)


class HarvestableResourceTestCase(GeoNodeBaseTestSupport):
    unique_identifier = 'id'
    title = 'Test'
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"

    def setUp(self):
        super().setUp()
        self.harvester = models.Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type
        )
        self.harvestable_resource = models.HarvestableResource.objects.create(
            unique_identifier=self.unique_identifier,
            title=self.title,
            harvester=self.harvester,
            last_refreshed=datetime.datetime.now()
        )

    def test_check_attributes(self):
        self.assertIsNotNone(self.harvestable_resource.pk)
        self.assertEqual(self.harvestable_resource.harvester, self.harvester)
        self.assertEqual(self.harvestable_resource.title, self.title)
        self.assertEqual(self.harvestable_resource.unique_identifier, self.unique_identifier)
        self.assertFalse(self.harvestable_resource.should_be_harvested)
        self.assertEqual(self.harvestable_resource.status, models.HarvestableResource.STATUS_READY)
