
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import (
    APIRequestFactory,
    APITestCase,
)


from .. import models


_REQUEST_FACTORY = APIRequestFactory()


class HarvesterViewSetTestCase(APITestCase):
    user = get_user_model().objects.get(username='AnonymousUser')
    harvester_type = "geonode.harvesting.harvesters.geonode.GeonodeLegacyHarvester"

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

    def test_get_harvester_list(self):
        response = self.client.get("/api/v2/harvesters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], len(self.harvesters))
        for index, harvester in enumerate(self.harvesters):
            self.assertEqual(response.data["harvesters"][index]["id"], self.harvesters[index].pk)
            self.assertEqual(response.data["harvesters"][index]["name"], self.harvesters[index].name)
