#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from user_messages.models import Thread, Message
from geonode.messaging.notifications import notify_thread_participants
from geonode.people.models import Profile
from geonode.tests.base import GeoNodeBaseTestSupport
from unittest.mock import patch


class TestSendEmail(GeoNodeBaseTestSupport):

    def setUp(self):
        self.p = Profile.objects.create(username='test', email='test1@test.test')
        self.p1 = Profile.objects.create(username='test1')
        self.sender = Profile.objects.create(username='sender', email='test1@test.test')
        self.t = Thread.objects.create(subject='test')
        self.t.single_users.add(self.p)
        self.t.single_users.add(self.p1)
        self.m = Message.objects.create(content='test', thread=self.t, sender=self.sender)

    @patch('django.core.mail.message.EmailMessage.send')
    def test_emails_sent(self, email_message):
        notify_thread_participants(self.t.pk, self.m.pk)
        email_message.assert_called_once()
        pass
