#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode.geoapps.models import GeoApp
from geonode.base.models import TopicCategory
from geonode.resource.manager import resource_manager
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.metadata.manager import metadata_manager
from geonode.base.populate_test_data import all_public, create_models, remove_models


class GeoAppTests(GeoNodeBaseTestSupport):
    """Tests geonode.geoapps module"""

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.bobby = get_user_model().objects.get(username="bobby")
        self.geo_app = resource_manager.create(
            None,
            resource_type=GeoApp,
            defaults=dict(
                title="Testing GeoApp", owner=self.bobby, blob='{"test_data": {"test": ["test_1","test_2","test_3"]}}'
            ),
        )
        self.user = get_user_model().objects.get(username="admin")
        self.geoapp = GeoApp.objects.create(
            name="name", title="geoapp_titlte", thumbnail_url="initial", owner=self.user
        )

    def test_geoapp_category_is_correctly_assigned_in_metadata_upload(self):
        self.client.login(username="admin", password="admin")
        url = reverse("metadata-schema_instance", args=(self.geoapp.id,))

        # assign a category to the GeoApp
        category = TopicCategory.objects.order_by("identifier").first()
        self.geoapp.category = category
        self.geoapp.save()
        # retrieving the new one
        new_category = TopicCategory.objects.order_by("identifier").last()

        payload = metadata_manager.build_schema_instance(self.geoapp)
        payload["category"] = {"id": new_category.identifier}
        response = self.client.put(url, data=payload, content_type="application/json")

        self.geoapp.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_category.identifier, self.geoapp.category.identifier)

    def test_geoapp_copy(self):
        self.client.login(username="admin", password="admin")
        geoapp_copy = None
        try:
            geoapp_copy = resource_manager.copy(self.geoapp, defaults=dict(title="Testing GeoApp 2"))
            self.assertIsNotNone(geoapp_copy)
            self.assertEqual(geoapp_copy.title, "Testing GeoApp 2")
        finally:
            if geoapp_copy:
                geoapp_copy.delete()
            self.assertIsNotNone(self.geoapp)
