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

from celery.task import task
from django.conf import settings
from django.core.mail import send_mail


@task(name='geonode.tasks.email.send_queued_notifications', queue='email')
def send_queued_notifications(*args):
    """
    Sends queued notifications.

    settings.NOTIFICATION_QUEUE_ALL needs to be true in order to take advantage of this.
    """

    try:
        from notification.engine import send_all
    except ImportError:
        return

    # Make sure the application can write to the location where lock files are stored.
    if not args and getattr(settings, 'NOTIFICATION_LOCK_LOCATION', None):
        send_all(settings.NOTIFICATION_LOCK_LOCATION)
    else:
        send_all(*args)


@task(name='geonode.tasks.email.send_email', queue='email')
def send_email(*args, **kwargs):
    """
    Sends an email using django's send_mail functionality.
    """

    send_mail(*args, **kwargs)
