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
import mock.mock

from geonode.harvesting.harvesters import geonode
from geonode.tests.base import GeoNodeBaseSimpleTestSupport


class GeoNodeHarvesterWorkerTestCase(GeoNodeBaseSimpleTestSupport):

    def test_base_api_url(self):
        """Base API URL does not have an extra slash, regardless of whether the original URL has it or not"""
        base_remote_urls = [
            ("http://fake-url1", "http://fake-url1/api"),
            ("http://fake-url2/", "http://fake-url2/api"),
        ]
        harvester_id = "fake-id"
        for base_url, expected in base_remote_urls:
            worker = geonode.GeonodeLegacyHarvester(base_url, harvester_id)
            self.assertEqual(worker.base_api_url, expected)

    @mock.patch("geonode.harvesting.harvesters.geonode.requests.Session")
    def test_check_availability_works_when_response_includes_layers_object(self, mock_requests_session):
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"layers": []}
        mock_requests_session.return_value.get.return_value = mock_response

        base_url = "http://fake-url1"
        worker = geonode.GeonodeLegacyHarvester(base_url, harvester_id=None)
        result = worker.check_availability()
        self.assertEqual(result, True)

    @mock.patch("geonode.harvesting.harvesters.geonode.requests.Session")
    def test_check_availability_fails_when_response_does_not_include_layers_object(self, mock_requests_session):
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {}
        mock_requests_session.return_value.get.return_value = mock_response

        base_url = "http://fake-url2"
        worker = geonode.GeonodeLegacyHarvester(base_url, harvester_id=None)
        result = worker.check_availability()
        self.assertEqual(result, False)
