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
from io import BytesIO

from unittest.mock import patch

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat

from guardian.shortcuts import get_anonymous_user

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.compat import ensure_string
from geonode.base.models import License, Region
from geonode.documents import DocumentsAppConfig
from geonode.resource.manager import resource_manager
from geonode.documents.forms import DocumentFormMixin
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.tests.utils import NotificationsTestsHelper
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP
from geonode.documents.models import Document, DocumentResourceLink

from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models)
from geonode.upload.api.exceptions import FileUploadLimitException

from .forms import DocumentCreateForm


class DocumentsTest(GeoNodeBaseTestSupport):

    type = 'document'

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        create_models('map')
        self.imgfile = io.BytesIO(
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
            b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
        self.anonymous_user = get_anonymous_user()

    def test_document_mimetypes_rendering(self):
        ARCHIVETYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'archive']
        AUDIOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'audio']
        IMGTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'image']
        VIDEOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'video']
        self.assertIsNotNone(ARCHIVETYPES)
        self.assertIsNotNone(AUDIOTYPES)
        self.assertIsNotNone(IMGTYPES)
        self.assertIsNotNone(VIDEOTYPES)

        # Make sure we won't have template rendering issues
        self.assertTrue('dwg' in ARCHIVETYPES)
        self.assertTrue('dxf' in ARCHIVETYPES)
        self.assertTrue('tif' in ARCHIVETYPES)
        self.assertTrue('tiff' in ARCHIVETYPES)
        self.assertTrue('pbm' in ARCHIVETYPES)

    @patch("geonode.documents.tasks.create_document_thumbnail")
    def test_create_document_with_no_rel(self, thumb):
        """Tests the creation of a document with no relations"""
        thumb.return_value = True
        f = [f"{settings.MEDIA_ROOT}/img.gif"]

        superuser = get_user_model().objects.get(pk=2)
        c = Document.objects.create(
            files=f,
            owner=superuser,
            title='theimg')
        c.set_default_permissions()
        self.assertEqual(Document.objects.get(pk=c.id).title, 'theimg')

    @patch("geonode.documents.tasks.create_document_thumbnail")
    def test_create_document_with_rel(self, thumb):
        """Tests the creation of a document with no a map related"""
        thumb.return_value = True
        f = [f"{settings.MEDIA_ROOT}/img.gif"]

        superuser = get_user_model().objects.get(pk=2)

        c = Document.objects.create(
            files=f,
            owner=superuser,
            title='theimg')

        m = Map.objects.first()
        ctype = ContentType.objects.get_for_model(m)
        _d = DocumentResourceLink.objects.create(
            document_id=c.id,
            content_type=ctype,
            object_id=m.id)

        self.assertEqual(Document.objects.get(pk=c.id).title, 'theimg')
        self.assertEqual(DocumentResourceLink.objects.get(pk=_d.id).object_id, m.id)

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
            ))
        doc = Document.objects.get(pk=c.id)
        self.assertEqual(doc.title, "GeoNode Map")
        self.assertEqual(doc.extension, "pdf")

    def test_create_document_url_view(self):
        """
        Tests creating and updating external documents.
        """
        self.client.login(username='admin', password='admin')
        form_data = {
            'title': 'GeoNode Map',
            'permissions': '{"users":{"AnonymousUser": ["view_resourcebase"]},"groups":{}}',
            'doc_url': 'http://www.geonode.org/map.pdf'}

        response = self.client.post(reverse('document_upload'), data=form_data)
        self.assertEqual(response.status_code, 302)

        d = Document.objects.get(title='GeoNode Map')
        self.assertEqual(d.doc_url, 'http://www.geonode.org/map.pdf')

    def test_upload_document_form(self):
        """
        Tests the Upload form.
        """
        form_data = dict()
        form = DocumentCreateForm(data=form_data)
        self.assertFalse(form.is_valid())

        # title is required
        self.assertTrue('title' in form.errors)

        # since neither a doc_file nor a doc_url are included __all__ should be
        # in form.errors.
        self.assertTrue('__all__' in form.errors)

        form_data = {
            'title': 'GeoNode Map',
            'permissions': '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
            'doc_url': 'http://www.geonode.org/map.pdf'}

        form = DocumentCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        self.assertTrue(isinstance(form.cleaned_data['permissions'], dict))

        # if permissions are not JSON serializable, the field should be in
        # form.errors.
        form_data['permissions'] = 'non-json string'
        self.assertTrue(
            'permissions' in DocumentCreateForm(
                data=form_data).errors)

        form_data = {
            'title': 'GeoNode Map',
            'permissions': '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
        }

        file_data = {
            'doc_file': SimpleUploadedFile(
                'test_img_file.gif',
                self.imgfile.read(),
                'image/gif')}
        form = DocumentCreateForm(form_data, file_data)
        self.assertTrue(form.is_valid())

        # The form should raise a validation error when a url and file is
        # present.
        form_data['doc_url'] = 'http://www.geonode.org/map.pdf'
        form = DocumentCreateForm(form_data, file_data)
        self.assertFalse(form.is_valid())
        self.assertTrue('__all__' in form.errors)

    def test_replace_document(self):
        self.client.login(username='admin', password='admin')

        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')
        response = self.client.post(
            reverse('document_upload'),
            data={
                'title': 'File Doc',
                'doc_file': f,
                'permissions': '{"users":{"AnonymousUser": ["view_resourcebase"]}}'},
            follow=True)
        self.assertEqual(response.status_code, 200)

        # Replace Document
        d = Document.objects.get(title='File Doc')
        test_image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
        f = SimpleUploadedFile('test_image.png', BytesIO(test_image.tobytes()).read(), 'image/png')
        response = self.client.post(
            reverse('document_replace', args=(d.id,)),
            data={'doc_file': f}
        )
        self.assertEqual(response.status_code, 302)
        # Remove document
        d.delete()

    def test_upload_document_form_size_limit(self):
        form_data = {
            'title': 'GeoNode Map',
            'permissions': '{"anonymous":"document_readonly","authenticated":"resourcebase_readwrite","users":[]}',
        }
        test_file = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif'
        )
        test_file.size = settings.DEFAULT_MAX_UPLOAD_SIZE * 5  # Set as a large file

        file_data = {'doc_file': test_file}

        with self.assertRaises(FileUploadLimitException):
            form = DocumentCreateForm(form_data, file_data)

            self.assertFalse(form.is_valid())
            expected_error = (
                f"File size size exceeds {filesizeformat(settings.DEFAULT_MAX_UPLOAD_SIZE)}. "
                f"Please try again with a smaller file."
            )
            self.assertEqual(form.errors, {'doc_file': [expected_error]})

    def test_document_embed(self):
        """/documents/1 -> Test accessing the embed view of a document"""
        d = Document.objects.all().first()
        d.set_default_permissions()

        response = self.client.get(reverse('document_embed', args=(str(d.id),)))
        self.assertEqual(response.status_code, 200)

    def test_access_document_upload_form(self):
        """Test the form page is returned correctly via GET request /documents/upload"""

        log = self.client.login(username='bobby', password='bob')
        self.assertTrue(log)
        response = self.client.get(reverse('document_upload'))
        self.assertEqual(response.status_code, 405)

    def test_document_isuploaded(self):
        """/documents/upload -> Test uploading a document"""

        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')
        m = Map.objects.first()

        self.client.login(username='admin', password='admin')
        response = self.client.post(
            f"{reverse('document_upload')}?no__redirect=true",
            data={
                'doc_file': f,
                'title': 'uploaded_document',
                'q': m.id,
                'type': 'document',
                'permissions': '{"users":{"AnonymousUser": ["view_resourcebase"]}}'},
        )
        self.assertEqual(response.status_code, 200)

    # Permissions Tests

    def test_set_document_permissions(self):
        """Verify that the set_document_permissions view is behaving as expected
        """
        # Get a document to work with
        document = Document.objects.first()

        # Set the Permissions
        document.set_permissions(self.perm_spec)

        # Test that the Permissions for anonympus user are set correctly
        self.assertFalse(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                document.get_self_resource()))

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the document owner) were removed
        current_perms = document.get_all_level_info()
        self.assertEqual(len(current_perms['users']), 1)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec['users'].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, document.get_self_resource()))

    @patch("geonode.documents.tasks.create_document_thumbnail")
    def test_ajax_document_permissions(self, create_thumb):
        """Verify that the ajax_document_permissions view is behaving as expected
        """
        create_thumb.return_value = True
        # Setup some document names to work with
        f = [f"{settings.MEDIA_ROOT}/img.gif"]

        superuser = get_user_model().objects.get(pk=2)
        document = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(
                files=f,
                owner=superuser,
                title='theimg',
                is_approved=True))
        document_id = document.id
        invalid_document_id = 20

        # Test that an invalid document is handled for properly
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    invalid_document_id,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Test that GET returns permissions
        response = self.client.get(reverse('resource_permissions', args=(document_id,)))
        assert ('permissions' in ensure_string(response.content))

        # Test that a user is required to have
        # documents.change_dataset_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")

        # Test that the method returns 200
        self.assertEqual(response.status_code, 200)

    def test_batch_edit(self):
        Model = Document
        view = 'document_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join(str(element.pk) for element in resources)
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view))
        self.assertTrue(response.status_code in (401, 403))
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view),
            data={'group': group.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view),
            data={'owner': owner.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view),
            data={'license': license.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view),
            data={'region': region.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            if resource.regions.all():
                self.assertTrue(region in resource.regions.all())
        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view),
            data={'language': language, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view),
            data={'keywords': keywords, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))


class DocumentModerationTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type=b'document')
        create_models(type=b'map')
        self.project_root = os.path.abspath(os.path.dirname(__file__))
        self.document_upload_url = f"{(reverse('document_upload'))}?no__redirect=true"
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()

    def _get_input_path(self):
        base_path = gisdata.GOOD_DATA
        return os.path.join(base_path, 'vector', 'readme.txt')

    def test_document_upload_redirect(self):
        with self.settings(ADMIN_MODERATE_UPLOADS=False):
            self.client.login(username=self.user, password=self.passwd)
            dname = 'document title'
            with open(os.path.join(f"{self.project_root}", "tests/data/img.gif"), "rb") as f:
                data = {
                    'title': dname,
                    'doc_file': f,
                    'resource': '',
                    'extension': 'gif',
                    'permissions': '{}',
                }
                resp = self.client.post(self.document_upload_url, data=data)
                self.assertEqual(resp.status_code, 200, resp.content)
                content = json.loads(resp.content.decode('utf-8'))
                self.assertTrue(content["success"])
                self.assertIn("url", content)


class DocumentsNotificationsTestCase(NotificationsTestsHelper):

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type=b'document')
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.is_superuser = True
        self.u.save()
        self.setup_notifications_for(DocumentsAppConfig.NOTIFICATIONS, self.u)
        self.norman = get_user_model().objects.get(username='norman')
        self.norman.email = 'norman@email.com'
        self.norman.is_active = True
        self.norman.save()
        self.setup_notifications_for(DocumentsAppConfig.NOTIFICATIONS, self.norman)

    def testDocumentsNotifications(self):
        with self.settings(
                EMAIL_ENABLE=True,
                NOTIFICATION_ENABLED=True,
                NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
                PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)
            _d = Document.objects.create(
                title='test notifications',
                owner=self.norman)
            self.assertTrue(self.check_notification_out('document_created', self.u))
            # Ensure "resource.owner" won't be notified for having created its own document
            self.assertFalse(self.check_notification_out('document_created', self.norman))

            self.clear_notifications_queue()
            _d.title = 'test notifications 2'
            _d.save(notify=True)
            self.assertTrue(self.check_notification_out('document_updated', self.u))

            self.clear_notifications_queue()
            lct = ContentType.objects.get_for_model(_d)

            if "pinax.ratings" in settings.INSTALLED_APPS:
                self.clear_notifications_queue()
                from pinax.ratings.models import Rating
                rating = Rating(user=self.norman,
                                content_type=lct,
                                object_id=_d.id,
                                content_object=_d,
                                rating=5)
                rating.save()
                self.assertTrue(self.check_notification_out('document_rated', self.u))


class DocumentResourceLinkTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')

        self.test_file = io.BytesIO(
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
            b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )

    def test_create_document_with_links(self):
        """Tests the creation of document links."""
        f = [f"{settings.MEDIA_ROOT}/img.gif"]
        superuser = get_user_model().objects.get(pk=2)

        d = Document.objects.create(
            files=f,
            owner=superuser,
            title='theimg'
        )

        self.assertEqual(Document.objects.get(pk=d.id).title, 'theimg')

        maps = list(Map.objects.all())
        layers = list(Dataset.objects.all())
        resources = maps + layers

        # create document links

        mixin1 = DocumentFormMixin()
        mixin1.instance = d
        mixin1.cleaned_data = dict(
            links=mixin1.generate_link_values(resources=resources),
        )
        mixin1.save_many2many()

        for resource in resources:
            ct = ContentType.objects.get_for_model(resource)
            _d = DocumentResourceLink.objects.get(
                document_id=d.id,
                content_type=ct.id,
                object_id=resource.id
            )
            self.assertEqual(_d.object_id, resource.id)

        # update document links

        mixin2 = DocumentFormMixin()
        mixin2.instance = d
        mixin2.cleaned_data = dict(
            links=mixin2.generate_link_values(resources=layers),
        )
        mixin2.save_many2many()

        for resource in layers:
            ct = ContentType.objects.get_for_model(resource)
            _d = DocumentResourceLink.objects.get(
                document_id=d.id,
                content_type=ct.id,
                object_id=resource.id
            )
            self.assertEqual(_d.object_id, resource.id)

        for resource in maps:
            ct = ContentType.objects.get_for_model(resource)
            with self.assertRaises(DocumentResourceLink.DoesNotExist):
                DocumentResourceLink.objects.get(
                    document_id=d.id,
                    content_type=ct.id,
                    object_id=resource.id
                )


class DocumentViewTestCase(GeoNodeBaseTestSupport):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        self.not_admin = get_user_model().objects.create(username='r-lukaku', is_active=True)
        self.not_admin.set_password('very-secret')
        self.not_admin.save()
        self.files = [f"{settings.MEDIA_ROOT}/img.gif"]
        self.test_doc = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(
                files=self.files,
                owner=self.not_admin,
                title='test',
                is_approved=True))
        self.perm_spec = {"users": {"AnonymousUser": []}}
        self.doc_link_url = reverse('document_link', args=(self.test_doc.pk,))

    def test_that_keyword_multiselect_is_disabled_for_non_admin_users(self):
        """
        Test that keyword multiselect widget is disabled when the user is not an admin
        when FREETEXT_KEYWORDS_READONLY=True
        """
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form']['keywords'].field.disabled)

    def test_that_featured_enabling_and_disabling_for_users(self):
        # Non Admins
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        response = self.client.get(url)
        self.assertFalse(self.not_admin.is_superuser)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form']['featured'].field.disabled)
        # Admin
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form']['featured'].field.disabled)

    def test_that_keyword_multiselect_is_not_disabled_for_admin_users(self):
        """
        Test that only admin users can create/edit keywords
        """
        admin = self.not_admin
        admin.is_superuser = True
        admin.save()
        self.client.login(username=admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        response = self.client.get(url)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_non_admin_user_can_create_write_to_map_without_keyword(self):
        """
        Test that non admin users can write to maps without creating/editing keywords
        when FREETEXT_KEYWORDS_READONLY=True
        """
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.post(url, data={
                "resource-owner": self.not_admin.id,
                "resource-title": "doc",
                "resource-date": "2022-01-24 16:38 pm",
                "resource-date_type": "creation",
                "resource-language": "eng",
            })
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
        self.test_doc.refresh_from_db()
        self.assertEqual('doc', self.test_doc.title)

    def test_that_non_admin_user_cannot_create_edit_keyword(self):
        """
        Test that non admin users cannot edit/create keywords when FREETEXT_KEYWORDS_READONLY=True
        """
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.post(url, data={'resource-keywords': 'wonderful-keyword'})
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.content, b'Unauthorized: Cannot edit/create Free-text Keywords')

    def test_that_keyword_multiselect_is_enabled_for_non_admin_users_when_freetext_keywords_readonly_istrue(self):
        """
        Test that keyword multiselect widget is not disabled when the user is not an admin
        and FREETEXT_KEYWORDS_READONLY=False
        """
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.get(url)
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_non_admin_user_can_create_edit_keyword_when_freetext_keywords_readonly_istrue(self):
        """
        Test that non admin users can edit/create keywords when FREETEXT_KEYWORDS_READONLY=False
        """
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('document_metadata', args=(self.test_doc.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.post(url, data={
                "resource-owner": self.not_admin.id,
                "resource-title": "doc",
                "resource-date": "2022-01-24 16:38 pm",
                "resource-date_type": "creation",
                "resource-language": "eng",
                'resource-keywords': 'wonderful-keyword'
            })
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
        self.test_doc.refresh_from_db()
        self.assertEqual("doc", self.test_doc.title)

    def test_document_link_with_permissions(self):
        self.test_doc.set_permissions(self.perm_spec)
        # Get link as Anonymous user
        response = self.client.get(self.doc_link_url)
        self.assertEqual(response.status_code, 401)
        # Access resource with user logged-in
        self.client.login(username=self.not_admin.username, password='very-secret')
        response = self.client.get(self.doc_link_url)
        self.assertEqual(response.status_code, 404)
        # test document link with external url
        doc = resource_manager.create(
            None,
            resource_type=Document,
            defaults=dict(
                doc_url="http://geonode.org/map.pdf",
                owner=self.not_admin,
                title="GeoNode Map Doc",
            ))
        self.assertEqual(doc.href, 'http://geonode.org/map.pdf')
