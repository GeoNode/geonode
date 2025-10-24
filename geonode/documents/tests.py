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

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

"""
import os
import io
import json
import gisdata

from PIL import Image

from unittest.mock import patch
from urllib.parse import urlparse
from pathlib import Path

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat

from guardian.shortcuts import get_anonymous_user

from geonode.assets.utils import create_asset_and_link, get_default_asset
from geonode.maps.models import Map
from geonode.compat import ensure_string
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.documents.apps import DocumentsAppConfig
from geonode.resource.manager import resource_manager
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.tests.utils import NotificationsTestsHelper
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP
from geonode.documents.models import Document

from geonode.base.populate_test_data import all_public, create_models, create_single_doc
from geonode.upload.api.exceptions import FileUploadLimitException

from .forms import DocumentCreateForm
from geonode.security.registry import permissions_registry


TEST_GIF = os.path.join(os.path.dirname(__file__), "tests/data/img.gif")


class DocumentsTest(GeoNodeBaseTestSupport):
    type = "document"
    IMAGE_BYTES = (
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    perm_spec = {
        "users": {"admin": ["change_resourcebase", "change_resourcebase_permissions", "view_resourcebase"]},
        "groups": {},
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # ... model creation
        create_models("map")
        create_models("document")
        all_public()

        # Moved static computations here:
        cls.project_root = os.path.abspath(os.path.dirname(__file__))
        cls.anonymous_user = get_anonymous_user()

    def setUp(self):
        super().setUp()
        self.project_root = self.__class__.project_root
        self.anonymous_user = self.__class__.anonymous_user
        self.imgfile = io.BytesIO(self.__class__.IMAGE_BYTES)

    def test_document_mimetypes_rendering(self):
        ARCHIVETYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == "archive"]
        AUDIOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == "audio"]
        IMGTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == "image"]
        VIDEOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == "video"]
        self.assertIsNotNone(ARCHIVETYPES)
        self.assertIsNotNone(AUDIOTYPES)
        self.assertIsNotNone(IMGTYPES)
        self.assertIsNotNone(VIDEOTYPES)

        # Make sure we won't have template rendering issues
        self.assertTrue("dwg" in ARCHIVETYPES)
        self.assertTrue("dxf" in ARCHIVETYPES)
        self.assertTrue("tif" in ARCHIVETYPES)
        self.assertTrue("tiff" in ARCHIVETYPES)
        self.assertTrue("pbm" in ARCHIVETYPES)

    @patch("geonode.documents.tasks.create_document_thumbnail")
    def test_create_document_with_no_rel(self, thumb):
        """Tests the creation of a document with no relations"""
        thumb.return_value = True

        superuser = get_user_model().objects.get(pk=2)
        c = Document.objects.create(owner=superuser, title="theimg")
        _, _ = create_asset_and_link(c, superuser, [TEST_GIF])
        c.set_default_permissions()
        self.assertEqual(Document.objects.get(pk=c.id).title, "theimg")

    def test_remote_document_is_marked_remote(self):
        """Tests creating an external document set its sourcetype to REMOTE."""
        self.client.login(username="admin", password="admin")
        form_data = {
            "title": "A remote document through form is remote",
            "doc_url": "http://www.geonode.org/map.pdf",
        }

        response = self.client.post(reverse("document_upload"), data=form_data)

        self.assertEqual(response.status_code, 302)

        d = Document.objects.get(title="A remote document through form is remote")
        self.assertEqual(d.sourcetype, SOURCE_TYPE_REMOTE)

    def test_download_is_not_ajax_safe(self):
        """Remote document is mark as not safe."""
        self.client.login(username="admin", password="admin")
        form_data = {
            "title": "A remote document through form is remote",
            "doc_url": "https://development.demo.geonode.org/static/mapstore/img/geonode-logo.svg",
        }

        response = self.client.post(reverse("document_upload"), data=form_data)

        self.assertEqual(response.status_code, 302)

        d = Document.objects.get(title="A remote document through form is remote")
        self.assertFalse(d.download_is_ajax_safe)

    def test_download_is_ajax_safe(self):
        """Remote document is mark as not safe."""
        d = create_single_doc("example_doc_name")
        self.assertTrue(d.download_is_ajax_safe)

    def test_create_document_url(self):
        """Tests creating an external document instead of a file."""

        superuser = get_user_model().objects.get(pk=2)
        c = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(
                doc_url="http://geonode.org/map.pdf",
                owner=superuser,
                title="GeoNode Map",
            ),
        )
        doc = Document.objects.get(pk=c.id)
        self.assertEqual(doc.title, "GeoNode Map")
        self.assertEqual(doc.extension, "pdf")

    def test_create_document_url_view(self):
        """
        Tests creating and updating external documents.
        """
        self.client.login(username="admin", password="admin")
        form_data = {
            "title": "GeoNode Map",
            "permissions": '{"users":{"AnonymousUser": ["view_resourcebase"]},"groups":{}}',
            "doc_url": "http://www.geonode.org/map.pdf",
        }

        response = self.client.post(reverse("document_upload"), data=form_data)
        self.assertEqual(response.status_code, 302)

        d = Document.objects.get(title="GeoNode Map")
        self.assertEqual(d.doc_url, "http://www.geonode.org/map.pdf")

    def test_uploaded_csv_with_uppercase_extension(self):
        """
        The extension of the file should always be lowercase
        """

        self.client.login(username="admin", password="admin")
        try:
            with open(os.path.join(os.path.dirname(__file__), "tests/data/test.CSV"), "rb") as f:
                data = {"title": "CSV with uppercase extension", "doc_file": f, "extension": "CSV"}
                self.client.post(reverse("document_upload"), data=data)
            d = Document.objects.get(title="CSV with uppercase extension")
            # verify that the extension is not lowercase
            self.assertEqual(d.extension, "csv")
            # be sure that also the file extension is not lowercase
            asset = get_default_asset(d)
            self.assertEqual(Path(asset.location[0]).suffix, ".csv")
        finally:
            Document.objects.filter(title="CSV with uppercase extension").delete()

    def test_upload_document_form(self):
        """
        Tests the Upload form.
        """
        form_data = dict()
        form = DocumentCreateForm(data=form_data)
        self.assertFalse(form.is_valid())

        # title is required
        self.assertTrue("title" in form.errors)

        # since neither a doc_file nor a doc_url are included __all__ should be
        # in form.errors.
        self.assertTrue("__all__" in form.errors)

        form_data = {
            "title": "GeoNode Map",
            "permissions": '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
            "doc_url": "http://www.geonode.org/map.pdf",
        }

        form = DocumentCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        self.assertTrue(isinstance(form.cleaned_data["permissions"], dict))

        # if permissions are not JSON serializable, the field should be in
        # form.errors.
        form_data["permissions"] = "non-json string"
        self.assertTrue("permissions" in DocumentCreateForm(data=form_data).errors)

        form_data = {
            "title": "GeoNode Map",
            "permissions": '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
        }

        file_data = {"doc_file": SimpleUploadedFile("test_img_file.gif", self.imgfile.read(), "image/gif")}
        form = DocumentCreateForm(form_data, file_data)
        self.assertTrue(form.is_valid())

        # The form should raise a validation error when a url and file is
        # present.
        form_data["doc_url"] = "http://www.geonode.org/map.pdf"
        form = DocumentCreateForm(form_data, file_data)
        self.assertFalse(form.is_valid())
        self.assertTrue("__all__" in form.errors)

    def test_non_image_documents_thumbnail(self):
        self.client.login(username="admin", password="admin")
        try:
            with open(os.path.join(f"{self.project_root}", "tests/data/text.txt"), "rb") as f:
                data = {"title": "Non img File Doc", "doc_file": f, "extension": "txt"}
                self.client.post(reverse("document_upload"), data=data)
            d = Document.objects.get(title="Non img File Doc")
            self.assertIsNone(d.thumbnail_url)
        finally:
            Document.objects.filter(title="Non img File Doc").delete()

    def test_documents_thumbnail(self):
        self.client.login(username="admin", password="admin")
        try:
            # test image doc
            with open(os.path.join(f"{self.project_root}", "tests/data/img.gif"), "rb") as f:
                data = {
                    "title": "img File Doc",
                    "doc_file": f,
                    "extension": "gif",
                }
                with self.settings(THUMBNAIL_SIZE={"width": 400, "height": 200}):
                    self.client.post(reverse("document_upload"), data=data)
                    d = Document.objects.get(title="img File Doc")
                    self.assertIsNotNone(d.thumbnail_url)
                    thumb_file = os.path.join(
                        settings.MEDIA_ROOT, f"thumbs/{os.path.basename(urlparse(d.thumbnail_url).path)}"
                    )
                    file = Image.open(thumb_file)
                    self.assertEqual(file.size, (400, 200))
                    # check thumbnail qualty and extention
                    self.assertEqual(file.format, "JPEG")
            data = {
                "title": "Remote img File Doc",
                "doc_url": "https://raw.githubusercontent.com/GeoNode/geonode/master/geonode/documents/tests/data/img.gif",
                "extension": "gif",
            }
            with self.settings(THUMBNAIL_SIZE={"width": 400, "height": 200}):
                self.client.post(reverse("document_upload"), data=data)
                d = Document.objects.get(title="Remote img File Doc")
                self.assertIsNotNone(d.thumbnail_url)
                thumb_file = os.path.join(
                    settings.MEDIA_ROOT, f"thumbs/{os.path.basename(urlparse(d.thumbnail_url).path)}"
                )
                file = Image.open(thumb_file)
                self.assertEqual(file.size, (400, 200))
                # check thumbnail qualty and extention
                self.assertEqual(file.format, "JPEG")
            # test pdf doc
            with open(os.path.join(f"{self.project_root}", "tests/data/pdf_doc.pdf"), "rb") as f:
                data = {
                    "title": "Pdf File Doc",
                    "doc_file": f,
                    "extension": "pdf",
                }
                self.client.post(reverse("document_upload"), data=data)
                d = Document.objects.get(title="Pdf File Doc")
                self.assertIsNotNone(d.thumbnail_url)
                thumb_file = os.path.join(
                    settings.MEDIA_ROOT, f"thumbs/{os.path.basename(urlparse(d.thumbnail_url).path)}"
                )
                file = Image.open(thumb_file)
                # check thumbnail qualty and extention
                self.assertEqual(file.format, "JPEG")
        finally:
            Document.objects.filter(title="img File Doc").delete()
            Document.objects.filter(title="Pdf File Doc").delete()

    def test_upload_document_form_size_limit(self):
        form_data = {
            "title": "GeoNode Map",
            "permissions": '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
        }
        test_file = SimpleUploadedFile("test_img_file.gif", self.imgfile.read(), "image/gif")
        test_file.size = settings.DEFAULT_MAX_UPLOAD_SIZE * 5  # Set as a large file

        file_data = {"doc_file": test_file}

        with self.assertRaises(FileUploadLimitException):
            form = DocumentCreateForm(form_data, file_data)

            self.assertFalse(form.is_valid())
            expected_error = (
                f"File size size exceeds {filesizeformat(settings.DEFAULT_MAX_UPLOAD_SIZE)}. "
                f"Please try again with a smaller file."
            )
            self.assertEqual(form.errors, {"doc_file": [expected_error]})

    def test_document_embed(self):
        """/documents/1 -> Test accessing the embed view of a document"""
        d = Document.objects.all().first()
        d.set_default_permissions()

        response = self.client.get(reverse("document_embed", args=(str(d.id),)))
        self.assertEqual(response.status_code, 200)

    def test_access_document_upload_form(self):
        """Test the form page is returned correctly via GET request /documents/upload"""

        log = self.client.login(username="bobby", password="bob")
        self.assertTrue(log)
        response = self.client.get(reverse("document_upload"))
        self.assertEqual(response.status_code, 405)

    def test_document_isuploaded(self):
        """/documents/upload -> Test uploading a document"""

        f = SimpleUploadedFile("test_img_file.gif", self.imgfile.read(), "image/gif")
        m = Map.objects.first()

        self.client.login(username="admin", password="admin")
        response = self.client.post(
            f"{reverse('document_upload')}?no__redirect=true",
            data={
                "doc_file": f,
                "title": "uploaded_document",
                "q": m.id,
                "type": "document",
                "permissions": '{"users":{"AnonymousUser": ["view_resourcebase"]}}',
            },
        )
        self.assertEqual(response.status_code, 200)

    # Permissions Tests

    def test_set_document_permissions(self):
        """Verify that the set_document_permissions view is behaving as expected"""
        # Get a document to work with
        document = Document.objects.first()

        # Set the Permissions
        document.set_permissions(self.perm_spec)

        # Test that the Permissions for anonympus user are set correctly
        self.assertFalse(self.anonymous_user.has_perm("view_resourcebase", document.get_self_resource()))

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the document owner) were
        current_perms = permissions_registry.get_perms(instance=document)
        self.assertEqual(len(current_perms["users"]), 1)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec["users"].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, document.get_self_resource()))

    @patch("geonode.documents.tasks.create_document_thumbnail")
    def test_ajax_document_permissions(self, create_thumb):
        """Verify that the ajax_document_permissions view is behaving as expected"""
        create_thumb.return_value = True
        # Setup some document names to work with
        superuser = get_user_model().objects.get(pk=2)
        document = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(files=[TEST_GIF], owner=superuser, title="theimg", is_approved=True),
        )
        document_id = document.id
        invalid_document_id = 20

        # Test that an invalid document is handled for properly
        response = self.client.post(
            reverse("resource_permissions", args=(invalid_document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Test that GET returns permissions
        response = self.client.get(reverse("resource_permissions", args=(document_id,)))
        assert "permissions" in ensure_string(response.content)

        # Test that a user is required to have
        # documents.change_dataset_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse("resource_permissions", args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username="bobby", password="bob")
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse("resource_permissions", args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username="admin", password="admin")
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse("resource_permissions", args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json",
        )

        # Test that the method returns 200
        self.assertEqual(response.status_code, 200)


class DocumentModerationTestCase(GeoNodeBaseTestSupport):

    @classmethod
    def setUpClass(cls):
        """Runs once for the entire test class."""
        super().setUpClass()
        create_models(type=b"document")
        create_models(type=b"map")
        cls.project_root = os.path.abspath(os.path.dirname(__file__))
        cls.document_upload_url = f"{(reverse('document_upload'))}?no__redirect=true"

        cls.user = "admin"
        cls.passwd = "admin"
        cls.u = get_user_model().objects.get(username=cls.user)
        cls.u.email = "test@email.com"
        cls.u.is_active = True
        cls.u.save()

    def setUp(self):
        """Runs before every test method (Now only runs what's essential)."""
        super().setUp()
        self.u = self.__class__.u  # Assign the pre-configured user instance
        self.project_root = self.__class__.project_root
        self.document_upload_url = self.__class__.document_upload_url

    def _get_input_path(self):
        base_path = gisdata.GOOD_DATA
        return os.path.join(base_path, "vector", "readme.txt")

    def test_document_upload_redirect(self):
        with self.settings(ADMIN_MODERATE_UPLOADS=False):
            self.client.login(username=self.user, password=self.passwd)
            dname = "document title"
            with open(os.path.join(f"{self.project_root}", "tests/data/img.gif"), "rb") as f:
                data = {
                    "title": dname,
                    "doc_file": f,
                    "resource": "",
                    "extension": "gif",
                    "permissions": "{}",
                }
                resp = self.client.post(self.document_upload_url, data=data)
                self.assertEqual(resp.status_code, 200, resp.content)
                content = json.loads(resp.content.decode("utf-8"))
                self.assertTrue(content["success"])
                self.assertIn("url", content)


class DocumentsNotificationsTestCase(NotificationsTestsHelper):
    # Static data can be defined once as class attributes
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWD = "admin"
    NORMAL_USERNAME = "norman"

    @classmethod
    def setUpClass(cls):
        """
        Runs once for the entire test class.
        Database operations and static object initialization go here.
        """
        super().setUpClass()
        create_models(type=b"document")
        cls.admin_user = get_user_model().objects.get(username=cls.ADMIN_USERNAME)
        cls.admin_user.email = "test@email.com"
        cls.admin_user.is_active = True
        cls.admin_user.is_superuser = True
        cls.admin_user.save()
        cls.norman_user = get_user_model().objects.get(username=cls.NORMAL_USERNAME)
        cls.norman_user.email = "norman@email.com"
        cls.norman_user.is_active = True
        cls.norman_user.save()

        cls.anonymous_user = get_anonymous_user()

        NotificationsTestsHelper().setup_notifications_for(DocumentsAppConfig.NOTIFICATIONS, cls.admin_user)
        NotificationsTestsHelper().setup_notifications_for(DocumentsAppConfig.NOTIFICATIONS, cls.norman_user)

    def setUp(self):
        """
        Runs before every test method.
        Only quick attribute assignments go here.
        """
        # Call super().setUp() if necessary for the test runner
        super().setUp()

        # Assign the pre-configured attributes to the test instance
        self.user = self.__class__.ADMIN_USERNAME
        self.passwd = self.__class__.ADMIN_PASSWD
        self.u = self.__class__.admin_user
        self.norman = self.__class__.norman_user
        self.anonymous_user = self.__class__.anonymous_user

    def testDocumentsNotifications(self):
        with self.settings(
            EMAIL_ENABLE=True,
            NOTIFICATION_ENABLED=True,
            NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
            PINAX_NOTIFICATIONS_QUEUE_ALL=False,
        ):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)
            _d = Document.objects.create(title="test notifications", owner=self.norman)
            self.assertTrue(self.check_notification_out("document_created", self.u))
            # Ensure "resource.owner" won't be notified for having created its own document
            self.assertFalse(self.check_notification_out("document_created", self.norman))

            self.clear_notifications_queue()
            _d.title = "test notifications 2"
            _d.save(notify=True)
            self.assertTrue(self.check_notification_out("document_updated", self.u))

            self.clear_notifications_queue()


class DocumentViewTestCase(GeoNodeBaseTestSupport):

    # Fixtures are correctly placed here, running once before setUpClass
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    # Define static data as class attributes
    NOT_ADMIN_USERNAME = "r-lukaku"

    @classmethod
    def setUpClass(cls):
        """
        Runs once for the entire test class. Database writes and static data setup go here.
        """
        super().setUpClass()

        cls.not_admin = get_user_model().objects.create(username=cls.NOT_ADMIN_USERNAME, is_active=True)
        cls.not_admin.set_password("very-secret")
        cls.not_admin.save()  # Two database writes (create + save password) run only once!

        cls.test_doc = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(files=[TEST_GIF], owner=cls.not_admin, title="test", is_approved=True),
        )

        cls.perm_spec = {"users": {"AnonymousUser": []}}

        cls.doc_link_url = reverse("document_link", args=(cls.test_doc.pk,))

    def setUp(self):
        """
        Runs before every test method. Only quick attribute assignments go here.
        """
        super().setUp()

        # Assign pre-configured attributes to the test instance
        self.not_admin = self.__class__.not_admin
        self.test_doc = self.__class__.test_doc
        self.perm_spec = self.__class__.perm_spec
        self.doc_link_url = self.__class__.doc_link_url

    def test_document_link_with_permissions(self):
        self.test_doc.set_permissions(self.perm_spec)
        # Get link as Anonymous user
        response = self.client.get(self.doc_link_url)
        self.assertEqual(response.status_code, 401)
        # Access resource with user logged-in
        self.client.login(username=self.not_admin.username, password="very-secret")
        response = self.client.get(self.doc_link_url)
        self.assertEqual(response.status_code, 200)
        # test document link with external url
        doc = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(
                doc_url="http://geonode.org/map.pdf",
                owner=self.not_admin,
                title="GeoNode Map Doc",
            ),
        )
        self.assertEqual(doc.href, "http://geonode.org/map.pdf")

        # create original link to external
        doc.link_set.create(resource=doc.resourcebase_ptr, link_type="original", url="http://google.com/test")
        self.assertEqual(doc.download_url, "http://google.com/test")
