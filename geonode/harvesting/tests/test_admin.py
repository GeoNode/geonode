from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework import status

from geonode.tests.base import GeoNodeBaseTestSupport

from .. import admin, models


class HarvesterAdminTestCase(GeoNodeBaseTestSupport):
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker"

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.get(username="admin")
        self.client.login(username="admin", password="admin")

        self.harvester = models.Harvester.objects.create(
            remote_url="http://fake1.com",
            name="harvester1",
            default_owner=self.user,
            harvester_type=self.harvester_type,
        )

    def test_get_form_returns_current_user(self):
        request = self.factory.post(reverse("admin:harvesting_harvester_add"))
        request.user = self.user
        model_admin = admin.HarvesterAdmin(model=models.Harvester, admin_site=AdminSite())
        form = model_admin.get_form(request)
        self.assertEqual(form.base_fields["default_owner"].initial.username, self.user.username)

    def test_add_harvester(self):
        data = {
            "name": "harvester",
            "remote_url": "http://fake.com",
            "harvesting_session_update_frequency": 60,
            "refresh_harvestable_resources_update_frequency": 30,
            "check_availability_frequency": 10,
            "harvester_type_specific_configuration": "{}",
            "harvester_type": self.harvester_type,
            "status": models.Harvester.STATUS_READY,
            "default_owner": self.user.pk,
        }
        self.assertFalse(models.Harvester.objects.filter(name=data["name"]).exists())
        response = self.client.post(reverse("admin:harvesting_harvester_add"), data)
        print(f"response: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # response from admin
        harvester = models.Harvester.objects.get(name=data["name"])
        self.assertEqual(harvester.name, data["name"])
        self.assertEqual(harvester.remote_url, data["remote_url"])
        self.assertEqual(harvester.status, models.Harvester.STATUS_READY)

    def test_update_harvester_availability(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.update_harvester_availability(None, [mock_harvester])
            mock_harvester.update_availability.assert_called()

    def test_initiate_update_harvestable_resources_initiates_when_harvester_is_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = True
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_update_harvestable_resources(None, [mock_harvester])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_update_harvestable_resources.assert_called()

    def test_initiate_update_harvestable_resources_skips_when_harvester_not_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = False
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_update_harvestable_resources(None, [mock_harvester])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_update_harvestable_resources.assert_not_called()

    def test_initiate_perform_harvesting_initiates_when_harvester_is_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = True
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_perform_harvesting(None, [mock_harvester])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_perform_harvesting.assert_called()

    def test_initiate_perform_harvesting_skips_when_harvester_not_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = False
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_perform_harvesting(None, [mock_harvester])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_perform_harvesting.assert_not_called()

    def test_reset_harvester_status(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.status = models.Harvester.STATUS_PERFORMING_HARVESTING
        model_admin = admin.HarvesterAdmin(model=mock_harvester, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.reset_harvester_status(None, [mock_harvester])
            self.assertEqual(mock_harvester.status, models.Harvester.STATUS_READY)
            mock_harvester.save.assert_called()


class AsynchronousHarvestingSessionAdminTestCase(GeoNodeBaseTestSupport):
    def test_django_admin_does_not_allow_creating_new_session(self):
        data = {"session_type": "harvesting", "harvester": 1000, "status": "pending"}
        response = self.client.post(reverse("admin:harvesting_harvester_add"), data, follow=True)
        print(response.redirect_chain)
        self.assertRedirects(response, "/en-us/admin/login/?next=/en-us/admin/harvesting/harvester/add/")


class HarvestableResourceAdminTestCase(GeoNodeBaseTestSupport):
    def test_initiate_harvest_selected_resources_initiates_when_harvester_is_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = True
        fake_resource_id = 1000
        mock_resource = mock.MagicMock(spec=models.HarvestableResource, harvester=mock_harvester, id=fake_resource_id)
        model_admin = admin.HarvestableResourceAdmin(model=mock_resource, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_harvest_selected_resources(None, [mock_resource])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_perform_harvesting.assert_called_with([fake_resource_id])

    def test_initiate_harvest_selected_resources_skips_when_harvester_not_available(self):
        mock_harvester_model = mock.MagicMock(spec=models.Harvester)
        mock_harvester = mock_harvester_model.return_value
        mock_harvester.update_availability.return_value = False
        fake_resource_id = 1000
        mock_resource = mock.MagicMock(spec=models.HarvestableResource, harvester=mock_harvester, id=fake_resource_id)
        model_admin = admin.HarvestableResourceAdmin(model=mock_resource, admin_site=AdminSite())
        with mock.patch.object(model_admin, "message_user"):
            model_admin.initiate_harvest_selected_resources(None, [mock_resource])
            mock_harvester.update_availability.assert_called()
            mock_harvester.initiate_perform_harvesting.assert_not_called()
