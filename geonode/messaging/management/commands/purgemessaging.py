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

from django.core.management.base import BaseCommand

from geonode.messaging.queues import queue_email_events, queue_geoserver_events, \
    queue_notifications_events, queue_all_events, \
    queue_geoserver_catalog, queue_geoserver_data, \
    queue_geoserver, queue_layer_viewers


class Command(BaseCommand):
    help = 'Start the MQ consumer to perform non blocking tasks'

    def handle(self, **options):

        queue_geoserver_events.purge()
        queue_notifications_events.purge()
        queue_email_events.purge()
        queue_all_events.purge()
        queue_geoserver_catalog.purge()
        queue_geoserver_data.purge()
        queue_geoserver.purge()
        queue_layer_viewers.purge()
