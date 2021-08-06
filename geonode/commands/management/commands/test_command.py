#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from django.core.management.base import BaseCommand, CommandError
import time


class Command(BaseCommand):
    """ This is just a fixture command to run basic tests """
    help = "A fixture command for basic tests"

    def add_arguments(self, parser):
        # parser.add_argument("some_ids", nargs="+", type=int)
        parser.add_argument("--cpair", nargs=2)
        parser.add_argument("--ppair", nargs=2)
        parser.add_argument("type")

    def handle(self, *args, **options):
        # PLEASE IGNORE THIS FOR NOW. THESE ARE SOME FOR SOME
        # LOCAL MANUAL TESTING WITH CELERY RUNNING
        print(args)
        print(options)

        if not all(isinstance(x, int) for x in options["cpair"]):
            raise CommandError("All cpair elements should be integer")

        time.sleep(15)
