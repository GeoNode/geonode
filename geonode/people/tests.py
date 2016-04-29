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

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.sites.models import Site


class PeopleTest(TestCase):

    fixtures = ('people_data.json', 'bobby.json')

    def test_forgot_username(self):
        url = reverse('forgot_username')

        # page renders
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # and responds for a bad email
        response = self.client.post(url, data={
            'email': 'foobar@doesnotexist.com'
        })
        # self.assertContains(response, "No user could be found with that email address.")

        admin = get_user_model().objects.get(username='bobby')
        response = self.client.post(url, data={
            'email': admin.email
        })
        # and sends a mail for a good one
        self.assertEqual(len(mail.outbox), 1)

        site = Site.objects.get_current()

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, "Your username for " + site.name)

    def test_account_email_sync(self):
        '''verify we can create an account and modify it keeping emails in sync'''
        from geonode.people.models import Profile

        email = 'joe@b.ob'
        joebob = Profile.objects.create(username='joebob', email=email)
        self.assertEqual(joebob.emailaddress_set.get(primary=True).email, email)

        email = 'jo@eb.ob'
        joebob.email = email
        joebob.save()
        self.assertEqual(joebob.emailaddress_set.get(primary=True).email, email)

        email = joebob.emailaddress_set.get(primary=True)
        email.email = 'j@oe.bob'
        email.save()
        joebob = Profile.objects.get(id=joebob.id)
        self.assertEqual(email.email, joebob.email)
