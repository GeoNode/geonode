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

from django.contrib.auth import get_user_model
from django.test import RequestFactory

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.base.models import ResourceBase
from geonode.settings import PROJECT_ROOT
from geonode.metadata.handlers.base import BaseHandler
from geonode.metadata.tests.utils import MockSubHandler

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
        self.resource = ResourceBase.objects.create(title="Test Resource", uuid=str(uuid4()), owner=self.test_user_1)
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

        self.fake_subhandlers = {
            "date": MockSubHandler,
            "date_type": MockSubHandler,
            "category": MockSubHandler
        }

        # Handlers
        self.base_handler = BaseHandler()

    def tearDown(self):
        super().tearDown()

    # Tests for the Base handler
    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_base_handler_update_schema(self, mock_subhandlers):

        # Use of mock_subhandlers as a dictionary
        mock_subhandlers.update(self.fake_subhandlers)
        
        # Only the path is defined since it is loaded inside the base handler
        self.base_handler.json_base_schema = self.fake_base_schema_path

        # Input schema and context
        jsonschema = self.model_schema

        # Call the method
        updated_schema = self.base_handler.update_schema(jsonschema, self.context, self.lang)

        # Check the full base schema
        for field in self.fake_base_schema:
            self.assertIn(field, updated_schema["properties"])

        # Check subhandler execution
        self.assertEqual(updated_schema["properties"]["date"].get("oneOf"), [{"const": "fake const", "title": "fake title"}])
        self.assertEqual(updated_schema["properties"]["date_type"].get("oneOf"), [{"const": "fake const", "title": "fake title"}])
        self.assertNotIn("oneOf", updated_schema["properties"]["uuid"])
        self.assertNotIn("oneOf", updated_schema["properties"]["title"])
        self.assertNotIn("oneOf", updated_schema["properties"]["abstract"])

        # Check geonode:handler addition
        self.assertEqual(updated_schema["properties"]["date"].get("geonode:handler"), "base")
        self.assertEqual(updated_schema["properties"]["date_type"].get("geonode:handler"), "base")

    def test_base_handler_get_jsonschema_instance_without_subhandlers(self):
        
        fieldname = "title"
        self.assertTrue(hasattr(self.resource, fieldname), f"Field '{fieldname}' does not exist.")
        expected_field_value = self.resource.title

        # Call the method
        field_value = self.base_handler.get_jsonschema_instance(self.resource, fieldname, self.context, self.errors, lang=None)
        self.assertEqual(expected_field_value, field_value)
        self.assertEqual(self.errors, {})

    @patch("geonode.metadata.handlers.base.SUBHANDLERS", new_callable=dict)
    def test_base_handler_get_jsonschema_instance_with_subhandlers(self, mock_subhandlers):
        
        field_name = "category" # A field name which is included in the  SUBHANDLERS
        
        # Create a fake resource
        fake_resource = MagicMock()
        fake_resource.category = MagicMock()
        fake_resource.category.identifier = "mocked_category_value"
        expected_field_value = fake_resource.category.identifier

        # Use of mock_subhandlers as a dictionary
        mock_subhandlers.update(self.fake_subhandlers)

        # Call the method
        field_value = self.base_handler.get_jsonschema_instance(
            resource=fake_resource,
            field_name=field_name,
            context=self.context,
            errors=self.errors,
            lang=self.lang
            )
        
        self.assertEqual(expected_field_value, field_value)


        