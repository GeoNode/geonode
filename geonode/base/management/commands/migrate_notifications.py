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

from django.core.management.base import BaseCommand
from django.db import connection, IntegrityError
from django.db.utils import ProgrammingError

from pinax.notifications.models import NoticeSetting

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrate geonode-notifications settings to pinax-notifications
    """

    def has_duplicate(self, ns):
        args = dict(zip('medium send notice_type_id user_id'.split(' '), ns))
        return NoticeSetting.objects.filter(**args).exists()

    def handle(self, **options):
        c = connection.cursor()
        # check if old notifications exist
        try:
            c.execute('select medium, send, notice_type_id, user_id from notification_noticesetting;')
        except ProgrammingError as err:
            log.error(f"No table for notification app, exiting: {err}")
            # no source of data, bye!
            return

        for ns in c.fetchall():
            try:
                if self.has_duplicate(ns):
                    log.debug('settings for %s have duplicate', ns)
                    continue
                c.execute("""insert into pinax_notifications_noticesetting
                               (medium, send, notice_type_id, user_id)
                             values (%s, %s, %s, %s)""", ns)
            except IntegrityError as err:
                log.error('Cannot insert notifications for %s: %s', ns, err, exc_info=err)
