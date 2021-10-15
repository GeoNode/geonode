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

import datetime as dt
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from geonode.tests.base import GeoNodeBaseTestSupport

from .. import models


class HarvesterTestCase(GeoNodeBaseTestSupport):
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

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

    @mock.patch("geonode.harvesting.models.jsonschema")
    @mock.patch("geonode.harvesting.models.import_string")
    def test_validate_worker_configuration(self, mock_import_string, mock_jsonschema):
        extra_config_schema = "fake_config_schema"
        mock_worker_class = mock.MagicMock()
        mock_worker_class.get_extra_config_schema.return_value = extra_config_schema
        mock_import_string.return_value = mock_worker_class

        harvester_type = "fake_harvester_type"
        configuration = {"fake_key": "fake_configuration"}
        models.validate_worker_configuration(harvester_type, configuration)

        mock_import_string.assert_called_with(harvester_type)
        mock_worker_class.get_extra_config_schema.assert_called()
        mock_jsonschema.validate.assert_called_with(configuration, extra_config_schema)

    @mock.patch("geonode.harvesting.models.timezone")
    def test_get_next_check_availability_dispatch_time(self, mock_timezone):
        fixtures = [
            ("2020-01-01T00:00:00", "2020-01-01T00:05:00", 10, "2020-01-01T00:10:00"),
            ("2020-01-01T00:00:00", "2020-01-01T00:11:00", 10, "2020-01-01T00:11:00"),
        ]
        for last_checked, now, frequency, expected in fixtures:
            mock_timezone.now.return_value = dt.datetime.fromisoformat(
                now).replace(tzinfo=dt.timezone.utc)
            harvester = models.Harvester(check_availability_frequency=frequency)
            harvester.last_checked_availability = dt.datetime.fromisoformat(
                last_checked).replace(tzinfo=dt.timezone.utc)
            result = harvester.get_next_check_availability_dispatch_time()
            expected_result = dt.datetime.fromisoformat(expected).replace(tzinfo=dt.timezone.utc)
            self.assertEqual(result, expected_result)

    @mock.patch("geonode.harvesting.models.timezone")
    def test_get_next_dispatch_time(self, mock_timezone):
        fixtures = [
            ("2020-01-01T00:00:00", "2020-01-01T00:05:00", 10, "2020-01-01T00:10:00"),
            ("2020-01-01T00:00:00", "2020-01-01T00:11:00", 10, "2020-01-01T00:11:00"),
        ]
        for last_check, now, frequency, expected in fixtures:
            mock_timezone.now.return_value = dt.datetime.fromisoformat(
                now).replace(tzinfo=dt.timezone.utc)
            with mock.patch.object(
                    models.Harvester,
                    "latest_refresh_session",
                    new_callable=mock.PropertyMock
            ) as mock_latest_refresh_session:
                mock_latest_refresh_session.return_value = mock.MagicMock(
                    started=dt.datetime.fromisoformat(last_check).replace(tzinfo=dt.timezone.utc)
                )
                harvester = models.Harvester(
                    harvesting_session_update_frequency=10,
                    refresh_harvestable_resources_update_frequency=10,
                )
                result = harvester._get_next_dispatch_time(models.AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES)
                expected_result = dt.datetime.fromisoformat(expected).replace(tzinfo=dt.timezone.utc)
                self.assertEqual(result, expected_result)


class AsynchronousHarvestingSessionTestCase(GeoNodeBaseTestSupport):
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

    def setUp(self):
        super().setUp()
        self.harvester = models.Harvester.objects.create(
            remote_url=self.remote_url,
            name=self.name,
            default_owner=self.user,
            harvester_type=self.harvester_type
        )
        self.harvesting_session = models.AsynchronousHarvestingSession.objects.create(
            harvester=self.harvester,
            session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING
        )

    def test_check_attributes(self):
        """
        Test attributes of harvester_session after created.
        """
        self.assertIsNotNone(self.harvesting_session.pk)
        self.assertEqual(self.harvesting_session.harvester, self.harvester)
        self.assertEqual(self.harvesting_session.records_done, 0)


class HarvestableResourceTestCase(GeoNodeBaseTestSupport):
    unique_identifier = 'id'
    title = 'Test'
    remote_url = 'test.com'
    name = 'This is geonode harvester'
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

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
            last_refreshed=dt.datetime.now()
        )

    def test_check_attributes(self):
        self.assertIsNotNone(self.harvestable_resource.pk)
        self.assertEqual(self.harvestable_resource.harvester, self.harvester)
        self.assertEqual(self.harvestable_resource.title, self.title)
        self.assertEqual(self.harvestable_resource.unique_identifier, self.unique_identifier)
        self.assertFalse(self.harvestable_resource.should_be_harvested)
        self.assertEqual(self.harvestable_resource.status, models.HarvestableResource.STATUS_READY)


class WorkerConfigValidationTestCase(SimpleTestCase):

    @mock.patch("geonode.harvesting.models.jsonschema")
    @mock.patch("geonode.harvesting.models.import_string")
    def test_validate_worker_configuration(self, mock_import_string, mock_jsonschema):
        extra_config_schema = "fake_config_schema"
        mock_worker_class = mock.MagicMock()
        mock_worker_class.get_extra_config_schema.return_value = extra_config_schema
        mock_import_string.return_value = mock_worker_class

        harvester_type = "fake_harvester_type"
        configuration = {"somekey": "fake_configuration"}
        models.validate_worker_configuration(harvester_type, configuration)

        mock_import_string.assert_called_with(harvester_type)
        mock_worker_class.get_extra_config_schema.assert_called()
        mock_jsonschema.validate.assert_called_with(configuration, extra_config_schema)
