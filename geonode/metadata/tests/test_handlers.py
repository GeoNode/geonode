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
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils.translation import gettext as _

from django.test.testcases import TestCase
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.base.models import (
    ResourceBase, 
    TopicCategory,
    RestrictionCodeType,
    License,
    SpatialRepresentationType,
    Region,
    LinkedResource
)
from geonode.settings import PROJECT_ROOT
from geonode.metadata.handlers.base import (
    BaseHandler, 
    CategorySubHandler,
    DateTypeSubHandler,
    DateSubHandler,
    FrequencySubHandler,
    LanguageSubHandler,
    LicenseSubHandler,
    RestrictionsSubHandler,
    SpatialRepresentationTypeSubHandler,
)
from geonode.metadata.handlers.region import RegionHandler
from geonode.metadata.handlers.linkedresource import LinkedResourceHandler
from geonode.tests.base import GeoNodeBaseTestSupport

class HandlersTests(GeoNodeBaseTestSupport):

    def setUp(self):
        # set Json schemas
        self.model_schema = MODEL_SCHEMA
        self.lang = None
        self.errors = {}
        self.context = MagicMock()

        self.test_user_1 = get_user_model().objects.create_user(
            "user_1", "user_1@fakemail.com", "user_1_password", is_active=True
        )
        
        # Testing database setup
        self.resource = ResourceBase.objects.create(title="Test Resource", uuid=str(uuid4()), owner=self.test_user_1)
        self.extra_resource_1 = ResourceBase.objects.create(title="Extra resource 1", uuid=str(uuid4()), owner=self.test_user_1)
        self.extra_resource_2 = ResourceBase.objects.create(title="Extra resource 2", uuid=str(uuid4()), owner=self.test_user_1)
        self.extra_resource_3 = ResourceBase.objects.create(title="Extra resource 3", uuid=str(uuid4()), owner=self.test_user_1)
        
        self.category = TopicCategory.objects.create(identifier="fake_category", gn_description="a fake gn description", description="a detailed description")
        self.license = License.objects.create(identifier="fake_license", name="a fake name", description="a detailed description")
        self.restrictions = RestrictionCodeType.objects.create(identifier="fake_restrictions", description="a detailed description")
        self.spatial_repr = SpatialRepresentationType.objects.create(identifier="fake_spatial_repr", description="a detailed description")
        
        self.factory = RequestFactory()

        # Fake base schema path
        self.fake_base_schema_path = os.path.join(PROJECT_ROOT, "metadata/tests/data/fake_base_schema.json")
        
        # Load fake base schema
        with open(self.fake_base_schema_path) as f:
            self.fake_base_schema = json.load(f)

        # Load a mocked schema
        # Setup of the Manager
        with open(os.path.join(PROJECT_ROOT, "metadata/tests/data/fake_schema.json")) as f:
            self.fake_schema = json.load(f)

        # Handlers
        self.base_handler = BaseHandler()
        self.region_handler = RegionHandler()
        self.linkedresource_handler = LinkedResourceHandler()

        # A fake subschema
        self.fake_subschema = {
            "type": "string",
            "title": "new field",
            "description": "A new field was added",
            "maxLength": 255
            }

    def tearDown(self):
        super().tearDown()

    
    # Tests for the Base handler
    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_base_handler_update_schema(self, mock_subhandlers):
        
        """
        Ensure that the update_schema method gets a simple valid schema and 
        populate it with the base_schema properties accordignly
        """

        self.base_handler.json_base_schema = self.fake_base_schema_path

        # Model schema definition
        jsonschema = self.model_schema

        # Mock subhandlers and update_subschema functionality, which
        # will be used for the field "date"
        field_name = "date"
        mock_subhandlers[field_name] = MagicMock()
        mock_subhandlers[field_name].update_subschema = MagicMock()

        def mock_update_subschema(subschema, lang=None):
            subschema["oneOf"] = [
                {"const": "fake const", "title": "fake title"}
            ]
        
        # Add the mock behavior for update_subschema
        mock_subhandlers[field_name].update_subschema.side_effect = mock_update_subschema

        # Call the method
        updated_schema = self.base_handler.update_schema(jsonschema, self.context, self.lang)

        # Check the full base schema
        for field in self.fake_base_schema:
            self.assertIn(field, updated_schema["properties"])

        # Check subhandler execution for the field name "date"
        self.assertEqual(updated_schema["properties"]["date"].get("oneOf"), [{"const": "fake const", "title": "fake title"}])
        self.assertNotIn("oneOf", updated_schema["properties"]["uuid"])
        self.assertNotIn("oneOf", updated_schema["properties"]["title"])
        self.assertNotIn("oneOf", updated_schema["properties"]["abstract"])

        # Check geonode:handler addition
        self.assertEqual(updated_schema["properties"]["abstract"].get("geonode:handler"), "base")
        self.assertEqual(updated_schema["properties"]["date"].get("geonode:handler"), "base")

    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_base_handler_get_jsonschema_instance_without_subhandlers(self, mock_subhandlers):

        """
        Ensure that the get_json_schema_instance will get the db value 
        from a simple field
        """
        
        field_name = "title"
        self.assertTrue(hasattr(self.resource, field_name), f"Field '{field_name}' does not exist.")
        expected_field_value = self.resource.title

        # Call the method
        field_value = self.base_handler.get_jsonschema_instance(self.resource, field_name, self.context, self.errors, lang=None)

        # Ensure that the serialize method was not called
        mock_subhandlers.get(field_name, MagicMock()).serialize.assert_not_called()
        self.assertEqual(expected_field_value, field_value)
        self.assertEqual(self.errors, {})

    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_base_handler_get_jsonschema_instance_with_subhandlers(self, mock_subhandlers):
        
        """
        Ensure that when a field name corresponds to a model in th ResourceBase,
        the get_jsonschema_instance method gets a field_value which is a model
        and assign it to the corresponding value. For testing we use the "category 
        field"
        """
        
        field_name = "category"
        
        # Create a fake resource
        fake_resource = MagicMock()
        
        fake_resource.category = MagicMock()
        fake_resource.category.identifier = "mocked_category_value"
        expected_field_value = fake_resource.category.identifier 

        # Add a SUBHANDLER for the field that returns the MagicMock model
        mock_subhandlers[field_name] = MagicMock()
        mock_subhandlers[field_name].serialize.return_value = expected_field_value

        # Call the method
        field_value = self.base_handler.get_jsonschema_instance(
            resource=fake_resource,
            field_name=field_name,
            context=self.context,
            errors=self.errors,
            lang=self.lang
            )
        
        # Ensure that the serialize method has been called once
        mock_subhandlers[field_name].serialize.assert_called_once_with(fake_resource.category)
        self.assertEqual(expected_field_value, field_value)

    
    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_update_resource_success_without_subhandlers(self, mock_subhandlers):

        """
        Ensure that when a simple field name like title is set to the resource
        without calling the SUBHANDLERS classes
        """
        field_name = "title"
        expected_field_value = "new_fake_title_value"
        json_instance = {field_name: expected_field_value}

        # Call the method
        self.base_handler.update_resource(
            resource=self.resource,
            field_name=field_name,
            json_instance=json_instance,
            context=self.context,
            errors=self.errors
        )
 
        # Ensure that the deserialize method was not called
        mock_subhandlers.get(field_name, MagicMock()).deserialize.assert_not_called()
        self.assertEqual(expected_field_value, self.resource.title)
    

    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_update_resource_success_with_subhandlers(self, mock_subhandlers):

        """
        Ensure that when a field name corresponds to a model in th ResourceBase,
        the update_resource method receives a field_value and assign it to the 
        corresponding model. For testing we use the "category field"
        """
        field_name = "category"
        field_value = "new_category_value"
        json_instance = {field_name: field_value}

        # Fake resource object
        fake_resource = MagicMock()

        # Simulate a MagicMock model for category
        mock_category_model = MagicMock()
        mock_category_model.identifier = field_value

        # Add a SUBHANDLER for the field that returns the MagicMock model
        mock_subhandlers[field_name] = MagicMock()
        mock_subhandlers[field_name].deserialize.return_value = mock_category_model

        # Call the method
        self.base_handler.update_resource(
            resource=fake_resource,
            field_name=field_name,
            json_instance=json_instance,
            context=self.context,
            errors=self.errors
        )

        mock_subhandlers[field_name].deserialize.assert_called_once_with(field_value)
        self.assertEqual(fake_resource.category, mock_category_model)
  
    
    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    @patch("geonode.metadata.handlers.base.logger")
    def test_update_resource_exception_handling(self, mock_logger, mock_subhandlers):
        """
        Handling exception
        """
        field_name = "category"
        field_value = "new_category_value"
        json_instance = {field_name: field_value}

        # Fake resource object
        fake_resource = MagicMock()

        # Add a SUBHANDLER for the field that raises an exception during deserialization
        mock_subhandlers[field_name] = MagicMock()
        mock_subhandlers[field_name].deserialize.side_effect = Exception("Deserialization error")

        # Call the method
        self.base_handler.update_resource(
            resource=fake_resource,
            field_name=field_name,
            json_instance=json_instance,
            context=self.context,
            errors=self.errors
        )

        mock_subhandlers[field_name].deserialize.assert_called_once_with(field_value)

        # Ensure that the exception is logged
        mock_logger.warning.assert_called_once_with(
        f"Error setting field {field_name}={field_value}: Deserialization error"
        )
    
    # Tests for subhandler classes of the base handler
    @patch('geonode.metadata.handlers.base.reverse')
    def test_category_subhandler_update_subschema(self,  mocked_endpoint):

        """ 
        Test for the update_subschema of the CategorySubHandler.
        An instance of this model has been created initial setup
        """
        
        mocked_endpoint.return_value = "/mocked_url"

        subschema = {
          "type": "string",
          "title": "Category",
          "description": "a fake description",
          "maxLength": 255
        }
        
        # Call the update_subschema method with the real database data
        CategorySubHandler.update_subschema(subschema, lang='en')

        # Assert changes to the subschema
        self.assertIn("ui:options", subschema)
        self.assertIn("geonode-ui:autocomplete", subschema["ui:options"])
        self.assertEqual(subschema["ui:options"]["geonode-ui:autocomplete"], mocked_endpoint.return_value)

    
    def test_category_subhandler_serialize_with_existed_db_value(self):
        
        """
        Test the serialize method with existed db value.
        An instance of this model has been created initial setup
        """
        
        # Test the case where the db_value is a model instance
        serialized_value = CategorySubHandler.serialize(self.category)

        expected_value = {"id": self.category.identifier, "label": _(self.category.gn_description)}
        
        self.assertEqual(serialized_value, expected_value)
        
        # Assert that the serialize method returns the identifier
        self.assertEqual(serialized_value["id"], self.category.identifier)

    
    def test_category_subhandler_serialize_invalid_data(self):
        
        """
        Test the serialize method with invalid db value.
        An instance of this model has been created initial setup
        """
        
        # Test the case where the db_value is not a model instance
        non_category_value = "nonexistent value"
        
        invalid_serialized_value_1 = CategorySubHandler.serialize(non_category_value)
        invalid_serialized_value_2 = CategorySubHandler.serialize(None)

        # Assert that the serialize method returns the input value unchanged
        self.assertIsNone(invalid_serialized_value_1)
        self.assertIsNone(invalid_serialized_value_2)


    def test_category_subhandler_deserialize(self):
        
        """
        Test the deserialize method.
        An instance of this model has been created initial setup
        """

        field_value = {"id": "fake_category"}

        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = CategorySubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertEqual(deserialized_value, self.category)
        self.assertEqual(deserialized_value.identifier, field_value["id"])

    def test_category_subhandler_deserialize_with_invalid_data(self):
        
        """
        Test the deserialize method with invalid data.
        """
   
        field_value = None
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = CategorySubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertIsNone(deserialized_value)
    
    
    @patch('geonode.metadata.handlers.base.reverse')
    def test_license_subhandler_update_subschema(self,  mocked_endpoint):

        """ 
        Test for the update_subschema of the LicenseSubHandler.
        An instance of this model has been created initial setup
        """
        
        mocked_endpoint.return_value = "/mocked_url"

        subschema = {
          "type": "string",
          "title": "License",
          "description": "a fake description",
          "maxLength": 255
        }
        
        # Call the update_subschema method with the real database data
        LicenseSubHandler.update_subschema(subschema, lang='en')

        # Assert changes to the subschema
        self.assertIn("ui:options", subschema)
        self.assertIn("geonode-ui:autocomplete", subschema["ui:options"])
        self.assertEqual(subschema["ui:options"]["geonode-ui:autocomplete"], mocked_endpoint.return_value)

    
    def test_license_subhandler_serialize_with_existed_db_value(self):
        
        """
        Test the serialize method with existed db value.
        An instance of this model has been created initial setup
        """

        # Test the case where the db_value is a model instance
        serialized_value = LicenseSubHandler.serialize(self.license)

        expected_value = {"id": self.license.identifier, "label": _(self.license.name)}
        
        self.assertEqual(serialized_value, expected_value)
        
        # Assert that the serialize method returns the identifier
        self.assertEqual(serialized_value["id"], self.license.identifier)

    
    def test_license_subhandler_serialize_invalid_data(self):
        
        """
        Test the serialize method with invalid db value.
        An instance of this model has been created initial setup
        """
        
        # Test the case where the db_value is not a model instance
        non_license_value = "nonexistent value"
        
        invalid_serialized_value_1 = LicenseSubHandler.serialize(non_license_value)
        invalid_serialized_value_2 = LicenseSubHandler.serialize(None)

        # Assert that the serialize method returns the input value unchanged
        self.assertIsNone(invalid_serialized_value_1)
        self.assertIsNone(invalid_serialized_value_2)

    def test_license_subhandler_deserialize(self):
        
        """
        Test the deserialize method.
        An instance of this model has been created initial setup
        """

        field_value = {"id": "fake_license"}

        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = LicenseSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertEqual(deserialized_value, self.license)
        self.assertEqual(deserialized_value.identifier, field_value["id"])

    
    def test_license_subhandler_deserialize_with_invalid_data(self):
        
        """
        Test the deserialize method with invalid data.
        """
   
        field_value = None
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = LicenseSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertIsNone(deserialized_value)


    def test_restrictions_subhandler_update_subschema(self):

        """ 
        Test for the update_subschema of the LicenseSubHandler.
        An instance of the RestrictionCodeType model has been created
        """
        
        subschema = {
          "type": "string",
          "title": "restrictions",
          "description": "limitation(s) placed upon the access or use of the data.",
          "maxLength": 255
        }
        
        # Delete all the RestrictionCodeType models except the "fake_license"
        fake_restrictions = RestrictionCodeType.objects.get(identifier="fake_restrictions")
        RestrictionCodeType.objects.exclude(identifier=fake_restrictions.identifier).delete()

        # Call the update_subschema method with the real database data
        RestrictionsSubHandler.update_subschema(subschema, lang='en')

        # Assertions
        self.assertIn("oneOf", subschema)
        self.assertEqual(len(subschema["oneOf"]), 1)

        # Check that each entry in "oneOf" contains the expected "const", "title", and "description"
        self.assertEqual(subschema["oneOf"][0]["const"], "fake_restrictions")
        self.assertEqual(subschema["oneOf"][0]["title"], "fake_restrictions")
        self.assertEqual(subschema["oneOf"][0]["description"], "a detailed description")

    
    def test_restrictions_subhandler_serialize_with_existed_db_value(self):
        
        """
        Test the serialize method with existed db value.
        An instance of this model has been created initial setup
        """

        # Test the case where the db_value is a model instance
        serialized_value = RestrictionsSubHandler.serialize(self.restrictions)

        # Assert that the serialize method returns the identifier
        self.assertEqual(serialized_value, self.restrictions.identifier)

    def test_restrictions_subhandler_serialize_with_non_existed_db_value(self):
        
        """
        Test the serialize method without an existed db value.
        An instance of this model has been created initial setup
        """

        # Test the case where the db_value is not a model instance
        non_restrictions_value = "nonexistent value"
        
        serialized_value = RestrictionsSubHandler.serialize(non_restrictions_value)

        # Assert that the serialize method returns the input value unchanged
        self.assertEqual(serialized_value, non_restrictions_value)

    def test_restrictions_subhandler_deserialize(self):
        
        """
        Test the deserialize method.
        An instance of this model has been created initial setup
        """

        field_value = "fake_restrictions"
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = RestrictionsSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertEqual(deserialized_value, self.restrictions)
        self.assertEqual(deserialized_value.identifier, field_value)
        
    
    def test_restrictions_subhandler_deserialize_with_invalid_data(self):
        
        """
        Test the deserialize method with invalid data.
        """
   
        field_value = None
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = RestrictionsSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertIsNone(deserialized_value)


    def test_spatial_repr_type_subhandler_update_subschema(self):

        """ 
        Test for the update_subschema of the SpatialRepresentationTypeSubHandler.
        An instance of the SpatialRepresentationType model has been created
        """
        
        subschema = {
          "type": "string",
          "title": "spatial representation type",
          "description": "method used to represent geographic information in the dataset.",
          "maxLength": 255
        }

        # Delete all the SpatialRepresentationType models except the "fake_spatial_repr"
        fake_spatial_repr = SpatialRepresentationType.objects.get(identifier="fake_spatial_repr")
        SpatialRepresentationType.objects.exclude(identifier=fake_spatial_repr.identifier).delete()

        # Call the update_subschema method with the real database data
        SpatialRepresentationTypeSubHandler.update_subschema(subschema, lang='en')

        # Assertions
        self.assertIn("oneOf", subschema)
        self.assertEqual(len(subschema["oneOf"]), 1)

        # Check that each entry in "oneOf" contains the expected "const", "title", and "description"
        self.assertEqual(subschema["oneOf"][0]["const"], "fake_spatial_repr")
        self.assertEqual(subschema["oneOf"][0]["title"], "fake_spatial_repr")
        self.assertEqual(subschema["oneOf"][0]["description"], "a detailed description")

    
    def test_spatial_repr_type_subhandler_serialize_with_existed_db_value(self):
        
        """
        Test the serialize method with existed db value.
        An instance of this model has been created initial setup
        """

        # Test the case where the db_value is a model instance
        serialized_value = SpatialRepresentationTypeSubHandler.serialize(self.spatial_repr)

        # Assert that the serialize method returns the identifier
        self.assertEqual(serialized_value, self.spatial_repr.identifier)

    def test_spatial_repr_type_subhandler_serialize_with_non_existed_db_value(self):
        
        """
        Test the serialize method without an existed db value.
        An instance of this model has been created initial setup
        """

        # Test the case where the db_value is not a model instance
        non_spatial_repr_value = "nonexistent value"
        
        serialized_value = SpatialRepresentationTypeSubHandler.serialize(non_spatial_repr_value)

        # Assert that the serialize method returns the input value unchanged
        self.assertEqual(serialized_value, non_spatial_repr_value)

    def test_spatial_repr_type_subhandler_deserialize(self):
        
        """
        Test the deserialize method.
        An instance of this model has been created initial setup
        """

        field_value = "fake_spatial_repr"
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = SpatialRepresentationTypeSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertEqual(deserialized_value, self.spatial_repr)
        self.assertEqual(deserialized_value.identifier, field_value)

    
    def test_spatial_repr_type_subhandler_deserialize_with_invalid_data(self):
        
        """
        Test the deserialize method with invalid data.
        """
   
        field_value = None
        
        # Call the method using the "fake_category" identifier from the created instance
        deserialized_value = SpatialRepresentationTypeSubHandler.deserialize(field_value)

        # Assert that the deserialized value is the correct model instance
        self.assertIsNone(deserialized_value)


    def test_date_type_subhandler_update_subschema(self):
        
        """
        SubHandler test for the date type
        """
        
        # Prepare the initial subschema
        subschema = {
          "type": "string",
          "title": "date type",
          "maxLength": 255
        }

        # Expected values for "oneOf"
        expected_one_of_values = [
            {"const": "creation", "title": "Creation"},
            {"const": "publication", "title": "Publication"},
            {"const": "revision", "title": "Revision"},
        ]

        # Call the method to update the subschema
        DateTypeSubHandler.update_subschema(subschema, lang="en")

        # Assertions
        self.assertIn("oneOf", subschema)
        self.assertEqual(subschema["oneOf"], expected_one_of_values)
        self.assertIn("default", subschema)
        self.assertEqual(subschema["default"], "Publication")
    

    def test_date_subhandler_serialize_with_valid_datetime(self):
        
        """
        Subhandler test for the date serialization to the isoformat
        """
        
        test_datetime = datetime(2024, 12, 19, 15, 30, 45)

        # Call the serialize method
        serialized_value = DateSubHandler.serialize(test_datetime)

        # Expected ISO 8601 format
        expected_value = "2024-12-19T15:30:45"

        self.assertEqual(serialized_value, expected_value)

    def test_date_subhandler_serialize_without_datetime(self):

        """
        Subhandler test for the date serialization to the isoformat with non
        existent datetime object
        """
        
        test_value = "nonexistent datetime"

        # Call the serialize method
        serialized_value = DateSubHandler.serialize(test_value)

        self.assertEqual(serialized_value, test_value)


    @patch("geonode.metadata.handlers.base.UPDATE_FREQUENCIES", new=[
        ("fake_frequency1", _("Fake frequency 1")),
        ("fake_frequency2", _("Fake frequency 2")),
        ("fake_frequency3", _("Fake frequency 3")),
    ])
    def test_frequency_subhandler_update_subschema(self):

        """
        Subhandler test for the maintenance frequency
        """
        
        subschema = {
          "type": "string",
          "title": "maintenance frequency",
          "description": "a detailed description",
          "maxLength": 255
        }

        # Expected values for "oneOf"
        expected_one_of_values = [
            {"const": "fake_frequency1", "title": "Fake frequency 1"},
            {"const": "fake_frequency2", "title": "Fake frequency 2"},
            {"const": "fake_frequency3", "title": "Fake frequency 3"},
        ]

        # Call the method to update the subschema
        FrequencySubHandler.update_subschema(subschema, lang="en")

        self.assertIn("oneOf", subschema)
        self.assertEqual(subschema["oneOf"], expected_one_of_values)

    
    @patch("geonode.metadata.handlers.base.ALL_LANGUAGES", new=[
        ("fake_language1", "Fake language 1"),
        ("fake_language2", "Fake language 2"),
        ("fake_language3", "Fake language 3"),
    ])
    def test_language_subhandler_update_subschema(self):

        """
        Language subhandler test
        """
        
        subschema = {
          "type": "string",
          "title": "language",
          "description": "language used within the dataset",
          "maxLength": 255,
          "default": "eng"
        }

        # Expected values for "oneOf"
        expected_one_of_values = [
            {"const": "fake_language1", "title": "Fake language 1"},
            {"const": "fake_language2", "title": "Fake language 2"},
            {"const": "fake_language3", "title": "Fake language 3"},
        ]

        # Call the method to update the subschema
        LanguageSubHandler.update_subschema(subschema, lang="en")

        self.assertIn("oneOf", subschema)
        self.assertEqual(subschema["oneOf"], expected_one_of_values)

    
    def test_add_sub_schema_without_after_what(self):
        
        """
        This method is used by most of the handlers in the update_schema
        method, in order to add the subschema to the desired place. 
        This test ensures the method's functionality without after_what
        """
        
        jsonschema = self.fake_schema
        subschema = self.fake_subschema
        property_name = "new_field"

        self.base_handler._add_subschema(jsonschema, property_name, subschema)

        self.assertIn(property_name, jsonschema["properties"])
        self.assertEqual(jsonschema["properties"][property_name], subschema)

    
    def test_add_sub_schema_with_after_what(self):
        
        """
        This method is used by most of the handlers in the update_schema
        method, in order to add the subschema to the desired place.
        This test ensures the method's functionality with after_what
        """
        
        jsonschema = self.fake_schema
        subschema = self.fake_subschema
        property_name = "new_field"

        # Add the "new_field" after the field "field2"
        self.base_handler._add_subschema(jsonschema, property_name, subschema, after_what="field2")

        self.assertIn(property_name, jsonschema["properties"])
        # Check that the new field has been added with the defined order
        self.assertEqual(list(jsonschema["properties"].keys()), ["field1", "field2", "new_field", "field3"])

    
    def test_add_subschema_with_nonexistent_after_what(self):
        
        """
        This method is used by most of the handlers in the update_schema
        method, in order to add the subschema to the desired place.
        This test ensures the method's functionality with a non-existent
        after_what
        """
        
        jsonschema = self.fake_schema
        subschema = self.fake_subschema
        property_name = "new_field"

        self.base_handler._add_subschema(jsonschema, property_name, subschema, after_what="nonexistent_property")

        # Check that the new property was added
        self.assertIn(property_name, jsonschema["properties"])

        # Check that the order is maintained as best as possible
        self.assertEqual(list(jsonschema["properties"].keys()), ["field1", "field2", "field3", "new_field"])

        # Check that the subschema was added
        self.assertEqual(jsonschema["properties"][property_name], subschema)

    
    def test_add_subschema_to_empty_jsonschema(self):
        
        """
        This method is used by most of the handlers in the update_schema
        method, in order to add the subschema to the desired place.
        This test ensures the method's functionality with an empty schema
        """
        
        jsonschema = {"properties": {}}
        subschema = self.fake_subschema
        property_name = "new_field"

        self.base_handler._add_subschema(jsonschema, property_name, subschema, after_what="nonexistent_property")

        self.assertIn(property_name, jsonschema["properties"])
        self.assertEqual(jsonschema["properties"][property_name], subschema)

    
    # Tests for the Region handler
    
    @patch('geonode.metadata.handlers.region.reverse')
    def test_region_handler_update_schema(self, mock_reverse):
        
        """
        Test for the update_schema of the region_handler. In this
        test we don't check if the region subschema was added after
        the defined property because the _add_subschema method has 
        been tested above
        """
        
        jsonschema = self.fake_schema
        mock_reverse.return_value = "/mocked_endpoint"

        # Define the expected regions schema
        expected_regions = {
            "type": "array",
            "title": "Regions",
            "description": "keyword identifies a location",
            "items": {
                "type": "object",
               "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string", "title": "title"},
                },
            },
            "geonode:handler": "region",
            "ui:options": {"geonode-ui:autocomplete": "/mocked_endpoint"},
        }

        # Call the method
        updated_schema = self.region_handler.update_schema(jsonschema, self.context, lang=self.lang)

        self.assertIn("regions", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["regions"], expected_regions)


    def test_region_handler_get_jsonschema_instance(self):
        
        """
        Test the get_jsonschema_instance of the region handler
        using two region examples: Italy and Greece
        """

        # Add two Region instances to the ResourceBase instance
        region_1 = Region.objects.get(code="ITA")
        region_2 = Region.objects.get(code="GRC")
        self.resource.regions.add(region_1, region_2)
        
        # Call the method to get the JSON schema instance
        field_name = "regions"

        region_instance = self.region_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        # Assert that the JSON schema contains the regions we added
        expected_region_subschema = [
            {"id": str(region_1.id), "label": region_1.name},
            {"id": str(region_2.id), "label": region_2.name}
        ]
        
        self.assertEqual(
            sorted(region_instance, key=lambda x: x["id"]),
            sorted(expected_region_subschema, key=lambda x: x["id"])
        )

    
    def test_region_handler_update_resource(self):
        
        """
        Test the update resource of the region handler
        using two region examples from the testing database
        """

        # Initially we add two Region instances to the ResourceBase instance
        region_1 = Region.objects.get(code="GLO")
        region_2 = Region.objects.get(code="AFR")
        self.resource.regions.add(region_1, region_2)

        # Definition of the new regions which will be used from the tested method
        # in order to update the database replacing the above regions with the regions below
        updated_region_1 = Region.objects.get(code="ITA")
        updated_region_2 = Region.objects.get(code="GRC")
        region_3 = Region.objects.get(code="CYP")

        payload_data = {
            "regions": [
                {"id": str(updated_region_1.id), "label": updated_region_1.name},
                {"id": str(updated_region_2.id), "label": updated_region_2.name},
                {"id": str(region_3.id), "label": region_3.name},
            ]
        }
        
        # Call the method to get the JSON schema instance
        field_name = "regions"

        # Call the method
        self.region_handler.update_resource(self.resource, field_name, payload_data, self.context, self.errors)

        # Ensure that only the regions defined in the payload_data are included in the resource model
        self.assertEqual(
            sorted(self.resource.regions.all(), key=lambda region: region.name),
            sorted([updated_region_1, updated_region_2, region_3], key=lambda region: region.name)
        )


    # Tests for the linkedresource handler
    
    @patch('geonode.metadata.handlers.linkedresource.reverse')
    def test_linkedresource_handler_update_schema(self, mock_reverse):
        
        """
        Test for the update_schema of the linkedresource
        """
        
        jsonschema = self.fake_schema
        mock_reverse.return_value = "/mocked_endpoint"

        # Define the expected regions schema
        expected_linked = {
            "type": "array",
            "title": _("Related resources"),
            "description": _("Resources related to this one"),
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                    },
                    "label": {"type": "string", "title": _("title")},
                },
            },
            "geonode:handler": "linkedresource",
            "ui:options": {"geonode-ui:autocomplete": "/mocked_endpoint"},
        }

        # Call the method
        updated_schema = self.linkedresource_handler.update_schema(jsonschema, self.context, lang=self.lang)

        self.assertIn("linkedresources", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["linkedresources"], expected_linked)


    def test_linkedresource_handler_get_jsonschema_instance(self):
        
        """
        Test the get_jsonschema_instance of the linkedresource handler
        """

        # Add a linked resource to the main resource (self.resource)
        linked_resource = LinkedResource.objects.create(
            source=self.resource,
            target=self.extra_resource_1,
            )

        field_name = "linkedresources"

        linkedresource_instance = self.linkedresource_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        expected_linkedresource_subschema = [
            {"id": str(linked_resource.target.id), "label": linked_resource.target.title},
        ]
        
        self.assertEqual(linkedresource_instance, expected_linkedresource_subschema)

    
    def test_linkedresource_handler_update_resource(self):
        
        """
        Test the update resource of the linkedresource handler
        """

        # Add a linked resource just to test if it will be removed
        # after the update_resource call
        # Add a linked resource to the main resource (self.resource)
        LinkedResource.objects.create(
            source=self.resource,
            target=self.extra_resource_3,
            )

        payload_data = {
            "linkedresources": [
                {"id": self.extra_resource_1.id},
                {"id": self.extra_resource_2.id}
            ]
        }
        
        # Call the method to get the JSON schema instance
        field_name = "linkedresources"

        # Call the method
        self.linkedresource_handler.update_resource(self.resource, field_name, payload_data, self.context, self.errors)

        # Verify the new links
        linked_resources = LinkedResource.objects.filter(source=self.resource, internal=False)
        linked_targets = [link.target for link in linked_resources]
        self.assertIn(self.extra_resource_1, linked_targets)
        self.assertIn(self.extra_resource_2, linked_targets)
        # Ensure that the initial linked resource has been removed
        self.assertNotIn(self.extra_resource_3, linked_targets)

        # Ensure that there is only one linked resource
        self.assertEqual(len(linked_targets), 2)


    











        