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
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework import status
from django.utils.translation import gettext as _

from rest_framework.test import APITestCase
from geonode.metadata.settings import MODEL_SCHEMA
from geonode.metadata.manager import metadata_manager
from geonode.metadata.api.views import (
    ProfileAutocomplete,
    MetadataLinkedResourcesAutocomplete,
    MetadataRegionsAutocomplete,
    MetadataHKeywordAutocomplete,
    MetadataGroupAutocomplete,
)
from geonode.metadata.settings import METADATA_HANDLERS
from geonode.base.models import ResourceBase
from geonode.settings import PROJECT_ROOT
from geonode.base.models import (
    TopicCategory,
    License,
    Region,
    HierarchicalKeyword,
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    Thesaurus,
)
from geonode.groups.models import GroupProfile, GroupMember


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
        self.other_resource = ResourceBase.objects.create(
            title="Test other Resource", uuid=str(uuid4()), owner=self.test_user_1
        )
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

        # Setup the database
        TopicCategory.objects.create(identifier="cat1", gn_description="fake category 1")
        TopicCategory.objects.create(identifier="cat2", gn_description="fake category 2")
        License.objects.create(identifier="license1", name="fake license 1")
        License.objects.create(identifier="license2", name="fake license 2")
        Region.objects.create(code="fake_code_1", name="fake name 1")
        Region.objects.create(code="fake_code_2", name="fake name 2")
        HierarchicalKeyword.objects.create(name="fake_keyword_1", slug="fake keyword 1")
        HierarchicalKeyword.objects.create(name="fake_keyword_2", slug="fake keyword 2")

        # Create groups for the metadata group autocomplete
        self.group1 = GroupProfile.objects.create(title="Group A", slug="group_a")
        self.group2 = GroupProfile.objects.create(title="Group B", slug="group_b")

        # Create Thesaurus keywords for the Thesaurus autocomplete
        self.thesaurus = Thesaurus.objects.create(title="Spatial scope thesaurus", identifier="3-2-4-3-spatialscope")
        self.thesaurus_id = self.thesaurus.id
        # Create keywords for the thesaurus
        self.keyword1 = ThesaurusKeyword.objects.create(
            about="keyword1", alt_label="Alternative Label 1", thesaurus=self.thesaurus
        )
        self.keyword2 = ThesaurusKeyword.objects.create(
            about="keyword2", alt_label="Alternative Label 2", thesaurus=self.thesaurus
        )
        self.keyword3 = ThesaurusKeyword.objects.create(
            about="keyword3", alt_label="Alternative Label 3", thesaurus=self.thesaurus
        )

        ThesaurusKeywordLabel.objects.create(keyword=self.keyword1, label="Label 1", lang="en")
        ThesaurusKeywordLabel.objects.create(keyword=self.keyword2, label="Label 2", lang="en")
        ThesaurusKeywordLabel.objects.create(keyword=self.keyword3, label="Italiano etichetta", lang="it")

    def tearDown(self):
        super().tearDown()

    # tests for the encpoint metadata/schema
    def test_schema_valid_structure(self):
        """
        Ensure the returned basic structure of the schema
        """

        url = reverse("metadata-schema")

        # Make a GET request to the action
        response = self.client.get(url, format="json")

        # Assert that the response is in JSON format
        self.assertEqual(response["Content-Type"], "application/json")

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
    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_get_schema_instance_with_default_lang(self, mock_has_permission, mock_build_schema_instance):
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
    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_get_schema_instance_with_lang(self, mock_has_permission, mock_build_schema_instance):
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
    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_put_patch_schema_instance_with_no_errors(self, mock_has_permission, mock_update_schema_instance):
        """
        Test the success case of PATCH and PUT methods of the schema_instance
        """

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        fake_payload = {"field": "value"}

        # set the returned value of the mocked update_schema_instance with an empty dict
        errors = {}
        mock_update_schema_instance.return_value = errors

        response = self.client.put(url, data=fake_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            response.content, {"message": "The resource was updated successfully", "extraErrors": errors}
        )
        mock_update_schema_instance.assert_called_with(self.resource, fake_payload)

    @patch("geonode.metadata.manager.metadata_manager.update_schema_instance")
    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_put_patch_schema_instance_with_errors(self, mock_has_permission, mock_update_schema_instance):
        """
        Test the PATCH and PUT methods of the schema_instance in case of errors
        """

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        fake_payload = {"field": "value"}

        # Set fake errors
        errors = {"fake_error_1": "Field 'title' is required", "fake_error_2": "Invalid value for 'type'"}
        mock_update_schema_instance.return_value = errors

        response = self.client.put(url, data=fake_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertJSONEqual(
            response.content,
            {"message": "Some errors were found while updating the resource", "extraErrors": errors},
        )
        mock_update_schema_instance.assert_called_with(self.resource, fake_payload)

    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_put_patch_schema_instance_with_bad_payload(self, mock_has_permission):
        """
        Test the PUT method with an invalid json payload
        """

        url = reverse("metadata-schema_instance", kwargs={"pk": self.resource.pk})
        fake_payload = "I_AM_BAD"

        response = self.client.put(url, data=fake_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("geonode.base.api.permissions.UserHasPerms.has_permission", return_value=True)
    def test_resource_not_found(self, mock_has_permission):
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
        self.assertJSONEqual(response.content, {"message": "The dataset was not found"})

    # Tests for categories autocomplete
    def test_categories_autocomplete_no_query(self):
        """
        Test the response when no query parameter is provided
        """

        self.url = reverse("metadata_autocomplete_categories")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        self.assertIn({"id": "cat1", "label": _("fake category 1")}, results)
        self.assertIn({"id": "cat2", "label": _("fake category 2")}, results)

    def test_categories_autocomplete_with_query(self):
        """
        Test the response when a query parameter is provided
        """

        self.url = reverse("metadata_autocomplete_categories")
        response = self.client.get(self.url, {"q": "fake cat"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        self.assertIn({"id": "cat1", "label": _("fake category 1")}, results)
        self.assertIn({"id": "cat2", "label": _("fake category 2")}, results)

    def test_categories_autocomplete_with_query_one_match(self):
        """
        Test partial matches for the query parameter
        """

        self.url = reverse("metadata_autocomplete_categories")
        response = self.client.get(self.url, {"q": "fake category 2"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertIn({"id": "cat2", "label": _("fake category 2")}, results)

    def test_categories_autocomplete_with_query_no_match(self):
        """
        Test when no results match the query parameter
        """

        self.url = reverse("metadata_autocomplete_categories")
        response = self.client.get(self.url, {"q": "A missing category"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 0)

    # Tests for License autocomplete
    def test_license_autocomplete_no_query(self):
        """
        Test the response when no query parameter is provided
        """

        self.url = reverse("metadata_autocomplete_licenses")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        self.assertIn({"id": "license1", "label": _("fake license 1")}, results)
        self.assertIn({"id": "license2", "label": _("fake license 2")}, results)

    def test_license_autocomplete_with_query(self):
        """
        Test the response when a query parameter is provided
        """

        self.url = reverse("metadata_autocomplete_licenses")
        response = self.client.get(self.url, {"q": "fake lic"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        self.assertIn({"id": "license1", "label": _("fake license 1")}, results)
        self.assertIn({"id": "license2", "label": _("fake license 2")}, results)

    def test_license_autocomplete_with_query_one_match(self):
        """
        Test partial matches for the query parameter
        """

        self.url = reverse("metadata_autocomplete_licenses")
        response = self.client.get(self.url, {"q": "fake license 2"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertIn({"id": "license2", "label": _("fake license 2")}, results)

    def test_license_autocomplete_with_query_no_match(self):
        """
        Test when no results match the query parameter
        """

        self.url = reverse("metadata_autocomplete_licenses")
        response = self.client.get(self.url, {"q": "A missing category"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 0)

    # Tests for Profile autocomplete

    @patch("geonode.people.utils.get_available_users")
    def test_profile_autocomplete_no_query(self, mock_get_available_users):
        """
        Test that the queryset is restricted to available users
        """

        mocked_available_users = [self.test_user_1, self.test_user_2]

        mock_get_available_users.return_value = get_user_model().objects.filter(
            pk__in=[u.pk for u in mocked_available_users]
        )

        request = self.factory.get(reverse("metadata_autocomplete_users"))
        request.user = self.test_user_1

        view = ProfileAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "user_1")
        self.assertEqual(results[1]["label"], "user_2")

    @patch("geonode.people.utils.get_available_users")
    def test_profile_autocomplete_with_query(self, mock_get_available_users):
        """
        Test that the queryset is restricted to one user
        """

        mocked_available_users = [self.test_user_1, self.test_user_2]

        mock_get_available_users.return_value = get_user_model().objects.filter(
            pk__in=[u.pk for u in mocked_available_users]
        )

        request = self.factory.get(reverse("metadata_autocomplete_users"), {"q": "user_2"})
        request.user = self.test_user_1

        view = ProfileAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "user_2")

    @patch("geonode.people.utils.get_available_users")
    def test_profile_autocomplete_no_match(self, mock_get_available_users):
        """
        Test when there is no match of available users
        """

        mocked_available_users = [self.test_user_1, self.test_user_2]

        mock_get_available_users.return_value = get_user_model().objects.filter(
            pk__in=[u.pk for u in mocked_available_users]
        )

        request = self.factory.get(reverse("metadata_autocomplete_users"), {"q": "missing_user"})
        request.user = self.test_user_1

        view = ProfileAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 0)

    # Tests for MetadataLinkedResourcesAutocomplete view
    @patch("geonode.base.views.get_visible_resources")
    def test_linked_resources_autocomplete_with_query(self, mock_get_visible_resources):

        request = self.factory.get("/metadata/autocomplete/resources", {"q": "Test other Resource"})
        request.user = self.test_user_1

        # Mock the return value of get_visible_resources
        mock_get_visible_resources.return_value = [self.other_resource]

        view = MetadataLinkedResourcesAutocomplete.as_view()
        response = view(request)

        # Ensure the queryset was filtered by the query parameter
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "Test other Resource [resourcebase]")

    @patch("geonode.base.views.get_visible_resources")
    def test_linked_resources_autocomplete_without_query(self, mock_get_visible_resources):

        request = self.factory.get("/metadata/autocomplete/resources")
        request.user = self.test_user_1

        # Mock the return value of get_visible_resources
        mock_get_visible_resources.return_value = [self.resource, self.other_resource]

        view = MetadataLinkedResourcesAutocomplete.as_view()
        response = view(request)

        # Ensure the queryset was filtered by the query parameter
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "Test Resource [resourcebase]")
        self.assertEqual(results[1]["label"], "Test other Resource [resourcebase]")

    @patch("geonode.base.views.get_visible_resources")
    def test_linked_resources_autocomplete_no_match(self, mock_get_visible_resources):

        request = self.factory.get("/metadata/autocomplete/resources")
        request.user = self.test_user_1

        # Mock the return value of get_visible_resources
        mock_get_visible_resources.return_value = []

        view = MetadataLinkedResourcesAutocomplete.as_view()
        response = view(request)

        # Ensure the queryset was filtered by the query parameter
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]
        self.assertEqual(len(results), 0)

    # Tests for the Region autocomplete view

    def test_regions_autocomplete_without_query(self):
        """
        Test filtering the queryset with the 'q' parameter
        """
        # Simulate a request with a query parameter
        request = self.factory.get("/metadata/autocomplete/regions")

        view = MetadataRegionsAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "fake name 1")
        self.assertEqual(results[1]["label"], "fake name 2")

    def test_regions_autocomplete_with_general_query(self):
        """
        Test filtering the queryset with the 'q' parameter
        """
        # Simulate a request with a query parameter
        request = self.factory.get("/metadata/autocomplete/regions", {"q": "fake name"})

        view = MetadataRegionsAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "fake name 1")
        self.assertEqual(results[1]["label"], "fake name 2")

    def test_regions_autocomplete_one_match(self):
        """
        Test filtering the queryset with the 'q' parameter
        """
        # Simulate a request with a query parameter
        request = self.factory.get("/metadata/autocomplete/regions", {"q": "fake name 2"})

        view = MetadataRegionsAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "fake name 2")

    def test_regions_autocomplete_no_match(self):
        """
        Test filtering the queryset with the 'q' parameter
        """
        # Simulate a request with a query parameter
        request = self.factory.get("/metadata/autocomplete/regions", {"q": "missing region"})

        view = MetadataRegionsAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 0)

    # Tests for hkeyword_autocomplete view
    def test_hkeyword_autocomplete_without_query(self):

        request = self.factory.get("/metadata/autocomplete/hkeywords")

        view = MetadataHKeywordAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert all keywords are returned
        self.assertEqual(len(results), 2)
        self.assertIn("fake_keyword_1", results)
        self.assertIn("fake_keyword_2", results)

    def test_hkeyword_autocomplete_with_query(self):

        request = self.factory.get("/metadata/autocomplete/hkeywords", {"q": "fake keyword"})

        view = MetadataHKeywordAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert all keywords are returned
        self.assertEqual(len(results), 2)
        self.assertIn("fake_keyword_1", results)
        self.assertIn("fake_keyword_2", results)

    def test_hkeyword_autocomplete_one_match(self):

        request = self.factory.get("/metadata/autocomplete/hkeywords", {"q": "fake keyword 2"})

        view = MetadataHKeywordAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert all keywords are returned
        self.assertEqual(len(results), 1)
        self.assertIn("fake_keyword_2", results)

    def test_hkeyword_autocomplete_no_match(self):

        request = self.factory.get("/metadata/autocomplete/hkeywords", {"q": "missing keyword"})

        view = MetadataHKeywordAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert all keywords are returned
        self.assertEqual(len(results), 0)

    # Tests for the Metadata GroupProfile autocomplete
    def test_metadata_group_autocomplete_no_user(self):
        """
        Test group autocomplete when the user is None
        """
        request = self.factory.get("/metadata/autocomplete/groups")
        request.user = None
        view = MetadataGroupAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])

    def test_metadata_group_autocomplete_superuser(self):
        """
        Test group autocomplete when the user is SuperUser
        """

        # Create a superuser
        superuser = get_user_model().objects.create_superuser(
            username="superuser", email="superuser@example.com", password="password"
        )

        request = self.factory.get("/metadata/autocomplete/groups")
        request.user = superuser
        view = MetadataGroupAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "Group A")
        self.assertEqual(results[1]["label"], "Group B")

    def test_metadata_group_autocomplete_staff_user(self):
        """
        Test group autocomplete when the user is staff user
        """

        # Create a staff user
        staff_user = get_user_model().objects.create_user(
            username="staff", email="staff@example.com", password="password", is_staff=True
        )

        request = self.factory.get("/metadata/autocomplete/groups")
        request.user = staff_user
        view = MetadataGroupAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "Group A")
        self.assertEqual(results[1]["label"], "Group B")

    def test_metadata_group_autocomplete_simple_user(self):
        """
        Test group autocomplete when the user is a simple user
        with an associated group (Group B)
        """

        # Associate Group B with test_user_1
        GroupMember.objects.create(user=self.test_user_1, group=self.group2)

        request = self.factory.get("/metadata/autocomplete/groups")
        request.user = self.test_user_1
        view = MetadataGroupAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "Group B")

    def test_metadata_group_autocomplete_superuser_with_query(self):
        """
        Test group autocomplete when the user is SuperUser
        and creates a specific query
        """
        superuser = get_user_model().objects.create_superuser(
            username="superuser", email="superuser@example.com", password="password"
        )

        request = self.factory.get("/metadata/autocomplete/groups", {"q": "Group A"})
        request.user = superuser
        view = MetadataGroupAutocomplete.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        results = json.loads(response.content)["results"]

        # Assert the results match the query
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "Group A")

    # Tests for Thesaurus autocomplete

    def test_tkeywords_autocomplete_no_query(self):

        url = reverse("metadata_autocomplete_tkeywords", kwargs={"thesaurusid": self.thesaurus_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]
        self.assertEqual(len(results), 3)

        self.assertIn({"id": "keyword1", "label": "Label 1"}, results)
        self.assertIn({"id": "keyword2", "label": "Label 2"}, results)

        # Check that untranslated keywords are prefixed with "!"
        self.assertIn({"id": "keyword3", "label": "! Alternative Label 3"}, results)

    def test_tkeywords_autocomplete_with_query(self):
        """
        Test of the tkeywords autocomplete view using a specific query.
        Keep in mind that the non-translated keywords will be included
        in the result
        """

        url = reverse("metadata_autocomplete_tkeywords", kwargs={"thesaurusid": self.thesaurus_id})
        response = self.client.get(url, {"q": "Label 1"})
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        # Ensure that the Label 2 is not included in the result
        self.assertEqual(len(results), 2)
        self.assertIn({"id": "keyword1", "label": "Label 1"}, results)
        self.assertIn({"id": "keyword3", "label": "! Alternative Label 3"}, results)

    # Manager tests

    def test_registry_and_add_handler(self):

        self.assertEqual(set(metadata_manager.handlers.keys()), set(METADATA_HANDLERS.keys()))
        for handler_id in METADATA_HANDLERS.keys():
            self.assertIn(handler_id, metadata_manager.handlers)

    @patch(
        "geonode.metadata.manager.metadata_manager.root_schema",
        new_callable=lambda: {
            "title": "Test Schema",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "integer", "geonode:required": True},
            },
        },
    )
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
    @patch("geonode.metadata.manager.Thesaurus.objects.filter")
    def test_get_schema(self, mock_db_value, mock_setitem, mock_get, mock_build_schema):

        lang = "en"
        expected_schema = self.fake_schema
        thesaurus_date = "some_date_value"

        # Mock the Thesaurus.objects.filter().first() method to return the thesaurus_date
        mock_db_value.return_value.values_list.return_value.first.return_value = thesaurus_date

        # Case when the schema is already in cache
        mock_get.return_value = {"schema": expected_schema, "date": thesaurus_date}
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
        mock_setitem.assert_called_once_with(str(lang), {"schema": expected_schema, "date": "some_date_value"})
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
            self.assertEqual(errors["field2"]["__errors"], ["Error while processing this field: Error in handler2"])

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
