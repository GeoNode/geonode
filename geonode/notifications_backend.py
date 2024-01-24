#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from django.core.mail import send_mail, get_connection, EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy

from pinax.notifications.backends.base import BaseBackend

logger = logging.getLogger(__name__)


class EmailBackend(BaseBackend):
    spam_sensitivity = 2

    def can_send(self, user, notice_type, scoping):
        can_send = super().can_send(user, notice_type, scoping)
        if can_send and user.email:
            return True
        return False

    def deliver(self, recipient, sender, notice_type, extra_context):
        context = self.default_context()
        context.update(
            {
                "recipient": recipient,
                "sender": sender,
                "notice": gettext_lazy(notice_type.display),
            }
        )
        context.update(extra_context)

        messages = self.get_formatted_messages(("short.txt", "full.txt"), notice_type.label, context)

        context.update(
            {
                "message": messages["short.txt"],
            }
        )
        subject = "".join(render_to_string("pinax/notifications/email_subject.txt", context).splitlines())

        context.update({"message": messages["full.txt"]})
        body = render_to_string("pinax/notifications/email_body.txt", context)

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                recipient.email,
            ],
            reply_to=[
                settings.DEFAULT_FROM_EMAIL,
            ],
        )
        email.content_subtype = "html"

        # TODO: require this to be passed in extra_context
        connection = get_connection()

        try:
            # Manually open the connection
            connection.open()
            connection.send_messages(
                [
                    email,
                ]
            )
            # The connection was already open so send_messages() doesn't close it.
        except Exception as e:
            logger.error(e)
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email])
            except Exception as e:
                logger.error(e)
        finally:
            # We need to manually close the connection.
            connection.close()
