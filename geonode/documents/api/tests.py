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
import os
import logging

from django.contrib.auth import get_user_model
from urllib.parse import urljoin

from django.urls import reverse
from rest_framework.test import APITestCase

from guardian.shortcuts import assign_perm, get_anonymous_user
from geonode import settings

from geonode.base.populate_test_data import create_models
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
            "errors": ["A file path or a file must be speficied"],
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
            "errors": ["A file path or a file must be speficied"],
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
            "errors": ["The file provided is not in the supported extension file list"],
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
        cloned_path = actual.json().get("document", {}).get("file_path", "")[0]
        extension = actual.json().get("document", {}).get("extension", "")
        self.assertTrue(os.path.exists(cloned_path))
        self.assertEqual("xml", extension)
        self.assertTrue(Document.objects.filter(title="New document for testing").exists())

        if cloned_path:
            os.remove(cloned_path)

    def test_patch_point_of_contact(self):
        document = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{document.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"poc": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [poc.get("pk") for poc in response.json().get("document").get("poc")] for user_id in user_ids
            )
        )
        # Resetting all point of contact
        response = self.client.patch(url, data={"poc": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [poc.get("pk") for poc in response.json().get("document").get("poc")]
                for user_id in user_ids
            )
        )

    def test_patch_metadata_author(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"metadata_author": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    metadata_author.get("pk")
                    for metadata_author in response.json().get("document").get("metadata_author")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all metadata authors
        response = self.client.patch(url, data={"metadata_author": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    metadata_author.get("pk")
                    for metadata_author in response.json().get("document").get("metadata_author")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_processor(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"processor": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [processor.get("pk") for processor in response.json().get("document").get("processor")]
                for user_id in user_ids
            )
        )
        # Resetting all processors
        response = self.client.patch(url, data={"processor": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [processor.get("pk") for processor in response.json().get("document").get("processor")]
                for user_id in user_ids
            )
        )

    def test_patch_publisher(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"publisher": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [publisher.get("pk") for publisher in response.json().get("document").get("publisher")]
                for user_id in user_ids
            )
        )
        # Resetting all publishers
        response = self.client.patch(url, data={"publisher": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [publisher.get("pk") for publisher in response.json().get("document").get("publisher")]
                for user_id in user_ids
            )
        )

    def test_patch_custodian(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"custodian": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [custodian.get("pk") for custodian in response.json().get("document").get("custodian")]
                for user_id in user_ids
            )
        )
        # Resetting all custodians
        response = self.client.patch(url, data={"custodian": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [custodian.get("pk") for custodian in response.json().get("document").get("custodian")]
                for user_id in user_ids
            )
        )

    def test_patch_distributor(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"distributor": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [distributor.get("pk") for distributor in response.json().get("document").get("distributor")]
                for user_id in user_ids
            )
        )
        # Resetting all distributers
        response = self.client.patch(url, data={"distributor": []}, format="json")

        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [distributor.get("pk") for distributor in response.json().get("document").get("distributor")]
                for user_id in user_ids
            )
        )

    def test_patch_resource_user(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"resource_user": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [resource_user.get("pk") for resource_user in response.json().get("document").get("resource_user")]
                for user_id in user_ids
            )
        )
        # Resetting all resource users
        response = self.client.patch(url, data={"resource_user": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    resource_user.get("pk") for resource_user in response.json().get("document").get("resource_user")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_resource_provider(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"resource_provider": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    resource_provider.get("pk")
                    for resource_provider in response.json().get("document").get("resource_provider")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all principal investigator
        response = self.client.patch(url, data={"resource_provider": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    resource_provider.get("pk")
                    for resource_provider in response.json().get("document").get("resource_provider")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_originator(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")

        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"originator": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [originator.get("pk") for originator in response.json().get("document").get("originator")]
                for user_id in user_ids
            )
        )
        # Resetting all originators
        response = self.client.patch(url, data={"originator": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [originator.get("pk") for originator in response.json().get("document").get("originator")]
                for user_id in user_ids
            )
        )

    def test_patch_principal_investigator(self):
        layer = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"principal_investigator": [{"id": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    principal_investigator.get("pk")
                    for principal_investigator in response.json().get("document").get("principal_investigator")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all principal investigator
        response = self.client.patch(url, data={"principal_investigator": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    principal_investigator.get("pk")
                    for principal_investigator in response.json().get("document").get("principal_investigator")
                ]
                for user_id in user_ids
            )
        )