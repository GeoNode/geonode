#########################################################################
#
# Copyright (C) 2016 OSGeo
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
import logging

from django.contrib.auth import get_user_model
from urllib.parse import urljoin

from django.urls import reverse
from rest_framework.test import APITestCase

from guardian.shortcuts import assign_perm, get_anonymous_user
from geonode import settings

from geonode.base.populate_test_data import create_models
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.documents.models import Document

logger = logging.getLogger(__name__)


class DocumentsApiTests(APITestCase):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        create_models(b"document")
        create_models(b"map")
        create_models(b"dataset")
        self.admin = get_user_model().objects.get(username="admin")
        self.url = reverse("documents-list")
        self.invalid_file_path = f"{settings.PROJECT_ROOT}/tests/data/thesaurus.rdf"
        self.valid_file_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"

    def test_documents(self):
        """
        Ensure we can access the Documents list.
        """
        url = reverse("documents-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 9)
        # Pagination
        self.assertEqual(len(response.data["documents"]), 9)
        logger.debug(response.data)

        for _l in response.data["documents"]:
            self.assertTrue(_l["resource_type"], "document")

        # Get Linked Resources List
        resource = Document.objects.first()

        url = urljoin(f"{reverse('documents-detail', kwargs={'pk': resource.pk})}/", "linked_resources/")
        assign_perm("base.view_resourcebase", get_anonymous_user(), resource.get_self_resource())
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        # import json
        # logger.error(f"{json.dumps(layers_data)}")

    def test_extra_metadata_included_with_param(self):
        resource = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{resource.pk}")
        data = {"include[]": "metadata"}

        response = self.client.get(url, format="json", data=data)
        self.assertIsNotNone(response.data["document"].get("metadata"))

        response = self.client.get(url, format="json")
        self.assertNotIn("metadata", response.data["document"])

    def test_creation_return_error_if_file_is_not_passed(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        payload = {"document": {"title": "New document", "metadata_only": True}}
        expected = {
            "success": False,
            "errors": ["A file, file path or URL must be speficied"],
            "code": "document_exception",
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(400, actual.status_code)
        self.assertDictEqual(expected, actual.json())

    def test_creation_return_error_if_file_is_none(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        payload = {"document": {"title": "New document", "metadata_only": True, "file_path": None, "doc_file": None}}
        expected = {
            "success": False,
            "errors": ["A file, file path or URL must be speficied"],
            "code": "document_exception",
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(400, actual.status_code)
        self.assertDictEqual(expected, actual.json())

    def test_creation_should_rase_exec_for_unsupported_files(self):
        self.client.force_login(self.admin)
        payload = {"document": {"title": "New document", "metadata_only": True, "file_path": self.invalid_file_path}}
        expected = {
            "success": False,
            "errors": ["The file provided is not in the supported extensions list"],
            "code": "document_exception",
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(400, actual.status_code)
        self.assertDictEqual(expected, actual.json())

    def test_creation_should_create_the_doc(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        payload = {
            "document": {"title": "New document for testing", "metadata_only": True, "file_path": self.valid_file_path}
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(201, actual.status_code)
        extension = actual.json().get("document", {}).get("extension", "")
        self.assertEqual("xml", extension)
        self.assertTrue(Document.objects.filter(title="New document for testing").exists())

    def test_file_path_and_doc_path_are_not_returned(self):
        """
        If file_path and doc_path should not be visible
        from the GET payload
        """
        actual = self.client.get(self.url)
        self.assertEqual(200, actual.status_code)
        _doc_payload = actual.json().get("document", {})
        self.assertFalse("file_path" in _doc_payload)
        self.assertFalse("doc_path" in _doc_payload)

    def test_creation_from_url_should_create_the_doc(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        doc_url = "https://example.com/image"
        payload = {
            "document": {
                "title": "New document from URL for testing",
                "metadata_only": False,
                "doc_url": doc_url,
                "extension": "jpeg",
            }
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(201, actual.status_code)
        created_doc_url = actual.json().get("document", {}).get("doc_url", "")
        self.assertEqual(created_doc_url, doc_url)

    def test_remote_document_is_marked_remote(self):
        """Tests creating an external document set its sourcetype to REMOTE."""
        self.client.force_login(self.admin)
        doc_url = "https://example.com/image"
        payload = {
            "document": {
                "title": "A remote document is remote",
                "doc_url": doc_url,
                "extension": "jpeg",
            }
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(201, actual.status_code)
        created_sourcetype = actual.json().get("document", {}).get("sourcetype", "")
        self.assertEqual(created_sourcetype, SOURCE_TYPE_REMOTE)

    def test_either_path_or_url_doc(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        doc_url = "https://example.com/image"
        payload = {
            "document": {
                "title": "New document from URL for testing",
                "metadata_only": False,
                "doc_url": doc_url,
                "file_path": self.valid_file_path,
                "extension": "jpeg",
            }
        }
        actual = self.client.post(self.url, data=payload, format="json")
        expected = {
            "success": False,
            "errors": ["Either a file or a URL must be specified, not both"],
            "code": "document_exception",
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(400, actual.status_code)
        self.assertDictEqual(expected, actual.json())
