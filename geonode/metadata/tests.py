#########################################################################
#
# Copyright (C) 2024 OSGeo
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

import os
import logging
import shutil
import io
import json
from unittest.mock import patch
from uuid import uuid4

from django.urls import reverse
from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
from rest_framework import status

from rest_framework.test import APITestCase
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.settings import PROJECT_ROOT
from geonode.metadata.manager import metadata_manager
from geonode.metadata.settings import METADATA_HANDLERS
from geonode.base.models import ResourceBase


class MetadataApiTests(APITestCase):

    def setUp(self):
        # set Json schemas
        self.model_schema = MODEL_SCHEMA
        self.lang = None

        self.context = metadata_manager._init_schema_context(self.lang)
        
        self.handlers = {}
        for handler_id, module_path in METADATA_HANDLERS.items():
            handler_cls = import_string(module_path)
            self.handlers[handler_id] = handler_cls()

        self.test_user = get_user_model().objects.create_user(
            "someuser", "someuser@fakemail.com", "somepassword", is_active=True
        )
        self.resource = ResourceBase.objects.create(title="Test Resource", uuid=str(uuid4()), owner=self.test_user)

    def tearDown(self):
        super().tearDown()

    # tests for the encpoint metadata/schema
    def test_schema_valid_structure(self):
        """
        Ensure the returned basic structure of the schema
        """

        url = reverse('metadata-schema')
        
        # Make a GET request to the action
        response = self.client.get(url, format="json")

        # Assert that the response is in JSON format
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check that the response status code is 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the structure of the schema
        response_data = response.json()
        for field in self.model_schema.keys():
            self.assertIn(field, response_data)

    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_schema_not_found(self, mock_get_schema):
        """
        Test the behaviour of the schema endpoint 
        if the schema is not found
        """
        mock_get_schema.return_value = None

        url = reverse("metadata-schema")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"Message": "Schema not found"})

    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_schema_with_lang(self, mock_get_schema):
        """
        Test that the view recieves the lang parameter
        """
        mock_get_schema.return_value = {"fake_schema": "schema"}

        url = reverse("metadata-schema")
        response = self.client.get(url, {"lang": "it"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"fake_schema": "schema"})

        # Verify that get_schema was called with the correct lang
        mock_get_schema.assert_called_once_with("it")

    @patch("geonode.metadata.manager.metadata_manager.build_schema_instance")
    def test_get_schema_instance_with_default_lang(self, mock_build_schema_instance):
        
        mock_build_schema_instance.return_value = {"fake_schema_instance": "schema_instance"}

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, {"fake_schema_instance": "schema_instance"})

        # Ensure the mocked method was called
        mock_build_schema_instance.assert_called()
    
    @patch("geonode.metadata.manager.metadata_manager.build_schema_instance")
    def test_get_schema_instance_with_lang(self, mock_build_schema_instance):
        
        mock_build_schema_instance.return_value = {"fake_schema_instance": "schema_instance"}

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        response = self.client.get(url, {"lang": "it"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, {"fake_schema_instance": "schema_instance"})

        # Ensure the mocked method was called with the correct arguments
        mock_build_schema_instance.assert_called_once_with(self.resource, "it")

    @patch("geonode.metadata.manager.metadata_manager.update_schema_instance")
    def test_put_patch_schema_instance_with_no_errors(self, mock_update_schema_instance):
        
        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        fake_payload = {"field": "value"}

        # set the returned value of the mocked update_schema_instance with an empty dict
        errors = {}
        mock_update_schema_instance.return_value = errors

        methods = [self.client.put, self.client.patch]
        
        for method in methods:

            response = method(url, data=fake_payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertJSONEqual(
                response.content,
                {"message": "The resource was updated successfully", "extraErrors": errors}
            )
            mock_update_schema_instance.assert_called_with(self.resource, fake_payload)

    @patch("geonode.metadata.manager.metadata_manager.update_schema_instance")
    def test_put_patch_schema_instance_with_errors(self, mock_update_schema_instance):
        
        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        fake_payload = {"field": "value"}

        # Set fake errors
        errors = {
            "fake_error_1": "Field 'title' is required",
            "fake_error_2": "Invalid value for 'type'"
            }
        mock_update_schema_instance.return_value = errors

        methods = [self.client.put, self.client.patch]
        
        for method in methods:

            response = method(url, data=fake_payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertJSONEqual(
                response.content,
                {"message": "Some errors were found while updating the resource", "extraErrors": errors}
            )
            mock_update_schema_instance.assert_called_with(self.resource, fake_payload)

    def test_resource_not_found(self):
        # Define a fake primary key
        fake_pk = 1000

        # Construct the URL for the action
        url = reverse("metadata-schema_instance", kwargs={"pk": fake_pk})

        # Perform a GET request
        response = self.client.get(url)

        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertJSONEqual(
            response.content,
            {"message": "The dataset was not found"}
        )
    

    