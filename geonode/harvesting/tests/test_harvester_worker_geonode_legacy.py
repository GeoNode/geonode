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
from unittest import mock

from django.utils import timezone

from geonode.harvesting.harvesters import geonodeharvester
from geonode.tests.base import GeoNodeBaseSimpleTestSupport

from .. import models


class GeoNodeHarvesterWorkerTestCase(GeoNodeBaseSimpleTestSupport):
    def test_base_api_url(self):
        """Base API URL does not have an extra slash, regardless of whether the original URL has it or not"""
        base_remote_urls = [
            ("http://fake-url1", "http://fake-url1/api"),
            ("http://fake-url2/", "http://fake-url2/api"),
        ]
        harvester_id = "fake-id"
        for base_url, expected in base_remote_urls:
            worker = geonodeharvester.GeonodeLegacyHarvester(base_url, harvester_id)
            self.assertEqual(worker.base_api_url, expected)

    def test_that_copying_remote_resources_is_allowed(self):
        worker = geonodeharvester.GeonodeLegacyHarvester("http://fake-url2/", "fake-id")
        self.assertTrue(worker.allows_copying_resources)

    def test_creation_from_harvester(self):
        now = timezone.now()
        keywords = ["keyword1", "keyword2"]
        categories = ["category1", "category2"]
        combinations = [
            {
                "harvest_documents": True,
                "harvest_datasets": True,
                "copy_datasets": True,
                "copy_documents": True,
                "resource_title_filter": "something",
                "start_date_filter": now,
                "end_date_filter": now,
                "keywords_filter": keywords,
                "categories_filter": categories,
            },
        ]
        for param_combination in combinations:
            harvester = models.Harvester(
                name="fake1",
                harvester_type="geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester",
                harvester_type_specific_configuration=param_combination,
            )
            harvester.get_harvester_worker()

    @mock.patch("geonode.harvesting.harvesters.geonodeharvester.requests.Session")
    def test_check_availability_works_when_response_includes_layers_object(self, mock_requests_session):
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"layers": []}
        mock_requests_session.return_value.get.return_value = mock_response

        base_url = "http://fake-url1"
        worker = geonodeharvester.GeonodeLegacyHarvester(base_url, harvester_id=None)
        result = worker.check_availability()
        self.assertEqual(result, True)

    @mock.patch("geonode.harvesting.harvesters.geonodeharvester.requests.Session")
    def test_check_availability_fails_when_response_does_not_include_layers_object(self, mock_requests_session):
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {}
        mock_requests_session.return_value.get.return_value = mock_response

        base_url = "http://fake-url2"
        worker = geonodeharvester.GeonodeLegacyHarvester(base_url, harvester_id=None)
        result = worker.check_availability()
        self.assertEqual(result, False)
