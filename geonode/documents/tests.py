"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

"""
import StringIO
import json

from django.test import TestCase
from django.conf import settings
from django.test.client import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS
import geonode.documents.views
import geonode.security

imgfile = StringIO.StringIO('GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
                                '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

class EventsTest(TestCase):
    fixtures = ['map_data.json', 'intial_data.json']
    
    def test_create_document_with_no_rel(self):
        """Tests the createion of a document with no relations"""
        f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
    
        superuser = User.objects.get(pk=2)
        c, created = Document.objects.get_or_create(id=1, doc_file=f,owner=superuser, title='theimg')
        c.set_default_permissions()

        self.assertEquals(created, True)

    def test_create_document_with_rel(self):
        """Tests the createion of a document with no a map related"""
        f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
    
        superuser = User.objects.get(pk=2)
        
        m = Map.objects.all()[0]
        ctype = ContentType.objects.get_for_model(m)

        c, created = Document.objects.get_or_create(id=1, doc_file=f,owner=superuser, 
            title='theimg', content_type=ctype, object_id=m.id)

        self.assertEquals(created, True)

    def test_document_details(self):
        """/documents/1 -> Test accessing the detail view of a document"""

        if settings.DOCUMENTS_APP:
            f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
        
            superuser = User.objects.get(pk=2)
            d, created = Document.objects.get_or_create(id=1, doc_file=f,owner=superuser, title='theimg')
            d.set_default_permissions()

            c = Client()
            response = c.get(reverse('document_detail', args=(str(d.id),)))
            self.assertEquals(response.status_code, 200)

        else: 
            pass

    def test_access_document_upload_form(self):
        """Test the form page is returned correctly via GET request /documents/upload"""
        if settings.DOCUMENTS_APP:
            c = Client()
            log = c.login(username='bobby', password='bob')
            self.assertTrue(log)
            response = c.get(reverse('document_upload'))
            self.assertTrue('Upload Documents' in response.content)
        else:
            pass

    def test_document_isuploaded(self):
        """/documents/upload -> Test uploading a document"""
        if settings.DOCUMENTS_APP:
            f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
            m = Map.objects.all()[0]        
            c = Client()
            
            c.login(username='admin', password='admin')
            response = c.post(reverse('document_upload'), data={'file': f, 'title': 'uploaded_document', 'objid': m.id, 'ctype': 'map', 
                'permissions': '{"anonymous":"document_readonly","users":[]}'},
                              follow=True)
            self.assertEquals(response.status_code, 200)
        else:
            pass
        
    # Permissions Tests

    # Users
    # - admin (pk=2)
    # - bobby (pk=1)

    # Inherited
    # - LEVEL_NONE = _none

    # Layer
    # - LEVEL_READ = document_read
    # - LEVEL_WRITE = document_readwrite
    # - LEVEL_ADMIN = document_admin
    

    # FIXME: Add a comprehensive set of permissions specifications that allow us 
    # to test as many conditions as is possible/necessary
    
    # If anonymous and/or authenticated are not specified, 
    # should set_layer_permissions remove any existing perms granted??
    
    perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","document_readwrite"]]}
    
    def test_set_document_permissions(self):
        """Verify that the set_document_permissions view is behaving as expected
        """
        f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
    
        superuser = User.objects.get(pk=2)
        document, created = Document.objects.get_or_create(id=1, doc_file=f,owner=superuser, title='theimg')
        document.set_default_permissions()
        # Get a document to work with
        document = Document.objects.all()[0]
       
        # Set the Permissions
        geonode.documents.views.document_set_permissions(document, self.perm_spec)

        # Test that the Permissions for ANONYMOUS_USERS and AUTHENTICATED_USERS were set correctly        
        self.assertEqual(document.get_gen_level(ANONYMOUS_USERS), document.LEVEL_NONE) 
        self.assertEqual(document.get_gen_level(AUTHENTICATED_USERS), document.LEVEL_NONE)

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the document owner) were removed
        users = [n for (n, p) in self.perm_spec['users']]
        levels = document.get_user_levels().exclude(user__username__in = users + [document.owner])
        self.assertEqual(len(levels), 0)
       
        # Test that the User permissions specified in the perm_spec were applied properly
        for username, level in self.perm_spec['users']:
            user = geonode.maps.models.User.objects.get(username=username)
            self.assertEqual(document.get_user_level(user), level)    

    def test_ajax_document_permissions(self):
        """Verify that the ajax_document_permissions view is behaving as expected
        """
        
        if settings.DOCUMENTS_APP:
            # Setup some document names to work with 
            f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')
        
            superuser = User.objects.get(pk=1)
            document, created = Document.objects.get_or_create(id=1, doc_file=f,owner=superuser, title='theimg')
            document.set_default_permissions()
            document_id = document.id
            invalid_document_id = 5
            
            c = Client()

            # Test that an invalid document is handled for properly
            response = c.post(reverse('document_permissions', args=(invalid_document_id,)), 
                                data=json.dumps(self.perm_spec),
                                content_type="application/json")
            self.assertEquals(response.status_code, 404) 

            # Test that POST is required
            response = c.get(reverse('document_permissions', args=(document_id,)))
            self.assertEquals(response.status_code, 405)
            
            # Test that a user is required to have documents.change_layer_permissions

            # First test un-authenticated
            response = c.post(reverse('document_permissions', args=(document_id,)), 
                                data=json.dumps(self.perm_spec),
                                content_type="application/json")
            self.assertEquals(response.status_code, 401) 

            # Next Test with a user that does NOT have the proper perms
            logged_in = c.login(username='bobby', password='bob')
            self.assertEquals(logged_in, True) 
            response = c.post(reverse('document_permissions', args=(document_id,)), 
                                data=json.dumps(self.perm_spec),
                                content_type="application/json")
            self.assertEquals(response.status_code, 401) 

            # Login as a user with the proper permission and test the endpoint
            logged_in = c.login(username='admin', password='admin')
            self.assertEquals(logged_in, True)
            response = c.post(reverse('document_permissions', args=(document_id,)), 
                                data=json.dumps(self.perm_spec),
                                content_type="application/json")

            # Test that the method returns 200         
            self.assertEquals(response.status_code, 200)
        else:
            pass
