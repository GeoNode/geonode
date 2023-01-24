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
from geonode.harvesting.models import Harvester, HarvestableResource
from geonode.harvesting.tests.harvesters.test_harvester import TestHarvester
from geonode.layers.models import Dataset


class TestBaseHarvester(GeoNodeBaseTestSupport):
    """
    Test Base harvester
    """

    remote_url = "test.com"
    name = "This is geonode harvester"
    user = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.tests.harvesters.test_harvester.TestHarvester"

    def setUp(self):
        super().setUp()
        self.worker = TestHarvester(remote_url=self.remote_url, harvester_id=1)

    def test_worker_from_harvester(self):
        """
        Test worker that generated from harvester
        """
        harvester = Harvester.objects.create(
            remote_url=self.remote_url, name=self.name, default_owner=self.user, harvester_type=self.harvester_type
        )
        worker = harvester.get_harvester_worker()
        self.assertEqual(worker.__class__, TestHarvester)
        self.assertEqual(worker.remote_url, self.remote_url)
        self.assertEqual(harvester.default_owner, self.user)

    def test_worker_from_django_record(self):
        """
        Test worker that generated from worker using harvester record
        """
        harvester = Harvester.objects.create(
            remote_url=self.remote_url, name=self.name, default_owner=self.user, harvester_type=self.harvester_type
        )
        worker = TestHarvester.from_django_record(harvester)
        self.assertEqual(worker.__class__, TestHarvester)
        self.assertEqual(worker.remote_url, self.remote_url)
        self.assertEqual(harvester.default_owner, self.user)

    def test_worker_methods(self):
        """
        Test functions in worker
        """
        self.assertEqual(self.worker.remote_url, self.remote_url)
        self.assertEqual(self.worker.harvester_id, 1)
        self.assertTrue(self.worker.allows_copying_resources)
        self.assertTrue(self.worker.check_availability())
        self.assertEqual(self.worker.get_num_available_resources(), 1)
        self.assertEqual(len(self.worker.list_resources()), 1)
        self.assertEqual(self.worker.get_geonode_resource_type("type"), Dataset)

        harvestable_resource = HarvestableResource(
            unique_identifier="1",
            title="Test Resource",
            harvester=Harvester(
                remote_url=self.remote_url, name=self.name, default_owner=self.user, harvester_type=self.harvester_type
            ),
            last_refreshed=datetime.datetime.now(),
        )
        self.assertIsNone(self.worker.get_resource(harvestable_resource, 1))
