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
import logging

from django.conf import settings
from user_messages.models import Message
from user_messages.signals import message_sent

from geonode.notifications_helper import send_notification, notifications

logger = logging.getLogger(__name__)


def message_received_notification(**kwargs):
    """Send a notification when a request to a layer, map or document has
    been submitted
    """
    notice_type_label = "message_received"
    message = kwargs.get("message")
    thread = message.thread

    recipients = _get_user_to_notify(message)

    # Enable email notifications for reciepients
    if notifications:
        for user in recipients:
            notifications.models.NoticeSetting.objects.get_or_create(
                notice_type=notifications.models.NoticeType.objects.get(label=notice_type_label),
                send=True,
                user=user,
                medium=0,
            )

    ctx = {
        "message": message.content,
        "thread_subject": thread.subject,
        "sender": message.sender,
        "thread_url": settings.SITEURL + thread.get_absolute_url()[1:],
        "site_url": settings.SITEURL,
    }
    logger.debug(f"message_received_notification to: {recipients}")
    send_notification(recipients, notice_type_label, ctx)


def _get_user_to_notify(message):
    thread = message.thread
    users = thread.single_users.all() | thread.group_users.all()
    return users.exclude(username=message.sender.username).distinct()


def initialize_notification_signal():
    message_sent.connect(message_received_notification, sender=Message)
