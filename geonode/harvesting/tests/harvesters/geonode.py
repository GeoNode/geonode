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

from mock import patch
from django.contrib.auth import get_user_model
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.harvesting.models import Harvester
from geonode.harvesting.harvesters.geonodeharvester import GeonodeLegacyHarvester, GeoNodeResourceType
from geonode.harvesting.harvesters.base import BriefRemoteResource

test_resources = {
    GeoNodeResourceType.DATASET: 1,
    GeoNodeResourceType.DOCUMENT: 2,
    GeoNodeResourceType.MAP: 3,
}


def geonode_get_total_records(cls, resource_type: GeoNodeResourceType):
    """
    Fake _get_total_records function on GeonodeLegacyHarvester
    """
    return test_resources[resource_type]


def geonode_list_resources_by_type(cls, resource_type: GeoNodeResourceType, offset: int):
    """
    Fake _list_resources_by_type function on GeonodeLegacyHarvester
    """
    return [
        BriefRemoteResource(
            unique_identifier="ID",
            title="Title",
            resource_type=resource_type.value,
        )
    ]


class TestGeonodeHarvester(GeoNodeBaseTestSupport):
    """
    Test GeonodeLegacyHarvester
    """

    remote_url = "test.com"
    name = "This is geonode harvester"
    user = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"

    def setUp(self):
        super().setUp()
        self.worker = GeonodeLegacyHarvester(remote_url=self.remote_url, harvester_id=1)

    def test_base_api_url(self):
        """
        Test the return of base_api_url
        """
        self.assertEqual(self.worker.base_api_url, f"{self.remote_url}/api")

    def test_allows_copying_resources(self):
        """
        Test the return of allows_copying_resources
        """
        self.assertTrue(self.worker.allows_copying_resources)

    @patch("geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester._get_total_records", geonode_get_total_records)
    def test_get_num_available_resources_by_type(self):
        """
        Test function of _get_num_available_resources_by_type
        """
        worker = GeonodeLegacyHarvester(remote_url=self.remote_url, harvester_id=1)
        self.assertEqual(worker._get_num_available_resources_by_type(), test_resources)
        self.assertEqual(
            worker._get_total_records(GeoNodeResourceType.DATASET), test_resources[GeoNodeResourceType.DATASET]
        )
        self.assertEqual(
            worker._get_total_records(GeoNodeResourceType.DOCUMENT), test_resources[GeoNodeResourceType.DOCUMENT]
        )
        self.assertEqual(worker._get_total_records(GeoNodeResourceType.MAP), test_resources[GeoNodeResourceType.MAP])

    @patch("geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester._get_total_records", geonode_get_total_records)
    def test_get_num_available_resources(self):
        """
        Test function of get_num_available_resources for each of type in GeonodeLegacyHarvester
        """
        params = {"remote_url": self.remote_url, "harvester_id": 1}
        # test worker that harvest all type
        worker = GeonodeLegacyHarvester(**params)
        self.assertEqual(worker.get_num_available_resources(), 6)

        # test worker with skip document
        worker = GeonodeLegacyHarvester(**params, harvest_documents=False)
        self.assertEqual(worker.get_num_available_resources(), 4)

        # test worker with skip layer
        worker = GeonodeLegacyHarvester(**params, harvest_datasets=False)
        self.assertEqual(worker.get_num_available_resources(), 5)

        # test worker with skip maps
        worker = GeonodeLegacyHarvester(**params, harvest_maps=False)
        self.assertEqual(worker.get_num_available_resources(), 3)

    @patch(
        "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester._list_resources_by_type",
        geonode_list_resources_by_type,
    )
    def test_list_resources_by_type(self):
        """
        Test _list_resources_by_type function for every type in GeonodeLegacyHarvester
        """
        self.assertEqual(
            self.worker._list_resources_by_type(GeoNodeResourceType.DATASET, 0)[0].resource_type,
            GeoNodeResourceType.DATASET.value,
        )
        self.assertEqual(self.worker._list_dataset_resources(1)[0].resource_type, GeoNodeResourceType.DATASET.value)

        self.assertEqual(
            self.worker._list_resources_by_type(GeoNodeResourceType.DOCUMENT, 0)[0].resource_type,
            GeoNodeResourceType.DOCUMENT.value,
        )
        self.assertEqual(self.worker._list_document_resources(1)[0].resource_type, GeoNodeResourceType.DOCUMENT.value)

        self.assertEqual(
            self.worker._list_resources_by_type(GeoNodeResourceType.MAP, 0)[0].resource_type,
            GeoNodeResourceType.MAP.value,
        )
        self.assertEqual(self.worker._list_map_resources(1)[0].resource_type, GeoNodeResourceType.MAP.value)

    def test_extract_unique_identifier(self):
        """
        Test _extract_unique_identifier function
        """
        self.assertEqual(self.worker._extract_unique_identifier({"id": 1}), 1)

    def test_worker_from_django_record(self):
        """
        Test worker that genearted by harvester
        """
        harvester = Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type,
            harvester_type_specific_configuration={
                "harvest_documents": False,
                "harvest_datasets": True,
                "resource_title_filter": "",
            },
        )
        worker = GeonodeLegacyHarvester.from_django_record(harvester)
        self.assertEqual(worker.__class__, GeonodeLegacyHarvester)
        self.assertEqual(worker.remote_url, self.remote_url)
        self.assertEqual(harvester.default_owner, self.user)

        self.assertFalse(worker.harvest_documents)
        self.assertTrue(worker.harvest_datasets)
        self.assertTrue(worker.harvest_maps)
        self.assertEqual(worker.resource_name_filter, "")
