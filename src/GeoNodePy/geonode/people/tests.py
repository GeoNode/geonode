from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail

class PeopleTest(TestCase):
    
    fixtures = ('test_data.json',)
    
    def test_forgot_username(self):
        c = Client()
        url = reverse('forgot_username')
        
        # page renders
        response = c.get(url)
        self.assertEquals(response.status_code, 200)
        
        # and responds for a bad email
        response = c.post(url,data={
            'email' : 'foobar@doesnotexist.com'
        })
        self.assertContains(response, "No user could be found with that email address.")
        
        admin = User.objects.get(username='bobby')
        response = c.post(url,data={
            'email' : admin.email
        })
        # and sends a mail for a good one
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, "Your username for " + settings.SITENAME)