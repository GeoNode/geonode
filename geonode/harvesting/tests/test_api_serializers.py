from unittest import mock
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from rest_framework.test import (
    APIRequestFactory,
)

from geonode.tests.base import GeoNodeBaseTestSupport

from .. import models
from ..api import serializers


_REQUEST_FACTORY = APIRequestFactory()


class BriefHarvesterSerializerTestCase(GeoNodeBaseTestSupport):
    remote_url = "test.com"
    name = "This is geonode harvester"
    user = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker"

    @classmethod
    def setUpTestData(cls):
        cls.harvester = models.Harvester.objects.create(
            remote_url=cls.remote_url, name=cls.name, default_owner=cls.user, harvester_type=cls.harvester_type
        )

    def test_serializer_is_able_to_serialize_model_instance(self):
        api_endpoint = "/api/v2/harvesters/"
        request = _REQUEST_FACTORY.get(api_endpoint)
        serializer = serializers.BriefHarvesterSerializer(self.harvester, context={"request": request})
        serialized = serializer.data
        self.assertEqual(serialized["remote_url"], self.harvester.remote_url)
        self.assertEqual(serialized["name"], self.harvester.name)
        self.assertEqual(urlparse(serialized["links"]["self"]).path, f"{api_endpoint}{self.harvester.pk}/")
        self.assertIsNotNone(serialized["links"]["harvestable_resources"])


class HarvesterSerializerTestCase(GeoNodeBaseTestSupport):
    remote_url = "test.com"
    name = "This is geonode harvester"
    user = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker"

    @classmethod
    def setUpTestData(cls):
        cls.harvester = models.Harvester.objects.create(
            remote_url=cls.remote_url, name=cls.name, default_owner=cls.user, harvester_type=cls.harvester_type
        )

    def test_serializer_is_able_to_serialize_model_instance(self):
        api_endpoint = "/api/v2/harvesters/"
        request = _REQUEST_FACTORY.get(api_endpoint)
        serializer = serializers.BriefHarvesterSerializer(self.harvester, context={"request": request})
        serialized = serializer.data
        self.assertEqual(serialized["remote_url"], self.harvester.remote_url)
        self.assertEqual(serialized["name"], self.harvester.name)
        self.assertEqual(urlparse(serialized["links"]["self"]).path, f"{api_endpoint}{self.harvester.pk}/")
        self.assertIsNotNone(serialized["links"]["harvestable_resources"])

    @mock.patch("geonode.harvesting.models.validate_worker_configuration")
    def test_validate_also_validates_worker_specific_config(self, mock_validate_config):
        input_data = {
            "name": "phony",
            "remote_url": "http://fake.com",
            "user": 1,
            "harvester_type": "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker",
            "harvester_type_specific_configuration": {"something": "fake config"},
        }

        request = _REQUEST_FACTORY.post("/api/v2/harvesters/")
        request.user = self.user

        serializer = serializers.HarvesterSerializer(data=input_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        mock_validate_config.assert_called()

    def test_validate_does_not_allow_changing_status_and_worker_specific_config(self):
        input_data = {
            "name": "phony",
            "remote_url": "http://fake.com",
            "user": 1,
            "harvester_type_specific_configuration": {"something": "fake config"},
            "status": "updating-harvestable-resources",
        }

        request = _REQUEST_FACTORY.post("/api/v2/harvesters/")
        request.user = self.user

        serializer = serializers.HarvesterSerializer(data=input_data, context={"request": request})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_does_not_allow_setting_custom_status(self):
        input_data = {
            "name": "phony",
            "remote_url": "http://fake.com",
            "user": 1,
            "status": "updating-harvestable-resources",
        }

        request = _REQUEST_FACTORY.post("/api/v2/harvesters/")
        request.user = self.user

        serializer = serializers.HarvesterSerializer(data=input_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save()

    def test_create(self):
        input_data = {
            "name": "phony",
            "remote_url": "http://fake.com",
            "user": 1,
        }
        request = _REQUEST_FACTORY.post("/api/v2/harvesters/")
        request.user = self.user

        serializer = serializers.HarvesterSerializer(data=input_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        harvester = serializer.save()
        self.assertEqual(harvester.name, input_data["name"])

    def test_update_errors_out_if_current_status_is_not_ready(self):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"status": "updating-harvestable-resources"},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.harvester.status = models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
        self.harvester.save()
        with self.assertRaises(ValidationError):
            serializer.save()

    def test_update_errors_out_when_client_tries_to_set_status_ready(self):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"status": models.Harvester.STATUS_READY},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            serializer.save()

    @mock.patch("geonode.harvesting.api.serializers.tasks")
    def test_update_calls_update_harvestable_resources_task(self, mock_tasks):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"status": models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mock_tasks.update_harvestable_resources.signature.assert_called()
        mock_tasks.update_harvestable_resources.signature.return_value.apply_async.assert_called()

    @mock.patch("geonode.harvesting.api.serializers.tasks")
    def test_update_calls_harvesting_dispatcher_task(self, mock_tasks):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"status": models.Harvester.STATUS_PERFORMING_HARVESTING},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        called_args = mock_tasks.harvesting_dispatcher.signature.call_args_list[0].kwargs["args"]
        called_session_pk = called_args[0]
        session = models.AsynchronousHarvestingSession.objects.get(pk=called_session_pk)
        self.assertEqual(session.harvester.pk, self.harvester.pk)
        mock_tasks.harvesting_dispatcher.signature.return_value.apply_async.assert_called()

    @mock.patch("geonode.harvesting.api.serializers.tasks")
    def test_update_calls_update_harvester_availability_task(self, mock_tasks):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"status": models.Harvester.STATUS_CHECKING_AVAILABILITY},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mock_tasks.check_harvester_available.signature.assert_called_with(args=(self.harvester.pk,))
        mock_tasks.check_harvester_available.signature.return_value.apply_async.assert_called()

    @mock.patch("geonode.harvesting.api.serializers.tasks")
    def test_update_updates_harvestable_resources_whenever_worker_config_changes(self, mock_tasks):
        request = _REQUEST_FACTORY.patch(f"/api/v2/harvesters/{self.harvester.pk}")
        self.assertEqual(self.harvester.status, models.Harvester.STATUS_READY)
        self.assertEqual(len(self.harvester.harvester_type_specific_configuration), 0)
        serializer = serializers.HarvesterSerializer(
            self.harvester,
            data={"harvester_type_specific_configuration": {"harvest_datasets": False}},
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mock_tasks.update_harvestable_resources.signature.assert_called_with(args=(self.harvester.pk,))
        mock_tasks.update_harvestable_resources.signature.return_value.apply_async.assert_called()


class BriefAsynchronousHarvestingSessionSerializerTestCase(GeoNodeBaseTestSupport):
    harvester: models.Harvester

    @classmethod
    def setUpTestData(cls):
        remote_url = "test.com"
        name = "This is geonode harvester"
        user = get_user_model().objects.get(username="AnonymousUser")
        harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker"
        cls.harvester = models.Harvester.objects.create(
            remote_url=remote_url, name=name, default_owner=user, harvester_type=harvester_type
        )
        cls.harvesting_session = models.AsynchronousHarvestingSession.objects.create(
            harvester=cls.harvester, session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING
        )

    def test_serializer_is_able_to_serialize_model_instance(self):
        api_endpoint = "/api/v2/harvesting-sessions/"
        request = _REQUEST_FACTORY.get(api_endpoint)
        serializer = serializers.BriefAsynchronousHarvestingSessionSerializer(
            self.harvesting_session, context={"request": request}
        )
        serialized = serializer.data
        self.assertIsNotNone(serialized["started"])


class HarvestableResourceSerializerTestCase(GeoNodeBaseTestSupport):
    unique_identifier = "some-identifier"
    title = "something"
    remote_resource_type = "documents"
    default_should_be_harvested = False

    @classmethod
    def setUpTestData(cls):
        cls.harvester = models.Harvester.objects.create(
            remote_url="test.com",
            name="This is geonode harvester",
            default_owner=get_user_model().objects.get(username="AnonymousUser"),
            harvester_type="geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker",
        )
        cls.harvestable_resource = models.HarvestableResource.objects.create(
            unique_identifier=cls.unique_identifier,
            title=cls.title,
            harvester=cls.harvester,
            should_be_harvested=cls.default_should_be_harvested,
            remote_resource_type=cls.remote_resource_type,
            last_refreshed=now(),
        )

    def test_serializer_is_able_to_serialize_model_instance(self):
        api_endpoint = f"/api/v2/harvesters/{self.harvester.id}/harvestable-resources/"
        request = _REQUEST_FACTORY.get(api_endpoint)
        serializer = serializers.HarvestableResourceSerializer(self.harvestable_resource, context={"request": request})
        serialized = serializer.data
        self.assertIsNotNone(serialized["unique_identifier"], self.unique_identifier)
        self.assertIsNotNone(serialized["title"], self.title)
        self.assertIsNotNone(serialized["remote_resource_type"], self.remote_resource_type)
        self.assertIsNotNone(serialized["should_be_harvested"], self.default_should_be_harvested)

    def test_serializer_is_allowed_to_change_instance_should_be_harvested_attribute(self):
        self.assertEqual(self.harvestable_resource.should_be_harvested, self.default_should_be_harvested)
        api_endpoint = f"/api/v2/harvesters/{self.harvester.id}/harvestable-resources/"
        request = _REQUEST_FACTORY.patch(api_endpoint)
        serializer = serializers.HarvestableResourceSerializer(
            data={
                "unique_identifier": self.unique_identifier,
                "should_be_harvested": not self.default_should_be_harvested,
            },
            context={
                "request": request,
                "harvester": self.harvester,
            },
        )
        serializer.is_valid(raise_exception=True)
        print(f"validated_data: {serializer.validated_data}")
        serializer.save()
        self.harvestable_resource.refresh_from_db()
        self.assertEqual(self.harvestable_resource.should_be_harvested, not self.default_should_be_harvested)
