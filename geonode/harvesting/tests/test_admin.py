from unittest import mock

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

from geonode.tests.base import GeoNodeBaseTestSupport

from .. import models


class HarvesterAdminTestCase(GeoNodeBaseTestSupport):
    harvester_type = 'geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester'

    def setUp(self):
        self.user = get_user_model().objects.get(username='admin')
        self.client.login(username="admin", password="admin")

        self.harvester = models.Harvester.objects.create(
            remote_url="http://fake1.com",
            name="harvester1",
            default_owner=self.user,
            harvester_type=self.harvester_type
        )

    @mock.patch(
        "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester.check_availability")
    def test_add_harvester(self, mock_check_availability):
        mock_check_availability.return_value = True
        data = {
            'remote_url': "http://fake.com",
            'name': 'harvester',
            'harvester_type_specific_configuration': '{}',
            'harvester_type': self.harvester_type,
            'status': models.Harvester.STATUS_READY,
            'update_frequency': 60,
            'check_availability_frequency': 30,
            'default_owner': self.user.pk

        }
        self.assertFalse(models.Harvester.objects.filter(name=data["name"]).exists())
        response = self.client.post(reverse('admin:harvesting_harvester_add'), data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # response from admin
        harvester = models.Harvester.objects.get(name=data["name"])
        self.assertEqual(harvester.name, data['name'])
        self.assertEqual(harvester.remote_url, data['remote_url'])
        self.assertEqual(harvester.status, models.Harvester.STATUS_READY)
        self.assertEqual(harvester.remote_available, True)

    @mock.patch(
        "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester.check_availability")
    def test_update_harvester_availability(self, mock_check_availability):
        mock_check_availability.return_value = True
        data = {'action': 'update_harvester_availability',
                '_selected_action': [self.harvester.pk]}
        response = self.client.post(reverse('admin:harvesting_harvester_changelist'), data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # response from admin
        self.harvester.refresh_from_db()
        self.assertEqual(self.harvester.remote_available, True)

    @mock.patch(
        "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester.check_availability")
    def test_perform_harvesting(self, mock_check_availability):
        mock_check_availability.return_value = True
        data = {'action': 'perform_harvesting',
                '_selected_action': [self.harvester.pk]}
        self.harvester.status = models.Harvester.STATUS_READY
        self.harvester.save()

        response = self.client.post(reverse('admin:harvesting_harvester_changelist'), data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # response from admin
        self.harvester.refresh_from_db()
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_PERFORMING_HARVESTING)
