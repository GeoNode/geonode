# -*- coding: utf-8 -*-
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
from geonode.tests.base import GeoNodeBaseTestSupport

import os
import StringIO
import json

import gisdata
from datetime import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from geonode.base.models import License, Region

from guardian.shortcuts import get_anonymous_user

from .forms import DocumentCreateForm

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.documents.models import Document, DocumentResourceLink
from geonode.documents.forms import DocumentFormMixin
from geonode.base.populate_test_data import create_models
from geonode.tests.utils import NotificationsTestsHelper
from geonode.documents import DocumentsAppConfig


class DocumentsTest(GeoNodeBaseTestSupport):

    type = 'document'
    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    def setUp(self):
        super(DocumentsTest, self).setUp()
        create_models('map')
        self.imgfile = StringIO.StringIO(
            'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
            '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
        self.anonymous_user = get_anonymous_user()

    def test_create_document_with_no_rel(self):
        """Tests the creation of a document with no relations"""

        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')

        superuser = get_user_model().objects.get(pk=2)
        c = Document.objects.create(
            doc_file=f,
            owner=superuser,
            title='theimg')
        c.set_default_permissions()
        self.assertEquals(Document.objects.get(pk=c.id).title, 'theimg')

    def test_create_document_with_rel(self):
        """Tests the creation of a document with no a map related"""
        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')

        superuser = get_user_model().objects.get(pk=2)

        c = Document.objects.create(
            doc_file=f,
            owner=superuser,
            title='theimg')

        m = Map.objects.all()[0]
        ctype = ContentType.objects.get_for_model(m)
        _l = DocumentResourceLink.objects.create(
            document_id=c.id,
            content_type=ctype,
            object_id=m.id)

        self.assertEquals(Document.objects.get(pk=c.id).title, 'theimg')
        self.assertEquals(DocumentResourceLink.objects.get(pk=_l.id).object_id,
                          m.id)

    def test_create_document_url(self):
        """Tests creating an external document instead of a file."""

        superuser = get_user_model().objects.get(pk=2)
        c = Document.objects.create(doc_url="http://geonode.org/map.pdf",
                                    owner=superuser,
                                    title="GeoNode Map",
                                    )
        doc = Document.objects.get(pk=c.id)
        self.assertEquals(doc.title, "GeoNode Map")
        self.assertEquals(doc.extension, "pdf")

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

        form_data['doc_url'] = 'http://www.geonode.org/mapz.pdf'
        response = self.client.post(
            reverse(
                'document_replace',
                args=[
                    d.id]),
            data=form_data)
        self.assertEqual(response.status_code, 302)

        d = Document.objects.get(title='GeoNode Map')
        self.assertEqual(d.doc_url, 'http://www.geonode.org/mapz.pdf')

    def test_upload_document_form(self):
        """
        Tests the Upload form.
        """
        form_data = dict()
        form = DocumentCreateForm(data=form_data)
        self.assertFalse(form.is_valid())

        # title is required
        self.assertTrue('title' in form.errors)

        # permissions are required
        self.assertTrue('permissions' in form.errors)

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

    def test_document_details(self):
        """/documents/1 -> Test accessing the detail view of a document"""
        d = Document.objects.all().first()
        d.set_default_permissions()

        response = self.client.get(reverse('document_detail', args=(str(d.id),)))
        self.assertEquals(response.status_code, 200)

    def test_document_metadata_details(self):
        d = Document.objects.all().first()
        d.set_default_permissions()

        response = self.client.get(reverse('document_metadata_detail', args=(str(d.id),)))
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, "Approved", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Published", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Featured", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "<dt>Group</dt>", count=0, status_code=200, msg_prefix='', html=False)

        # ... now assigning a Group to the document
        group = Group.objects.first()
        d.group = group
        d.save()
        response = self.client.get(reverse('document_metadata_detail', args=(str(d.id),)))
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        d.group = None
        d.save()

    def test_access_document_upload_form(self):
        """Test the form page is returned correctly via GET request /documents/upload"""

        log = self.client.login(username='bobby', password='bob')
        self.assertTrue(log)
        response = self.client.get(reverse('document_upload'))
        self.assertTrue('Upload Documents' in response.content)

    def test_document_isuploaded(self):
        """/documents/upload -> Test uploading a document"""

        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')
        m = Map.objects.all()[0]

        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse('document_upload'),
            data={
                'file': f,
                'title': 'uploaded_document',
                'q': m.id,
                'type': 'map',
                'permissions': '{"users":{"AnonymousUser": ["view_resourcebase"]}}'},
            follow=True)
        self.assertEquals(response.status_code, 200)

    # Permissions Tests

    def test_set_document_permissions(self):
        """Verify that the set_document_permissions view is behaving as expected
        """
        # Get a document to work with
        document = Document.objects.all()[0]

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
        self.assertEqual(len(current_perms['users'].keys()), 2)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec['users'].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, document.get_self_resource()))

    def test_ajax_document_permissions(self):
        """Verify that the ajax_document_permissions view is behaving as expected
        """

        # Setup some document names to work with
        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.imgfile.read(),
            'image/gif')

        superuser = get_user_model().objects.get(pk=2)
        document = Document.objects.create(
            doc_file=f,
            owner=superuser,
            title='theimg')
        document.set_default_permissions()
        document_id = document.id
        invalid_document_id = 20

        # Test that an invalid document is handled for properly
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    invalid_document_id,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(reverse('resource_permissions', args=(document_id,)))
        assert('permissions' in response.content)

        # Test that a user is required to have
        # documents.change_layer_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse('resource_permissions', args=(document_id,)),
            data=json.dumps(self.perm_spec),
            content_type="application/json")

        # Test that the method returns 200
        self.assertEquals(response.status_code, 200)

    def test_batch_edit(self):
        Model = Document
        view = 'document_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join([str(element.pk) for element in resources])
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view, args=(ids,)))
        self.assertEquals(response.status_code, 401)
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'group': group.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'owner': owner.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'license': license.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'region': region.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            if resource.regions.all():
                self.assertTrue(region in resource.regions.all())
        # test date change
        from django.utils import timezone
        date = datetime.now(timezone.get_current_timezone())
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'date': date},
        )
        self.assertEquals(response.status_code, 200)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            today = date.today()
            todoc = resource.date.today()
            self.assertEquals((today.day, today.month, today.year),
                              (todoc.day, todoc.month, todoc.year))
        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'language': language},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'keywords': keywords},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))


class DocumentModerationTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(DocumentModerationTestCase, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='document')
        create_models(type='map')
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()

    def _get_input_path(self):
        base_path = gisdata.GOOD_DATA
        return os.path.join(base_path, 'vector', 'readme.txt')

    def test_moderated_upload(self):
        """
        Test if moderation flag works
        """
        with self.settings(ADMIN_MODERATE_UPLOADS=False):
            document_upload_url = reverse('document_upload')
            self.client.login(username=self.user, password=self.passwd)

            input_path = self._get_input_path()

            with open(input_path, 'rb') as f:
                data = {'title': 'document title',
                        'doc_file': f,
                        'doc_url': '',
                        'resource': '',
                        'permissions': '{}',
                        }
                resp = self.client.post(document_upload_url, data=data)
            self.assertEqual(resp.status_code, 302)
            dname = 'document title'
            _l = Document.objects.get(title=dname)

            self.assertTrue(_l.is_published)
            _l.delete()

        with self.settings(ADMIN_MODERATE_UPLOADS=True):
            document_upload_url = reverse('document_upload')
            self.client.login(username=self.user, password=self.passwd)

            input_path = self._get_input_path()

            with open(input_path, 'rb') as f:
                data = {'title': 'document title',
                        'doc_file': f,
                        'doc_url': '',
                        'resource': '',
                        'permissions': '{}',
                        }
                resp = self.client.post(document_upload_url, data=data)
            self.assertEqual(resp.status_code, 302)
            dname = 'document title'
            _l = Document.objects.get(title=dname)

            self.assertFalse(_l.is_published)


class DocumentNotificationsTestCase(NotificationsTestsHelper):

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='document')
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(DocumentsAppConfig.NOTIFICATIONS, self.u)

    def testDocumentNotifications(self):
        with self.settings(PINAX_NOTIFICATIONS_QUEUE_ALL=True):
            self.clear_notifications_queue()
            _l = Document.objects.create(title='test notifications', owner=self.u)
            self.assertTrue(self.check_notification_out('document_created', self.u))
            _l.title = 'test notifications 2'
            _l.save()
            self.assertTrue(self.check_notification_out('document_updated', self.u))

            from dialogos.models import Comment
            lct = ContentType.objects.get_for_model(_l)
            comment = Comment(author=self.u, name=self.u.username,
                              content_type=lct, object_id=_l.id,
                              content_object=_l, comment='test comment')
            comment.save()

            self.assertTrue(self.check_notification_out('document_comment', self.u))


class DocumentResourceLinkTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        create_models('document')
        create_models('map')
        create_models('layer')

        self.test_file = StringIO.StringIO(
            'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
            '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )

    def test_create_document_with_links(self):
        """Tests the creation of document links."""
        f = SimpleUploadedFile(
            'test_img_file.gif',
            self.test_file.read(),
            'image/gif')

        superuser = get_user_model().objects.get(pk=2)

        d = Document.objects.create(
            doc_file=f,
            owner=superuser,
            title='theimg')

        self.assertEquals(Document.objects.get(pk=d.id).title, 'theimg')

        maps = list(Map.objects.all())
        layers = list(Layer.objects.all())
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
            _l = DocumentResourceLink.objects.get(
                document_id=d.id,
                content_type=ct.id,
                object_id=resource.id
            )
            self.assertEquals(_l.object_id, resource.id)

        # update document links

        mixin2 = DocumentFormMixin()
        mixin2.instance = d
        mixin2.cleaned_data = dict(
            links=mixin2.generate_link_values(resources=layers),
        )
        mixin2.save_many2many()

        for resource in layers:
            ct = ContentType.objects.get_for_model(resource)
            _l = DocumentResourceLink.objects.get(
                document_id=d.id,
                content_type=ct.id,
                object_id=resource.id
            )
            self.assertEquals(_l.object_id, resource.id)

        for resource in maps:
            ct = ContentType.objects.get_for_model(resource)
            with self.assertRaises(DocumentResourceLink.DoesNotExist):
                DocumentResourceLink.objects.get(
                    document_id=d.id,
                    content_type=ct.id,
                    object_id=resource.id
                )
