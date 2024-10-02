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


from unittest.mock import patch
from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers
from geonode.metadata.engine import engine, Field, FieldsConverter
from rest_framework.test import APITestCase


class MetadataEngineTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        cls.converter = FieldsConverter()

    def test_fields_should_be_converted_with_biding_false(self):
        """
        Given an input list, they should be converted into the
        serializer like object
        """
        input_list = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]
        output = self.converter.convert_fields(input_list, bind=False)
        self.assertIsNotNone(output)
        self.assertTrue("title" in output.keys())
        field = output["title"]
        self.assertIsNone(field.source)

    def test_fields_should_be_converted_with_biding_true(self):
        """
        Given an input list, they should be converted into the
        serializer like object
        """
        input_list = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]
        output = self.converter.convert_fields(input_list, bind=True)
        self.assertIsNotNone(output)
        self.assertTrue("title" in output.keys())
        field = output["title"]
        self.assertIsNotNone(field.source)

    def test_field_validate(self):  # TODO test needs to be done
        """
        Test to validate the .validate function for the field
        """
        input_list = [{"title": serializers.CharField(help_text="test")}]
        self.converter.validate(input_list)

    def test_metadata_save_metadata(self):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        test_metadata_save_metadata works as expected
        """

    @patch("geonode.metadata.engine.MetadataEngine.get_data_by_pk")
    def test_get_data_by_pk(self, patched_value):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        get_data_by_pk works as expected
        """
        # should return the field of the metadata with its value
        expected = [{"metadata_field": "metadata_value"}]
        patched_value.return_value = expected
        self.assertListEqual(expected, engine.get_data_by_pk(pk=1))

    @patch("geonode.metadata.engine.MetadataEngine.get_data")
    def test_get_data(self, patched_value):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        get_data works as expected
        """
        # should return the field of the metadata with its value
        expected = [{"metadata_field": "metadata_value"}]
        patched_value.return_value = expected
        self.assertListEqual(expected, engine.get_data())

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    def test_get_fields(self, patched_value):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        get_fields works as expected.
        Should return the list of the metadata field as metadata object
        """
        expected = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]
        patched_value.return_value = expected

        self.assertListEqual(patched_value, expected)

    def test_validate_fields(self):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        validate_fields works as expected
        """

    def test_get_engine_lists(self):  # TODO this test should be improved during the development
        """
        Test to ensure that the metadata engine function
        get_engine_lists works as expected
        """


class TestMetadataAPI(APITestCase):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls) -> None:
        cls.user = get_user_model().objects.filter(username="admin").first()
        cls.url = reverse("metadata-list")
        super().setUpClass()

    def test_anonymous_cannot_see_metadata_list(self):
        """
        Anonymous cannot see the metadata.
        TODO: we should show only the metadata where the user
        has perms on the relative resource
        """
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    @patch("geonode.metadata.engine.MetadataEngine.get_data")
    def test_get_should_return_the_list_of_metadata(self, get_data, get_fields):
        """
        The list serializer should return the list of the available metadata
        """
        get_data.return_value = [{"title": "nice title"}]
        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")

        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

        output = response.json()

        self.assertListEqual(output, [{"title": "nice title"}])

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    @patch("geonode.metadata.engine.MetadataEngine.get_data_by_pk")
    def test_retrieve_should_return_the_list_of_metadata_by_pk(self, get_data, get_fields):
        """
        The list serializer should return the list of the available metadata
        """
        get_data.return_value = {"title": "nice title"}
        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")

        response = self.client.get(reverse("metadata-detail", kwargs={"pk": 1}))
        self.assertEqual(200, response.status_code)

        output = response.json()

        self.assertDictEqual(output, {"title": "nice title"})

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    def test_post_for_create_metadata_raise_error_if_no_payload_is_passed(self, get_fields):
        """
        Raise error if the payload is passed in the call
        """
        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")
        response = self.client.post(reverse("metadata-list"), data={}, content_type="application/json")
        self.assertEqual(400, response.status_code)

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    def test_post_for_create_metadata_raise_error_with_missing_fields(self, get_fields):
        """
        Should raise error if some mandatory field is missing
        """
        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")
        data = {"different_field": "different value"}
        response = self.client.post(reverse("metadata-list"), data=data, format="json")
        self.assertEqual(400, response.status_code)
        self.assertDictEqual({"title": ["This field is required."]}, response.json())

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    @patch("geonode.metadata.engine.MetadataEngine.get_data_by_pk")
    def test_post_should_create_metadata(self, get_data, get_fields):
        """
        Should raise error if some mandatory field is missing
        """
        get_data.return_value = {"title": "nice title"}

        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")

        response = self.client.post(reverse("metadata-list"), data={"title": "some title"}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({"title": "nice title"}, response.json())

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    @patch("geonode.metadata.engine.MetadataEngine.get_data_by_pk")
    def test_patch_raise_error_if_pk_is_missing(self, get_data, get_fields):
        """
        Should raise error if some mandatory field is missing
        """
        get_data.return_value = {"title": "nice title"}

        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")

        response = self.client.patch(reverse("metadata-list"), data={"title": "some title"}, format="json")
        self.assertEqual(403, response.status_code)

    @patch("geonode.metadata.engine.MetadataEngine.get_fields")
    @patch("geonode.metadata.engine.MetadataEngine.get_data_by_pk")
    def test_patch_should_update_metadata(self, get_data, get_fields):
        """
        Should raise error if some mandatory field is missing
        """
        get_data.return_value = {"title": "nice title"}

        get_fields.return_value = [
            Field(
                name="title",  # mandatory
                type="str",  # mandatory
                kwargs={"max_length": 255, "help_text": "name by which the cited resource is known"},  # optional
            )
        ]

        self.client.login(username=self.user.username, password="admin")

        response = self.client.patch(
            reverse("metadata-detail", kwargs={"pk": 1}), data={"title": "some title"}, format="json"
        )
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({"title": "nice title"}, response.json())
