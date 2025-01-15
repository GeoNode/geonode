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
from django.contrib.auth.models import Group
from geonode.groups.models import GroupProfile
from geonode.people import Roles

from geonode.metadata.settings import MODEL_SCHEMA
from geonode.base.models import (
    ResourceBase,
    TopicCategory,
    RestrictionCodeType,
    License,
    SpatialRepresentationType,
    Region,
    LinkedResource,
    Thesaurus,
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    ContactRole,
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
from geonode.metadata.handlers.doi import DOIHandler
from geonode.metadata.handlers.linkedresource import LinkedResourceHandler
from geonode.metadata.handlers.group import GroupHandler
from geonode.metadata.handlers.hkeyword import HKeywordHandler
from geonode.metadata.handlers.thesaurus import TKeywordsHandler
from geonode.resource.utils import KeywordHandler
from geonode.metadata.handlers.contact import ContactHandler, ROLE_NAMES_MAP
from geonode.metadata.handlers.sparse import SparseHandler, sparse_field_registry
from geonode.metadata.models import SparseField
from geonode.metadata.exceptions import UnsetFieldException

from geonode.tests.base import GeoNodeBaseTestSupport


class HandlersTests(GeoNodeBaseTestSupport):

    def setUp(self):
        # set Json schemas
        self.model_schema = MODEL_SCHEMA
        self.lang = None
        self.errors = {}
        self.context = MagicMock()

        self.test_user = get_user_model().objects.create_user(
            "user_1", "user_1@fakemail.com", "user_1_password", is_active=True
        )

        # Testing database setup
        self.resource = ResourceBase.objects.create(title="Test Resource", uuid=str(uuid4()), owner=self.test_user)
        self.extra_resource_1 = ResourceBase.objects.create(
            title="Extra resource 1", uuid=str(uuid4()), owner=self.test_user
        )
        self.extra_resource_2 = ResourceBase.objects.create(
            title="Extra resource 2", uuid=str(uuid4()), owner=self.test_user
        )
        self.extra_resource_3 = ResourceBase.objects.create(
            title="Extra resource 3", uuid=str(uuid4()), owner=self.test_user
        )

        self.category = TopicCategory.objects.create(
            identifier="fake_category", gn_description="a fake gn description", description="a detailed description"
        )
        self.license = License.objects.create(
            identifier="fake_license", name="a fake name", description="a detailed description"
        )
        self.restrictions = RestrictionCodeType.objects.create(
            identifier="fake_restrictions", description="a detailed description"
        )
        self.spatial_repr = SpatialRepresentationType.objects.create(
            identifier="fake_spatial_repr", description="a detailed description"
        )
        self.fake_group = Group.objects.create(name="fake group")
        # Create instances for thesaurus
        self.thesaurus1 = Thesaurus.objects.create(title="Spatial scope thesaurus", identifier="3-2-4-3-spatialscope")
        self.thesaurus2 = Thesaurus.objects.create(
            title="INSPIRE themes thesaurus", identifier="3-2-4-1-gemet-inspire-themes"
        )

        # Create ThesaurusKeywords
        self.keyword1 = ThesaurusKeyword.objects.create(
            about="http://example.com/keyword1",
            alt_label="Alt Label 1",
            thesaurus=self.thesaurus1,
        )
        self.keyword2 = ThesaurusKeyword.objects.create(
            about="http://example.com/keyword2",
            alt_label="Alt Label 2",
            thesaurus=self.thesaurus2,
        )

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
        self.doi_handler = DOIHandler()
        self.group_handler = GroupHandler()
        self.hkeyword_handler = HKeywordHandler()
        self.contact_handler = ContactHandler()
        self.tkeywords_handler = TKeywordsHandler()
        self.sparse_handler = SparseHandler()

        # A fake subschema
        self.fake_subschema = {
            "type": "string",
            "title": "new field",
            "description": "A new field was added",
            "maxLength": 255,
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
            subschema["oneOf"] = [{"const": "fake const", "title": "fake title"}]

        # Add the mock behavior for update_subschema
        mock_subhandlers[field_name].update_subschema.side_effect = mock_update_subschema

        # Call the method
        updated_schema = self.base_handler.update_schema(jsonschema, self.context, self.lang)

        # Check the full base schema
        for field in self.fake_base_schema:
            self.assertIn(field, updated_schema["properties"])

        # Check subhandler execution for the field name "date"
        self.assertEqual(
            updated_schema["properties"]["date"].get("oneOf"), [{"const": "fake const", "title": "fake title"}]
        )
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
        field_value = self.base_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, lang=None
        )

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
            resource=fake_resource, field_name=field_name, context=self.context, errors=self.errors, lang=self.lang
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
            errors=self.errors,
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
            errors=self.errors,
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
            errors=self.errors,
        )

        mock_subhandlers[field_name].deserialize.assert_called_once_with(field_value)

        # Ensure that the exception is logged
        mock_logger.warning.assert_called_once_with(
            f"Error setting field {field_name}={field_value}: Deserialization error"
        )

    # Tests for subhandler classes of the base handler
    @patch("geonode.metadata.handlers.base.reverse")
    def test_category_subhandler_update_subschema(self, mocked_endpoint):
        """
        Test for the update_subschema of the CategorySubHandler.
        An instance of this model has been created initial setup
        """

        mocked_endpoint.return_value = "/mocked_url"

        subschema = {"type": "string", "title": "Category", "description": "a fake description", "maxLength": 255}

        # Call the update_subschema method with the real database data
        CategorySubHandler.update_subschema(subschema, lang="en")

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

    @patch("geonode.metadata.handlers.base.reverse")
    def test_license_subhandler_update_subschema(self, mocked_endpoint):
        """
        Test for the update_subschema of the LicenseSubHandler.
        An instance of this model has been created initial setup
        """

        mocked_endpoint.return_value = "/mocked_url"

        subschema = {"type": "string", "title": "License", "description": "a fake description", "maxLength": 255}

        # Call the update_subschema method with the real database data
        LicenseSubHandler.update_subschema(subschema, lang="en")

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
            "maxLength": 255,
        }

        # Delete all the RestrictionCodeType models except the "fake_license"
        fake_restrictions = RestrictionCodeType.objects.get(identifier="fake_restrictions")
        RestrictionCodeType.objects.exclude(identifier=fake_restrictions.identifier).delete()

        # Call the update_subschema method with the real database data
        RestrictionsSubHandler.update_subschema(subschema, lang="en")

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
            "maxLength": 255,
        }

        # Delete all the SpatialRepresentationType models except the "fake_spatial_repr"
        fake_spatial_repr = SpatialRepresentationType.objects.get(identifier="fake_spatial_repr")
        SpatialRepresentationType.objects.exclude(identifier=fake_spatial_repr.identifier).delete()

        # Call the update_subschema method with the real database data
        SpatialRepresentationTypeSubHandler.update_subschema(subschema, lang="en")

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
        subschema = {"type": "string", "title": "date type", "maxLength": 255}

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

    @patch(
        "geonode.metadata.handlers.base.UPDATE_FREQUENCIES",
        new=[
            ("fake_frequency1", _("Fake frequency 1")),
            ("fake_frequency2", _("Fake frequency 2")),
            ("fake_frequency3", _("Fake frequency 3")),
        ],
    )
    def test_frequency_subhandler_update_subschema(self):
        """
        Subhandler test for the maintenance frequency
        """

        subschema = {
            "type": "string",
            "title": "maintenance frequency",
            "description": "a detailed description",
            "maxLength": 255,
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

    @patch(
        "geonode.metadata.handlers.base.ALL_LANGUAGES",
        new=[
            ("fake_language1", "Fake language 1"),
            ("fake_language2", "Fake language 2"),
            ("fake_language3", "Fake language 3"),
        ],
    )
    def test_language_subhandler_update_subschema(self):
        """
        Language subhandler test
        """

        subschema = {
            "type": "string",
            "title": "language",
            "description": "language used within the dataset",
            "maxLength": 255,
            "default": "eng",
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

    @patch("geonode.metadata.handlers.region.reverse")
    def test_region_handler_update_schema(self, mock_reverse):
        """
        Test for the update_schema of the region_handler
        """

        # fake schema definition which includes the "attribution" field
        schema = {
            "properties": {
                "attribution": {"type": "string", "title": "attribution", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }
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
        updated_schema = self.region_handler.update_schema(schema, self.context, lang=self.lang)

        self.assertIn("regions", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["regions"], expected_regions)
        # Check that the new field has been added with the expected order
        self.assertEqual(list(schema["properties"].keys()), ["attribution", "regions", "fake_field"])

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
        expected_region_instance = [
            {"id": str(region_1.id), "label": region_1.name},
            {"id": str(region_2.id), "label": region_2.name},
        ]

        self.assertEqual(
            sorted(region_instance, key=lambda x: x["id"]), sorted(expected_region_instance, key=lambda x: x["id"])
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
            sorted([updated_region_1, updated_region_2, region_3], key=lambda region: region.name),
        )

    # Tests for the linkedresource handler

    @patch("geonode.metadata.handlers.linkedresource.reverse")
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

        payload_data = {"linkedresources": [{"id": self.extra_resource_1.id}, {"id": self.extra_resource_2.id}]}

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

    # Tests for the DOI handler
    def test_doi_handler_update_schema(self):
        """
        Test for the update_schema of the doi_handler
        """

        # fake_schema definition which includes the "edition" field
        schema = {
            "properties": {
                "edition": {"type": "string", "title": "edition", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }

        # Define the expected regions schema
        expected_doi_subschema = {
            "type": ["string", "null"],
            "title": "DOI",
            "description": _("a DOI will be added by Admin before publication."),
            "maxLength": 255,
            "geonode:handler": "doi",
        }

        # Call the method
        updated_schema = self.doi_handler.update_schema(schema, self.context, lang=self.lang)

        self.assertIn("doi", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["doi"], expected_doi_subschema)
        # Check that the new field has been added with the expected order
        self.assertEqual(list(schema["properties"].keys()), ["edition", "doi", "fake_field"])

    def test_doi_handler_get_jsonschema_instance(self):
        """
        Test the get_jsonschema_instance of the doi handler
        """

        # Initially we add a doi to the ResourceBase instance
        self.resource.doi = "10.1234/fake_doi"

        field_name = "doi"

        # Call the method
        result = self.doi_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        # Assert the result is as expected
        self.assertEqual(result, "10.1234/fake_doi")

    def test_doi_handler_update_resource(self):
        """
        Test the update resource of the doi handler
        """

        # Initially we add a doi to the ResourceBase instance
        self.resource.doi = "10.1234/fake_doi"

        payload_data = {"doi": "10.1000/new_fake_doi"}

        # Call the method to get the JSON schema instance
        field_name = "doi"

        # Call the method
        self.doi_handler.update_resource(self.resource, field_name, payload_data, self.context, self.errors)

        # Ensure that only the regions defined in the payload_data are included in the resource model
        self.assertEqual(self.resource.doi, "10.1000/new_fake_doi")

    # Tests for the Group handler
    @patch("geonode.metadata.handlers.group.reverse")
    def test_group_handler_update_schema(self, mock_reverse):
        """
        Test for the update_schema of the group_handler
        """

        mock_reverse.return_value = "/mocked_endpoint"

        # fake_schema definition which includes the "date_type" field
        schema = {
            "properties": {
                "date_type": {"type": "string", "title": "date_type", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }

        # Define the expected regions schema
        expected_group_subschema = {
            "type": "object",
            "title": _("group"),
            "properties": {
                "id": {
                    "type": "string",
                    "ui:widget": "hidden",
                },
                "label": {
                    "type": "string",
                    "title": _("group"),
                },
            },
            "geonode:handler": "group",
            "ui:options": {"geonode-ui:autocomplete": "/mocked_endpoint"},
        }

        # Call the method
        updated_schema = self.group_handler.update_schema(schema, self.context, lang=self.lang)

        self.assertIn("group", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["group"], expected_group_subschema)
        # Check that the new field has been added with the expected order
        self.assertEqual(list(schema["properties"].keys()), ["date_type", "group", "fake_field"])

    def test_group_handler_get_jsonschema_instance_with_group(self):
        """
        Test the get_jsonschema_instance of the group handler
        """

        GroupProfile.objects.create(group=self.fake_group, title="Test Group Profile")
        self.resource.group = self.fake_group

        field_name = "group"

        expected_group_instance = {
            "id": str(self.resource.group.groupprofile.pk),
            "label": self.resource.group.groupprofile.title,
        }

        group_instance = self.group_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        self.assertEqual(group_instance, expected_group_instance)

    def test_group_handler_get_jsonschema_instance_without_group(self):
        """
        Test the get_jsonschema_instance of the group handler
        in case that we don't have a group
        """

        field_name = "group"

        group_instance = self.group_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        self.assertIsNone(group_instance)

    def test_group_handler_update_resource_with_valid_id(self):

        group_profile = GroupProfile.objects.create(group=self.fake_group, title="Test Group Profile")

        field_name = "group"
        payload_data = {"group": {"id": group_profile.pk}}

        # Call the method
        self.group_handler.update_resource(self.resource, field_name, payload_data, self.context, self.errors)

        # Assert the resource group was updated
        self.assertEqual(self.resource.group, group_profile.group)

    def test_group_handler_update_resource_with_no_id(self):

        field_name = "group"
        json_instance = {"group": None}

        # Call the method
        self.group_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        # Assert the resource group was set to None
        self.assertIsNone(self.resource.group)

    def test_group_handler_update_resource_without_field(self):

        field_name = "group"
        json_instance = {}

        # Call the method
        self.group_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        # Assert the resource group was set to None
        self.assertIsNone(self.resource.group)

    # Tests hkeyword handler
    @patch("geonode.metadata.handlers.hkeyword.reverse")
    def test_hkeyword_handler_update_schema(self, mock_reverse):
        """
        Test for the update_schema of the hkeyword_handler
        """

        mock_reverse.return_value = "/mocked_endpoint"

        # fake_schema definition which includes the "tkeywords" field
        schema = {
            "properties": {
                "tkeywords": {"type": "string", "title": "tkeywords", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }

        # Define the expected regions schema
        expected_hkeywords_subschema = {
            "type": "array",
            "title": _("Keywords"),
            "description": _("Hierarchical keywords"),
            "items": {
                "type": "string",
            },
            "ui:options": {
                "geonode-ui:autocomplete": {
                    "url": "/mocked_endpoint",
                    "creatable": True,
                },
            },
            "geonode:handler": "hkeyword",
        }

        # Call the method
        updated_schema = self.hkeyword_handler.update_schema(schema, self.context, lang=self.lang)

        self.assertIn("hkeywords", updated_schema["properties"])
        self.assertEqual(updated_schema["properties"]["hkeywords"], expected_hkeywords_subschema)
        # Check that the new field has been added with the expected order
        self.assertEqual(list(schema["properties"].keys()), ["tkeywords", "hkeywords", "fake_field"])

    def test_hkeywords_handler_get_jsonschema_instance_with_keywords(self):

        field_name = "keywords"

        hkeywords = ["Keyword 1", "Keyword 2"]
        KeywordHandler(self.resource, hkeywords).set_keywords()

        # Call the method
        result = self.hkeyword_handler.get_jsonschema_instance(self.resource, field_name, self.context, self.errors)

        #  Assert the correct list of keyword names with order-independent
        expected = ["Keyword 1", "Keyword 2"]
        self.assertCountEqual(result, expected)

    def test_hkeywords_handler_get_jsonschema_instance_no_keywords(self):

        # Ensure no keywords are defined with the resource
        KeywordHandler(self.resource, []).set_keywords()

        field_name = "keywords"

        # Call the method
        result = self.hkeyword_handler.get_jsonschema_instance(self.resource, field_name, self.context, self.errors)

        # Assert the result is an empty list
        self.assertEqual(result, [])

    def test_hkeywords_handler_update_resource_with_valid_keywords(self):

        field_name = "hkeywords"
        json_instance = {"hkeywords": ["new keyword 1", "new keyword 2"]}

        # Call the method
        self.hkeyword_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        # Assert that the keywords were correctly added to the resource
        keywords = list(self.resource.keywords.all())
        keyword_names = [keyword.name for keyword in keywords]
        expected_keywords = ["new keyword 1", "new keyword 2"]
        self.assertCountEqual(keyword_names, expected_keywords)

    def test_hkeywords_handler_update_resource_without_keywords(self):

        field_name = "hkeywords"
        json_instance = {"hkeywords": []}

        # Call the method
        self.hkeyword_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        self.assertEqual(self.resource.keywords.count(), 0)

    def test_hkeywords_handler_update_resource_with_null_empty_keywords(self):

        field_name = "hkeywords"
        json_instance = {"hkeywords": [None, "valid keyword", ""]}

        # Call the method
        self.hkeyword_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        # Assert that the keywords were correctly added to the resource
        keywords = list(self.resource.keywords.all())
        keyword_names = [keyword.name for keyword in keywords]
        expected_keywords = ["valid keyword"]
        self.assertCountEqual(keyword_names, expected_keywords)

    # Tests for contact handler
    @patch("geonode.metadata.handlers.contact.reverse")
    def test_contact_handler_update_schema(self, mock_reverse):
        # Mock reverse function
        mock_reverse.return_value = "/mocked/url"

        # Call update_schema
        updated_schema = self.contact_handler.update_schema(self.fake_schema, self.context, self.lang)

        self.assertIn("contacts", updated_schema["properties"])

        # Check if all roles are included in the contacts
        contacts = updated_schema["properties"]["contacts"]["properties"]
        for role in Roles:
            rolename = ROLE_NAMES_MAP.get(role, role.name)
            self.assertIn(rolename, contacts)

            contact = contacts[rolename]
            self.assertIn("type", contact)

            if role.is_multivalue:
                self.assertEqual(contact.get("type"), "array")
                self.assertIn("minItems", contact)
                self.assertIn("properties", contact["items"])
                if role.is_required:
                    self.assertEqual(contact["minItems"], 1)
                else:
                    self.assertEqual(contact["minItems"], 0)
            else:
                self.assertEqual(contact.get("type"), "object")
                self.assertIn("properties", contact)
                # Assert 'id' field is required if the role is required
                if role.is_required:
                    self.assertIn("id", contact["required"])
                else:
                    self.assertNotIn("id", contact["required"])

    def test_contact_handler_get_jsonschema_instance(self):

        field_name = "contacts"

        # Create an author role for testing
        author_role = get_user_model().objects.create_user(
            "author_role", "author_role@fakemail.com", "new_fake_user_password", is_active=True
        )

        # Assign metadata author role
        ContactRole.objects.create(
            resource=self.resource, role=ROLE_NAMES_MAP[Roles.METADATA_AUTHOR], contact=author_role
        )

        # Call the method
        result = self.contact_handler.get_jsonschema_instance(
            self.resource, field_name, self.context, self.errors, self.lang
        )

        # Assert the output structure and content
        self.assertIn(ROLE_NAMES_MAP[Roles.OWNER], result)
        self.assertIn(ROLE_NAMES_MAP[Roles.METADATA_AUTHOR], result)

        # Check owner which is defined in the setUp method as test_user
        owner_entry = result[ROLE_NAMES_MAP[Roles.OWNER]]
        self.assertEqual(owner_entry["id"], str(self.test_user.id))
        self.assertEqual(owner_entry["label"], f"{self.test_user.username}")

        # Check metadata author
        author_entry = result[ROLE_NAMES_MAP[Roles.METADATA_AUTHOR]]
        self.assertEqual(len(author_entry), 1)  # Assuming it's a multivalue role
        self.assertEqual(author_entry[0]["id"], str(author_role.id))
        self.assertEqual(author_entry[0]["label"], f"{author_role.username}")

    def test_contact_handler_update_resource(self):

        field_name = "contacts"

        # Create a new owner instead of the initial test_user which is already defined as the owner
        new_owner = get_user_model().objects.create_user(
            "new_owner", "new_owner@fakemail.com", "new_owner_password", is_active=True
        )

        # Create an author role for testing
        author_role = get_user_model().objects.create_user(
            "author_role", "author_role@fakemail.com", "new_fake_user_password", is_active=True
        )

        # Prepare the JSON instance for updating
        json_instance = {
            field_name: {
                ROLE_NAMES_MAP[Roles.OWNER]: {"id": str(new_owner.id), "label": f"{new_owner.username}"},
                ROLE_NAMES_MAP[Roles.METADATA_AUTHOR]: [
                    {"id": str(author_role.id), "label": f"{author_role.username}"},
                ],
            }
        }

        # Call the method
        self.contact_handler.update_resource(self.resource, field_name, json_instance, self.context, self.errors)

        # Assert the owner has been updated
        self.assertEqual(self.resource.owner, new_owner)

        # Assert that the author role has been updated
        contacts = self.resource.__get_contact_role_elements__(ROLE_NAMES_MAP[Roles.METADATA_AUTHOR])

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].id, author_role.id)

    # Tests for thesaurus handler
    @patch("geonode.metadata.handlers.thesaurus.reverse")
    @patch("geonode.metadata.handlers.thesaurus.TKeywordsHandler.collect_thesauri")
    def test_tkeywords_handler_update_schema_with_thesauri(self, mock_collect_thesauri, mocked_endpoint):

        # fake_schema definition which includes the "category" field
        schema = {
            "properties": {
                "category": {"type": "string", "title": "category", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }

        # Mock data for collect_thesauri
        mock_collect_thesauri.return_value = {
            "3-2-4-3-spatialscope": {
                "id": 1,
                "card": {"minItems": 0, "maxItems": 1},
                "title": "Spatial scope",
                "description": "Administrative level that the data set intends to cover.",
            },
            "3-2-4-1-gemet-inspire-themes": {
                "id": 2,
                "card": {"minItems": 1},
                "title": "GEMET - INSPIRE themes, version 1.0",
                "description": "GEMET - INSPIRE themes, version 1.0",
            },
        }

        # Mock reverse to return a URL
        mocked_endpoint.side_effect = lambda name, kwargs: f"/mocked/url/{kwargs['thesaurusid']}"

        # Call the method
        updated_schema = self.tkeywords_handler.update_schema(schema, context={}, lang="en")

        # Assert tkeywords property is added
        tkeywords = updated_schema["properties"].get("tkeywords")
        self.assertIsNotNone(tkeywords)
        self.assertEqual(tkeywords["type"], "object")
        self.assertEqual(tkeywords["title"], "Keywords from Thesaurus")

        # Assert thesaurus structure for "3-2-4-3-spatialscope"
        thesaurus = tkeywords["properties"]["3-2-4-3-spatialscope"]
        self.assertEqual(thesaurus["type"], "array")
        self.assertEqual(thesaurus["title"], "Spatial scope")
        self.assertEqual(
            thesaurus["description"],
            "Administrative level that the data set intends to cover.",
        )
        self.assertEqual(thesaurus["minItems"], 0)
        self.assertEqual(thesaurus["maxItems"], 1)
        self.assertEqual(
            thesaurus["ui:options"]["geonode-ui:autocomplete"],
            "/mocked/url/1",
        )

        # Assert thesaurus structure for "3-2-4-1-gemet-inspire-themes"
        thesaurus = tkeywords["properties"]["3-2-4-1-gemet-inspire-themes"]
        self.assertEqual(thesaurus["type"], "array")
        self.assertEqual(thesaurus["title"], "GEMET - INSPIRE themes, version 1.0")
        self.assertEqual(
            thesaurus["description"],
            "GEMET - INSPIRE themes, version 1.0",
        )
        self.assertEqual(thesaurus["minItems"], 1)
        self.assertNotIn("maxItems", thesaurus)
        self.assertEqual(
            thesaurus["ui:options"]["geonode-ui:autocomplete"],
            "/mocked/url/2",
        )

    @patch("geonode.metadata.handlers.thesaurus.TKeywordsHandler.collect_thesauri")
    def test_tkeywords_handler_update_schema_no_thesauri(self, mock_collect_thesauri):

        schema = {
            "properties": {
                "category": {"type": "string", "title": "category", "maxLength": 255},
                "fake_field": {"type": "string", "title": "fake_field", "maxLength": 255},
            }
        }

        # Mock empty thesauri
        mock_collect_thesauri.return_value = {}

        # Call the method
        updated_schema = self.tkeywords_handler.update_schema(schema, context={}, lang="en")

        # Assert tkeywords property is hidden
        tkeywords = updated_schema["properties"].get("tkeywords")
        self.assertIsNotNone(tkeywords)
        self.assertEqual(tkeywords["ui:widget"], "hidden")

    def test_tkeywords_handler_get_jsonschema_instance_translated_keywords(self):
        """
        Test for the get_jsonschema_instance of the tkeywords handler.
        In the setUp function we have set two keywords. In this test
        we test the translated keywords

        """

        # Create two instances of ThesaurusKeywordLabel
        ThesaurusKeywordLabel.objects.create(keyword=self.keyword1, lang="en", label="Localized Label 1")

        ThesaurusKeywordLabel.objects.create(keyword=self.keyword2, lang="en", label="Localized Label 2")

        # Add the keywords to the resource:
        self.resource.tkeywords.add(self.keyword1, self.keyword2)

        # Call the method
        result = self.tkeywords_handler.get_jsonschema_instance(
            resource=self.resource, field_name="tkeywords", context={}, errors=[], lang="en"
        )

        # Assertions for the results
        # Check the structure for "3-2-4-3-spatialscope"
        self.assertIn("3-2-4-3-spatialscope", result)
        spatial_scope_keywords = result["3-2-4-3-spatialscope"]
        self.assertEqual(len(spatial_scope_keywords), 1)
        self.assertEqual(spatial_scope_keywords, [{"id": "http://example.com/keyword1", "label": "Localized Label 1"}])

        # Check the structure for "3-2-4-1-gemet-inspire-themes"
        self.assertIn("3-2-4-1-gemet-inspire-themes", result)
        inspire_themes_keywords = result["3-2-4-1-gemet-inspire-themes"]
        self.assertEqual(len(inspire_themes_keywords), 1)
        self.assertEqual(inspire_themes_keywords, [{"id": "http://example.com/keyword2", "label": "Localized Label 2"}])

    def test_tkeywords_handler_get_jsonschema_instance_untranslated_keywords(self):
        """
        Test for the get_jsonschema_instance of the tkeywords handler.
        In the setUp function we have set two keywords. In this test
        we test the untranslated keywords

        """

        # Add the keywords to the resource without using the ThesaurusKeywordLabel
        self.resource.tkeywords.add(self.keyword1, self.keyword2)

        # Call the method
        result = self.tkeywords_handler.get_jsonschema_instance(
            resource=self.resource, field_name="tkeywords", context=self.context, errors=self.errors, lang=self.lang
        )

        # Assertions for the results
        # Check the structure for "3-2-4-3-spatialscope"
        self.assertIn("3-2-4-3-spatialscope", result)
        spatial_scope_keywords = result["3-2-4-3-spatialscope"]
        self.assertEqual(len(spatial_scope_keywords), 1)
        self.assertEqual(spatial_scope_keywords, [{"id": "http://example.com/keyword1", "label": "Alt Label 1"}])

        # Check the structure for "3-2-4-1-gemet-inspire-themes"
        self.assertIn("3-2-4-1-gemet-inspire-themes", result)
        inspire_themes_keywords = result["3-2-4-1-gemet-inspire-themes"]
        self.assertEqual(len(inspire_themes_keywords), 1)
        self.assertEqual(inspire_themes_keywords, [{"id": "http://example.com/keyword2", "label": "Alt Label 2"}])

    def test_tkeywords_handler_update_resource(self):
        """
        Ensures that the method will import the keyword1 and
        the keyword2 in the database. It will not import the
        keyword3 since it is not included in the ThesaurusKeyword
        model
        """

        # JSON instance to simulate the input
        json_instance = {
            "tkeywords": {
                "thes-1": [
                    {"id": "http://example.com/keyword1", "label": "Keyword 1"},
                    {"id": "http://example.com/keyword2", "label": "Keyword 2"},
                ],
                "thes-2": [
                    {"id": "http://example.com/keyword3", "label": "Keyword 3"},
                ],
            }
        }

        # Call the method
        self.tkeywords_handler.update_resource(
            resource=self.resource,
            field_name="tkeywords",
            json_instance=json_instance,
            context=self.context,
            errors=self.errors,
        )

        # Fetch the resource from the database and verify its tkeywords after running the update_resource
        updated_keywords = self.resource.tkeywords.all()

        # Check the correct keywords are associated
        expected_keywords = ThesaurusKeyword.objects.filter(
            about__in=["http://example.com/keyword1", "http://example.com/keyword2"]
        )

        self.assertQuerysetEqual(
            updated_keywords.order_by("id"), expected_keywords.order_by("id"), transform=lambda x: x
        )

        # Ensure that only the keyword1 and keyword2 are stored in the database
        self.assertEqual(len(updated_keywords), 2)

    # Tests for the sparse handler

    def test_sparse_handler_update_schema(self):

        # Register two fields in the SparseFieldRegistry
        sparse_field_registry.register(
            field_name="new_sparse_field", schema={"type": "string", "title": "New Sparse Field"}, after="field1"
        )

        sparse_field_registry.register(
            field_name="another_sparse_field",
            schema={"type": "number", "title": "Another Sparse Field"},
            after="field2",
        )

        # Call the update_schema method using the fake_schema defined in the setUp method
        updated_schema = self.sparse_handler.update_schema(self.fake_schema, self.context)

        # Assert that the new fields have been added
        self.assertIn("new_sparse_field", updated_schema["properties"])
        self.assertIn("another_sparse_field", updated_schema["properties"])

        # Check that the fields have the correct type
        self.assertEqual(updated_schema["properties"]["new_sparse_field"]["type"], "string")
        self.assertEqual(updated_schema["properties"]["another_sparse_field"]["type"], "number")

        # Check that the handler info was added
        self.assertEqual(updated_schema["properties"]["new_sparse_field"]["geonode:handler"], "sparse")
        self.assertEqual(updated_schema["properties"]["another_sparse_field"]["geonode:handler"], "sparse")

        # Check the order of the schema
        self.assertEqual(
            list(updated_schema["properties"].keys()),
            ["field1", "new_sparse_field", "field2", "another_sparse_field", "field3"],
        )

    def test_sparse_handler_get_jsonschema_instance(self):

        CONTEXT_ID = "sparse"

        # Set up the context
        self.context = {
            CONTEXT_ID: {
                "schema": {
                    "properties": {
                        "string_field": {"type": "string"},
                        "number_field": {"type": "number"},
                        "integer_field": {"type": "integer"},
                        "nullable_field": {"type": ["null", "string"]},
                        "array_field": {"type": "array"},
                        "object_field": {"type": "object"},
                    }
                },
                "fields": {
                    "string_field": "test string",
                    "number_field": "42.0",
                    "integer_field": "7",
                    "nullable_field": None,
                    "array_field": '["item1", "item2"]',
                    "object_field": '{"key": "value"}',
                },
            }
        }

        # Test string field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "string_field", self.context, self.errors)
        self.assertEqual(result, "test string")

        # Test number field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "number_field", self.context, self.errors)
        self.assertEqual(result, 42.0)

        # Test integer field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "integer_field", self.context, self.errors)
        self.assertEqual(result, 7)

        # Test nullable field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "nullable_field", self.context, self.errors)
        self.assertIsNone(result)

        # Test array field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "array_field", self.context, self.errors)
        self.assertEqual(result, ["item1", "item2"])

        # Test object field
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "object_field", self.context, self.errors)
        self.assertEqual(result, {"key": "value"})

        # Test missing field with no default and non-nullable
        # with self.assertRaises(UnsetFieldException):
        #    self.sparse_handler.get_jsonschema_instance(self.resource, "missing_field", context, self.errors)

        # Test invalid number field
        self.context[CONTEXT_ID]["fields"]["number_field"] = "invalid_number"
        with self.assertRaises(UnsetFieldException):
            self.sparse_handler.get_jsonschema_instance(self.resource, "number_field", self.context, self.errors)

        # Test invalid integer field
        self.context[CONTEXT_ID]["fields"]["integer_field"] = "invalid_integer"
        with self.assertRaises(UnsetFieldException):
            self.sparse_handler.get_jsonschema_instance(self.resource, "integer_field", self.context, self.errors)

        # Test unhandled type
        self.context[CONTEXT_ID]["schema"]["properties"]["unknown_field"] = {"type": "unknown"}
        self.context[CONTEXT_ID]["fields"]["unknown_field"] = "some_value"
        result = self.sparse_handler.get_jsonschema_instance(self.resource, "unknown_field", self.context, self.errors)
        self.assertIsNone(result)

    def test_sparse_handler_update_resource(self):

        self.context = {
            "sparse": {
                "schema": {
                    "properties": {
                        "string_field": {"type": "string"},
                        "number_field": {"type": "number"},
                        "integer_field": {"type": "integer"},
                        "nullable_field": {"type": ["null", "string"]},
                        "array_field": {"type": "array"},
                        "object_field": {"type": "object"},
                    }
                }
            }
        }

        # Test string field
        json_instance_string_field = {"string_field": "updated string"}
        self.sparse_handler.update_resource(
            self.resource, "string_field", json_instance_string_field, self.context, self.errors
        )
        sparse_field = SparseField.objects.get(resource=self.resource, name="string_field")
        self.assertEqual(sparse_field.value, "updated string")

        # Test number field
        json_instance_number_field = {"number_field": 123.45}
        self.sparse_handler.update_resource(
            self.resource, "number_field", json_instance_number_field, self.context, self.errors
        )
        sparse_field = SparseField.objects.get(resource=self.resource, name="number_field")
        self.assertEqual(float(sparse_field.value), 123.45)

        # Test nullable field
        json_instance_nullable_field = {"nullable_field": None}
        self.sparse_handler.update_resource(
            self.resource, "nullable_field", json_instance_nullable_field, self.context, self.errors
        )
        sparse_field = SparseField.objects.filter(resource=self.resource, name="nullable_field").first()
        self.assertIsNone(sparse_field)

        # Test array field
        json_instance_array_field = {"array_field": ["item1", "item2"]}
        self.sparse_handler.update_resource(
            self.resource, "array_field", json_instance_array_field, self.context, self.errors
        )
        sparse_field = SparseField.objects.get(resource=self.resource, name="array_field")
        self.assertEqual(sparse_field.value, '["item1", "item2"]')

        # Test object field
        json_instance_object_field = {"object_field": {"key": "value"}}
        self.sparse_handler.update_resource(
            self.resource, "object_field", json_instance_object_field, self.context, self.errors
        )
        sparse_field = SparseField.objects.get(resource=self.resource, name="object_field")
        self.assertEqual(sparse_field.value, '{"key": "value"}')

        # Test invalid number
        json_instance_invalid_number = {"number_field": "not_a_number"}
        self.sparse_handler.update_resource(
            self.resource, "number_field", json_instance_invalid_number, self.context, self.errors
        )
        self.assertIn("Error parsing number", str(self.errors))

        # Test invalid integer number
        json_instance_invalid_int_number = {"integer_field": "not_an_integer"}
        self.sparse_handler.update_resource(
            self.resource, "integer_field", json_instance_invalid_int_number, self.context, self.errors
        )
        self.assertIn("Error parsing integer", str(self.errors))
