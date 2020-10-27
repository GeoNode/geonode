# -*- coding: utf-8 -*-
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

from django.conf import settings
from django.core.mail import send_mail

from django.core.cache import cache
from django.db import transaction
from contextlib import contextmanager

from celery.utils.log import get_task_logger

from geonode.celery_app import app

logger = get_task_logger(__name__)


@contextmanager
def memcache_lock(lock_id, oid):
    """
    ref.
     http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
    """
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, None)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if status:
            # don't release the lock if we didn't acquire it
            cache.delete(lock_id)


@app.task(
    bind=True,
    name='geonode.tasks.email.send_mail',
    queue='email',
    countdown=60,
    expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def send_email(self, *args, **kwargs):
    """
    Sends an email using django's send_mail functionality.
    """

    send_mail(*args, **kwargs)


@app.task(
    bind=True,
    name='geonode.tasks.notifications.send_queued_notifications',
    queue='email',
    countdown=60,
    expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def send_queued_notifications(self, *args):
    """Sends queued notifications.

    settings.PINAX_NOTIFICATIONS_QUEUE_ALL needs to be true in order to take
    advantage of this.

    """

    try:
        from notification.engine import send_all
    except ImportError:
        return

    # Make sure application can write to location where lock files are stored
    if not args and getattr(settings, 'NOTIFICATION_LOCK_LOCATION', None):
        send_all(settings.NOTIFICATION_LOCK_LOCATION)
    else:
        send_all(*args)


@app.task(bind=True,
          name='geonode.tasks.layers.set_permissions',
          queue='default')
def set_permissions(self, permissions_names, resources_names,
                    users_usernames, groups_names, delete_flag):
    from geonode.layers.utils import set_layers_permissions
    with transaction.atomic():
        for permissions_name in permissions_names:
            set_layers_permissions(
                permissions_name, resources_names, users_usernames, groups_names, delete_flag
            )
