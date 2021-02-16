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
from unittest.mock import patch
from django.contrib.auth.models import Group

from user_messages.models import Thread, Message, GroupMemberThread
from geonode.people.models import Profile
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.messaging.notifications import message_received_notification


class TestSendEmail(GeoNodeBaseTestSupport):

    def setUp(self):
        self.p = Profile.objects.create(username='test', email='test1@test.test')
        self.p1 = Profile.objects.create(username='test1')
        self.sender = Profile.objects.create(username='sender', email='test1@test.test')

        self.t = Thread.objects.create(subject='test', )
        self.t2 = Thread.objects.create(subject='test2', )

        GroupMemberThread.objects.create(thread=self.t2, group=Group.objects.get(pk=1), user=self.p)
        GroupMemberThread.objects.create(thread=self.t2, group=Group.objects.get(pk=1), user=self.p1)

        self.m2 = Message.objects.create(content='test', thread=self.t2, sender=self.sender)
        self.m = Message.objects.create(content='test', thread=self.t, sender=self.sender)

        self.t.single_users.add(self.p)
        self.t.single_users.add(self.p1)
        self.t2.group_users.add(self.p)
        self.t2.group_users.add(self.p1)

    @patch('geonode.notifications_backend.EmailBackend.deliver')
    def test_email_sent(self, email_message):
        with self.settings(ASYNC_SIGNALS=False,
                           NOTIFICATION_ENABLED=True,
                           NOTIFICATIONS_MODULE='pinax.notifications',
                           PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            message_received_notification(message=self.m)
            email_message.assert_called_once()

    @patch('geonode.notifications_backend.EmailBackend.deliver')
    def test_email_sent_many(self, email_message):
        with self.settings(ASYNC_SIGNALS=False,
                           NOTIFICATION_ENABLED=True,
                           NOTIFICATIONS_MODULE='pinax.notifications',
                           PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.p1.email = 'test@test.test'
            self.p1.save()
            message_received_notification(message=self.m)
            self.assertEqual(email_message.call_count, 2)

    @patch('geonode.notifications_backend.EmailBackend.deliver')
    def test_email_sent_to_group(self, email_message):
        with self.settings(ASYNC_SIGNALS=False,
                           NOTIFICATION_ENABLED=True,
                           NOTIFICATIONS_MODULE='pinax.notifications',
                           PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.p1.email = 'test@test.test'
            self.p1.save()
            message_received_notification(message=self.m2)
            self.assertEqual(email_message.call_count, 2)

    @patch('geonode.notifications_backend.EmailBackend.deliver')
    def test_email_sent_to_group_single(self, email_message):
        with self.settings(ASYNC_SIGNALS=False,
                           NOTIFICATION_ENABLED=True,
                           NOTIFICATIONS_MODULE='pinax.notifications',
                           PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            message_received_notification(message=self.m2)
            self.assertEqual(email_message.call_count, 1)
