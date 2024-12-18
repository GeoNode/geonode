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
import json
from unittest.mock import patch, MagicMock
from uuid import uuid4

from django.urls import reverse
from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework import status

from rest_framework.test import APITestCase
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.metadata.manager import metadata_manager
from geonode.metadata.settings import METADATA_HANDLERS
from geonode.base.models import ResourceBase
from geonode.settings import PROJECT_ROOT


class MetadataApiTests(APITestCase):

    def setUp(self):
        # set Json schemas
        self.model_schema = MODEL_SCHEMA
        self.lang = None

        self.test_user_1 = get_user_model().objects.create_user(
            "user_1", "user_1@fakemail.com", "user_1_password", is_active=True
        )
        self.test_user_2 = get_user_model().objects.create_user(
            "user_2", "user_2@fakemail.com", "user_2_password", is_active=True
        )
        self.resource = ResourceBase.objects.create(title="Test Resource", uuid=str(uuid4()), owner=self.test_user_1)
        self.factory = RequestFactory()

        # Setup of the Manager
        with open(os.path.join(PROJECT_ROOT, "metadata/tests/data/fake_schema.json")) as f:
            self.fake_schema = json.load(f)
        
        self.handler1 = MagicMock()
        self.handler2 = MagicMock()
        self.handler3 = MagicMock()

        self.fake_handlers = {
            "fake_handler1": self.handler1,
            "fake_handler2": self.handler2,
            "fake_handler3": self.handler3,
        }

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
        """
        Test schema_instance endpoint with the default lang parameter
        """
        
        mock_build_schema_instance.return_value = {"fake_schema_instance": "schema_instance"}

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, {"fake_schema_instance": "schema_instance"})

        # Ensure the mocked method was called
        mock_build_schema_instance.assert_called()
    
    @patch("geonode.metadata.manager.metadata_manager.build_schema_instance")
    def test_get_schema_instance_with_lang(self, mock_build_schema_instance):
        """
        Test schema_instance endpoint with specific lang parameter
        """
        
        mock_build_schema_instance.return_value = {"fake_schema_instance": "schema_instance"}

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        response = self.client.get(url, {"lang": "it"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, {"fake_schema_instance": "schema_instance"})

        # Ensure the mocked method was called with the correct arguments
        mock_build_schema_instance.assert_called_once_with(self.resource, "it")

    @patch("geonode.metadata.manager.metadata_manager.update_schema_instance")
    def test_put_patch_schema_instance_with_no_errors(self, mock_update_schema_instance):
        """
        Test the success case of PATCH and PUT methods of the schema_instance
        """
        
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
        """
        Test the PATCH and PUT methods of the schema_instance in case of errors
        """
        
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
        """
        Test case that the resource does not exist
        """
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


    #TODO tests for autocomplete views

    # Manager tests

    def test_registry_and_add_handler(self):

        self.assertEqual(set(metadata_manager.handlers.keys()), set(METADATA_HANDLERS.keys()))
        for handler_id in METADATA_HANDLERS.keys():
            self.assertIn(handler_id, metadata_manager.handlers)

    @patch("geonode.metadata.manager.metadata_manager.root_schema", new_callable=lambda: {
        "title": "Test Schema",
        "properties": {
            "field1": {"type": "string"},
            "field2": {"type": "integer", "geonode:required": True},
        },
    })
    @patch("geonode.metadata.manager.metadata_manager._init_schema_context")
    def test_build_schema(self, mock_init_schema_context, mock_root_schema):

        mock_init_schema_context.return_value = {}

        with patch.dict(metadata_manager.handlers, self.fake_handlers, clear=True):

            self.handler1.update_schema.side_effect = lambda schema, context, lang: schema
            self.handler2.update_schema.side_effect = lambda schema, context, lang: schema
            self.handler3.update_schema.side_effect = lambda schema, context, lang: schema

            # Call build_schema
            schema = metadata_manager.build_schema(lang="en")

            self.assertEqual(schema["title"], "Test Schema")
            self.assertIn("field1", schema["properties"])
            self.assertIn("field2", schema["properties"])
            self.assertIn("required", schema)
            self.assertIn("field2", schema["required"])
            self.handler1.update_schema.assert_called()
            self.handler2.update_schema.assert_called()
            self.handler3.update_schema.assert_called()

    @patch("geonode.metadata.manager.metadata_manager.build_schema")
    @patch("cachetools.FIFOCache.get")
    # Mock FIFOCache's __setitem__ method (cache setting)
    @patch("cachetools.FIFOCache.__setitem__")
    def test_get_schema(self, mock_setitem, mock_get, mock_build_schema):

        lang = "en"
        expected_schema = self.fake_schema
        
        # Case when the schema is already in cache
        mock_get.return_value = expected_schema
        result = metadata_manager.get_schema(lang)
        
        # Assert that the schema was retrieved from the cache
        mock_get.assert_called_once_with(str(lang), None)
        mock_build_schema.assert_not_called()
        self.assertEqual(result, expected_schema)

        # Reset mock calls to test the second case
        mock_get.reset_mock()
        mock_build_schema.reset_mock()
        mock_setitem.reset_mock()
        
        # Case when the schema is not in cache
        mock_get.return_value = None
        mock_build_schema.return_value = expected_schema
        result = metadata_manager.get_schema(lang)

        mock_get.assert_called_once_with(str(lang), None)
        mock_build_schema.assert_called_once_with(lang)
        mock_setitem.assert_called_once_with(str(lang), expected_schema)
        self.assertEqual(result, expected_schema)

    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_build_schema_instance_no_errors(self, mock_get_schema):

        self.lang = "en"
        mock_get_schema.return_value = self.fake_schema
        
        with patch.dict(metadata_manager.handlers, self.fake_handlers, clear=True):

            self.handler1.get_jsonschema_instance.return_value = {"data from fake handler 1"}
            self.handler2.get_jsonschema_instance.return_value = {"data from fake handler 2"}
            self.handler3.get_jsonschema_instance.return_value = {"data from fake handler 3"}
        
            # Call the method
            instance = metadata_manager.build_schema_instance(self.resource, self.lang)
        
            # Assert that the handlers were called and instance was built correctly
            self.handler1.get_jsonschema_instance.assert_called_once_with(self.resource, "field1", {}, {}, self.lang)
            self.handler2.get_jsonschema_instance.assert_called_once_with(self.resource, "field2", {}, {}, self.lang)
            self.handler3.get_jsonschema_instance.assert_called_once_with(self.resource, "field3", {}, {}, self.lang)
        
            self.assertEqual(instance["field1"], {"data from fake handler 1"})
            self.assertEqual(instance["field2"], {"data from fake handler 2"})
            self.assertEqual(instance["field3"], {"data from fake handler 3"})
            self.assertNotIn("extraErrors", instance)

    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_update_schema_instance_no_errors(self, mock_get_schema):
        
        # json_instance is the payload from the client.
        # In this test is used only to call the update_schema_instance
        json_instance = {"field1": "new_value1", "new_field2": "new_value2"}
        
        mock_get_schema.return_value = self.fake_schema
        # Mock the save method
        self.resource.save = MagicMock()
        
        with patch.dict(metadata_manager.handlers, self.fake_handlers, clear=True):
        
            # Simulate successful handler behavior
            self.handler1.update_resource.return_value = None
            self.handler2.update_resource.return_value = None
            self.handler3.update_resource.return_value = None
        
            # Call the update_schema_instance method
            errors = metadata_manager.update_schema_instance(self.resource, json_instance)
        
            # Assert that handlers were called to update the resource with the correct data
            self.handler1.update_resource.assert_called_once_with(self.resource, "field1", json_instance, {}, {})
            self.handler2.update_resource.assert_called_once_with(self.resource, "field2", json_instance, {}, {})
            self.handler3.update_resource.assert_called_once_with(self.resource, "field3", json_instance, {}, {})
        
            # Assert no errors were raised
            self.assertEqual(errors, {})
        
            # Check that resource.save() is called
            self.resource.save.assert_called_once()

            # Assert that there were no extra errors in the response
            self.assertNotIn("extraErrors", errors)

    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_update_schema_instance_with_handler_error(self, mock_get_schema):
        
        # json_instance is the payload from the client.
        # In this test is used only to call the update_schema_instance
        json_instance = {}

        mock_get_schema.return_value = self.fake_schema

        # Mock the save method
        self.resource.save = MagicMock()

        with patch.dict(metadata_manager.handlers, self.fake_handlers, clear=True):

            # Simulate an error in update_resource for handler2
            self.handler1.update_resource.side_effect = None
            self.handler2.update_resource.side_effect = Exception("Error in handler2")
            self.handler3.update_resource.side_effect = None

            # Call the method under test
            errors = metadata_manager.update_schema_instance(self.resource, json_instance)

            # Assert that update_resource was called for each handler
            self.handler1.update_resource.assert_called()
            self.handler2.update_resource.assert_called()
            self.handler3.update_resource.assert_called()

            # Assert that resource.save() was called
            self.resource.save.assert_called_once()

            # Verify that errors are collected for handler2
            self.assertIn("field2", errors)
            self.assertEqual(
                errors["field2"]["__errors"],
                ["Error while processing this field: Error in handler2"]
            )

            # Verify that no other errors were added for handler1 and handler3
            self.assertNotIn("field1", errors)
            self.assertNotIn("field3", errors)

    
    @patch("geonode.metadata.manager.metadata_manager.get_schema")
    def test_update_schema_instance_with_db_error(self, mock_get_schema):
        
        # json_instance is the payload from the client.
        # In this test is used only to call the update_schema_instance
        json_instance = {}

        mock_get_schema.return_value = self.fake_schema

        # Mock save method with an exception
        self.resource.save = MagicMock(side_effect=Exception("Error during the resource save"))
        
        with patch.dict(metadata_manager.handlers, self.fake_handlers, clear=True):

            self.handler1.update_resource.side_effect = None
            self.handler2.update_resource.side_effect = None
            self.handler3.update_resource.side_effect = None

            # Call the method under test
            errors = metadata_manager.update_schema_instance(self.resource, json_instance)

            # Assert that update_resource was called for each handler
            self.handler1.update_resource.assert_called()
            self.handler2.update_resource.assert_called()
            self.handler3.update_resource.assert_called()

            # Assert that save raised an error and was recorded
            self.resource.save.assert_called_once()
            self.assertIn("__errors", errors)
            self.assertEqual(errors["__errors"], ["Error while saving the resource: Error during the resource save"])