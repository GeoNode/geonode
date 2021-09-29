import datetime
from django.contrib.auth import get_user_model
from rest_framework import status
from geonode.tests.base import GeoNodeBaseTestSupport

from .. import models


class HarvesterViewSetTestCase(GeoNodeBaseTestSupport):
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

    @classmethod
    def setUpTestData(cls):
        harvester1 = models.Harvester.objects.create(
            remote_url="http://fake1.com",
            name="harvester1",
            default_owner=cls.user,
            harvester_type=cls.harvester_type
        )
        harvester2 = models.Harvester.objects.create(
            remote_url="http://fake2.com",
            name="harvester2",
            default_owner=cls.user,
            harvester_type=cls.harvester_type
        )
        cls.harvesters = [
            harvester1,
            harvester2
        ]

        harvester_resource1 = models.HarvestableResource.objects.create(
            unique_identifier="resource_1",
            title="resource 1",
            harvester=harvester1,
            last_refreshed=datetime.datetime.now()
        )
        harvester_resource2 = models.HarvestableResource.objects.create(
            unique_identifier="resource_2",
            title="resource 2",
            harvester=harvester2,
            last_refreshed=datetime.datetime.now()
        )
        cls.resources = {
            harvester1.id: harvester_resource1,
            harvester2.id: harvester_resource2,
        }

        session1 = models.AsynchronousHarvestingSession.objects.create(
            harvester=harvester1,
            session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING,
            records_done=10
        )
        session2 = models.AsynchronousHarvestingSession.objects.create(
            harvester=harvester2,
            session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING,
            records_done=5
        )
        cls.sessions = [session1, session2]

    def test_get_harvester_list(self):
        response = self.client.get("/api/v2/harvesters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], len(self.harvesters))
        for index, harvester in enumerate(self.harvesters):
            self.assertIn(
                self.harvesters[index].pk,
                [i["id"] for i in response.data["harvesters"]]
            )

            # self.assertEqual(response.data["harvesters"][index]["id"], self.harvesters[index].pk)
            # self.assertEqual(response.data["harvesters"][index]["name"], self.harvesters[index].name)

    def test_post_harvester_list_non_admin(self):
        response = self.client.post('/api/v2/harvesters/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_harvester_detail_for_non_admin(self):
        self.client.logout()
        for index, harvester in enumerate(self.harvesters):
            response = self.client.get(f"/api/v2/harvesters/{harvester.id}/")
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_harvester_detail_for_admin(self):
        self.client.login(username="admin", password="admin")
        for index, harvester in enumerate(self.harvesters):
            response = self.client.get(f"/api/v2/harvesters/{harvester.id}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["harvester"]["id"], harvester.pk)
            self.assertEqual(response.data["harvester"]["name"], harvester.name)

    def test_get_harvester_resources(self):
        for index, harvester in enumerate(self.harvesters):
            response = self.client.get(f"/api/v2/harvesters/{harvester.id}/harvestable-resources/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["harvestable_resources"][0]["unique_identifier"], self.resources[harvester.id].unique_identifier)
            self.assertEqual(response.data["harvestable_resources"][0]["title"], self.resources[harvester.id].title)

    def test_get_harvester_sessions(self):
        response = self.client.get("/api/v2/harvesting-sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], len(self.sessions))
        for index, harvester in enumerate(self.sessions):
            self.assertEqual(response.data["asynchronous_harvesting_sessions"][index]["id"], self.sessions[index].pk)
            self.assertEqual(response.data["asynchronous_harvesting_sessions"][index]["records_done"], self.sessions[index].records_done)
