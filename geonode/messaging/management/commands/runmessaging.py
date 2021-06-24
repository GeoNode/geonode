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

from geonode.messaging import connection
from geonode.messaging.consumer import Consumer

logger = logging.getLogger(__package__)
# logger.addHandler(logging.StreamHandler(sys.stdout))
# logger.setLevel(logging.DEBUG)


class Command(BaseCommand):

    help = 'Start the MQ consumer to perform non blocking tasks'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.')

    def handle(self, **options):
        with connection:
            try:
                logger.debug("Consumer starting.")
                worker = Consumer(connection)
                worker.run()
            except KeyboardInterrupt:
                logger.debug("Consumer stopped.")
