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

from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from geonode.geoapps.forms import GeoAppForm

from geonode.geoapps.models import GeoApp
from geonode.tests.base import GeoNodeBaseTestSupport


class TestGeoAppViews(GeoNodeBaseTestSupport):

    def setUp(self) -> None:
        self.user = get_user_model().objects.get(username='admin')
        self.geoapp = GeoApp.objects.create(
            uuid=str(uuid4()),
            name="name",
            title="geoapp_titlte",
            thumbnail_url='initial',
            owner=self.user)
        self.sut = GeoAppForm

    def test_update_geoapp_metadata(self):
        bobby = get_user_model().objects.get(username='admin')
        gep_app = GeoApp.objects.create(
            uuid=str(uuid4()),
            title="App",
            thumbnail_url='initial',
            owner=bobby)
        gep_app.set_default_permissions()
        url = reverse('geoapp_metadata', args=(gep_app.id,))
        data = {
            'resource-title': 'New title',
            'resource-owner': bobby.id,
            'resource-date': '2021-10-27 05:59 am',
            "resource-date_type": 'publication',
            'resource-language': gep_app.language
        }
        self.client.login(username=bobby.username, password='admin')
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(gep_app.thumbnail_url, GeoApp.objects.get(id=gep_app.id).thumbnail_url)
        self.assertEqual(GeoApp.objects.get(id=gep_app.id).title, 'New title')
        #   Check uuid is populate
        self.assertTrue(GeoApp.objects.get(id=gep_app.id).uuid)

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
