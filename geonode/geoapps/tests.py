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
from django.test import override_settings
from django.contrib.auth import get_user_model

from geonode.geoapps.models import GeoApp
from geonode.geoapps.forms import GeoAppForm
from geonode.base.models import TopicCategory
from geonode.resource.manager import resource_manager
from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models)


class GeoAppTests(GeoNodeBaseTestSupport):

    """Tests geonode.geoapps module
    """

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

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
        self.bobby = get_user_model().objects.get(username='bobby')
        self.geo_app = resource_manager.create(
            None,
            resource_type=GeoApp,
            defaults=dict(
                title="Testing GeoApp",
                owner=self.bobby,
                blob='{"test_data": {"test": ["test_1","test_2","test_3"]}}'
            )
        )
        self.user = get_user_model().objects.get(username='admin')
        self.geoapp = GeoApp.objects.create(
            name="name",
            title="geoapp_titlte",
            thumbnail_url='initial',
            owner=self.user
        )
        self.sut = GeoAppForm

    def test_resource_form_is_invalid_extra_metadata_not_json_format(self):
        self.client.login(username="admin", password="admin")
        url = reverse("geoapp_metadata", args=(self.geoapp.id,))
        response = self.client.post(url, data={
            "resource-owner": self.geoapp.owner.id,
            "resource-title": "geoapp_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "not-a-json"
        })
        expected = {"success": False, "errors": ["extra_metadata: The value provided for the Extra metadata field is not a valid JSON"]}
        self.assertDictEqual(expected, response.json())

    @override_settings(EXTRA_METADATA_SCHEMA={"key": "value"})
    def test_resource_form_is_invalid_extra_metadata_not_schema_in_settings(self):
        self.client.login(username="admin", password="admin")
        url = reverse("geoapp_metadata", args=(self.geoapp.id,))
        response = self.client.post(url, data={
            "resource-owner": self.geoapp.owner.id,
            "resource-title": "geoapp_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "[{'key': 'value'}]"
        })
        expected = {"success": False, "errors": ["extra_metadata: EXTRA_METADATA_SCHEMA validation schema is not available for resource geoapp"]}
        self.assertDictEqual(expected, response.json())

    def test_resource_form_is_invalid_extra_metadata_invalids_schema_entry(self):
        self.client.login(username="admin", password="admin")
        url = reverse("geoapp_metadata", args=(self.geoapp.id,))
        response = self.client.post(url, data={
            "resource-owner": self.geoapp.owner.id,
            "resource-title": "geoapp_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": '[{"key": "value"},{"id": "int", "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        expected = "extra_metadata: Missing keys: \'field_label\', \'field_name\', \'field_value\', \'filter_header\' at index 0 "
        self.assertIn(expected, response.json()['errors'][0])

    @override_settings(EXTRA_METADATA_SCHEMA={
        "geoapp": {
            "id": int,
            "filter_header": object,
            "field_name": object,
            "field_label": object,
            "field_value": object
        }
    })
    def test_resource_form_is_valid_extra_metadata(self):
        form = self.sut(data={
            "owner": self.geoapp.owner.id,
            "title": "geoapp_title",
            "date": "2022-01-24 16:38 pm",
            "date_type": "creation",
            "language": "eng",
            "extra_metadata": '[{"id": 1, "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        self.assertTrue(form.is_valid())

    def test_geoapp_category_is_correctly_assigned_in_metadata_upload(self):
        self.client.login(username="admin", password="admin")
        url = reverse("geoapp_metadata", args=(self.geoapp.id,))

        # assign a category to the GeoApp
        category = TopicCategory.objects.order_by('identifier').first()
        self.geoapp.category = category
        self.geoapp.save()
        # retrieving the new one
        new_category = TopicCategory.objects.order_by('identifier').last()

        response = self.client.post(url, data={
            "resource-owner": self.geoapp.owner.id,
            "resource-title": "geoapp_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "category_choice_field": new_category.id,
        })
        self.geoapp.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_category.identifier, self.geoapp.category.identifier)

    def test_geoapp_copy(self):
        self.client.login(username="admin", password="admin")
        geoapp_copy = None
        try:
            geoapp_copy = resource_manager.copy(
                self.geoapp,
                defaults=dict(
                    title="Testing GeoApp 2"
                )
            )
            self.assertIsNotNone(geoapp_copy)
            self.assertEqual(geoapp_copy.title, "Testing GeoApp 2")
        finally:
            if geoapp_copy:
                geoapp_copy.delete()
            self.assertIsNotNone(self.geoapp)
