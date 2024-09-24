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
from rest_framework.test import APITransactionTestCase

from guardian.shortcuts import assign_perm, get_anonymous_user
from geonode import settings

from geonode.base.populate_test_data import create_models
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.documents.models import Document

logger = logging.getLogger(__name__)


class DocumentsApiTests(APITransactionTestCase):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        create_models(b"document")
        create_models(b"map")
        create_models(b"dataset")
        self.admin = get_user_model().objects.get(username="admin")
        self.url = reverse("documents-list")
        self.invalid_file_path = f"{settings.PROJECT_ROOT}/tests/data/thesaurus.rdf"
        self.valid_file_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.no_title_file_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_sld.sld"

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

    def test_document_listing_advertised(self):
        document = Document.objects.first()
        document.advertised = False
        document.save()

        url = reverse("documents-list")

        payload = self.client.get(url)

        prev_count = payload.json().get("total")
        # the user can see only the advertised resources
        self.assertTrue(Document.objects.count() > prev_count)

        payload = self.client.get(f"{url}?advertised=True")
        # so if advertised is True, we dont see the advertised=False resource
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, prev_count)

        payload = self.client.get(f"{url}?advertised=False")
        # so if advertised is False, we see only the resource with advertised==False
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, 1)

        # if all is requested, we will see all the resources
        payload = self.client.get(f"{url}?advertised=all")
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, prev_count + 1)

        Document.objects.update(advertised=True)

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

    def test_uploading_doc_without_title(self):
        """
        A document should be uploaded without specifying a title
        """
        self.client.force_login(self.admin)
        payload = {"document": {"metadata_only": True, "file_path": self.no_title_file_path}}
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(201, actual.status_code)
        extension = actual.json().get("document", {}).get("extension", "")
        self.assertEqual("sld", extension)
        self.assertTrue(Document.objects.filter(title="test_sld.sld").exists())

    def test_patch_point_of_contact(self):
        document = Document.objects.first()
        url = urljoin(f"{reverse('documents-list')}/", f"{document.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"poc": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"metadata_author": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"processor": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        # check if all set processors are in the return json
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
        patch_data = {"publisher": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"custodian": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"distributor": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"resource_user": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"resource_provider": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"originator": [{"pk": uid} for uid in user_ids]}
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
        patch_data = {"principal_investigator": [{"pk": uid} for uid in user_ids]}
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

    def test_creation_should_create_the_doc_and_update_the_bbox(self):
        """
        If file_path is not available, should raise error
        """
        self.client.force_login(self.admin)
        payload = {
            "document": {
                "title": "New document for testing",
                "metadata_only": True,
                "file_path": self.valid_file_path,
                "extent": {"coords": [1123692.0, 5338214.0, 1339852.0, 5482615.0], "srid": "EPSG:3857"},
            },
        }
        actual = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(201, actual.status_code)
        extension = actual.json().get("document", {}).get("extension", "")
        self.assertEqual("xml", extension)
        doc = Document.objects.filter(title="New document for testing").all()
        self.assertTrue(doc.exists())
        x = doc.first()
        x.refresh_from_db()
        self.assertEqual("EPSG:3857", x.srid)
        self.assertEqual(actual.json()["document"].get("extent")["srid"], "EPSG:4326")
        self.assertEqual(
            actual.json()["document"].get("extent")["coords"],
            [10.094296982428332, 43.1721654049465, 12.03609530058109, 44.11086592050112],
        )

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
