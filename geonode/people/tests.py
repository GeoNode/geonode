#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
