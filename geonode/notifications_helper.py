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

import logging
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.db.models import signals

from geonode.tasks.email import send_queued_notifications

E = getattr(settings, 'NOTIFICATION_ENABLED', False)
M = getattr(settings, 'NOTIFICATIONS_MODULE', None)
notifications = None

has_notifications = E and M and M in settings.INSTALLED_APPS

if has_notifications:
    notifications = import_module(M)


class NotificationsAppConfigBase(AppConfig):
    """
    Base class for AppConfig notifications setup

    You should subclass it and provide list of notifications
    in NOTIFICATIONS attribute to automatically register to
    post_migrate signal.
    """
    # override in subclass
    NOTIFICATIONS = tuple()

    def _get_logger(self):
        return logging.getLogger(self.__class__.__module__)

    def _register_notifications(self, *args, **kwargs):
        if has_notifications:
            self._get_logger().info("Creating notifications")
            for label, display, description in self.NOTIFICATIONS:
                notifications.models.NoticeType.create(label, display, description)

    def ready(self):
        signals.post_migrate.connect(self._register_notifications, sender=self)


def call_celery(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        if settings.PINAX_NOTIFICATIONS_QUEUE_ALL:
            send_queued_notifications.delay()
        return ret
    return wrap


def send_now_notification(*args, **kwargs):
    """
    Simple wrapper around notifications.model send().
    This can be called safely if notifications are not installed.
    """
    if has_notifications:
        return notifications.models.send_now(*args, **kwargs)


@call_celery
def send_notification(*args, **kwargs):
    """
    Simple wrapper around notifications.model send().
    This can be called safely if notifications are not installed.
    """
    if has_notifications:
        # queue for further processing if required
        if settings.PINAX_NOTIFICATIONS_QUEUE_ALL:
            return queue_notification(*args, **kwargs)
        return notifications.models.send(*args, **kwargs)


def queue_notification(*args, **kwargs):
    if has_notifications:
        return notifications.models.queue(*args, **kwargs)


def get_notification_recipients(notice_type_label, exclude_user=None):
    """ Get notification recipients
    """
    if not has_notifications:
        return []
    recipients_ids = notifications.models.NoticeSetting.objects \
        .filter(notice_type__label=notice_type_label) \
        .values('user')
    from geonode.people.models import Profile
    profiles = Profile.objects.filter(id__in=recipients_ids)
    if exclude_user:
        profiles.exclude(username=exclude_user.username)
    return profiles
