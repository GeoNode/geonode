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
from time import sleep
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'It writes "pong" to stdout.'

    def add_arguments(self, parser):
        parser.add_argument("--sleep", nargs="?", const=1, type=float)
        parser.add_argument("--force_exception", nargs="?", type=bool)

    def handle(self, *args, **options):
        if options["sleep"]:
            seconds_to_sleep = options["sleep"]
            self.stdout.write(f"Sleeping for {seconds_to_sleep} seconds...")
            sleep(seconds_to_sleep)
        if options["force_exception"]:
            self.stdout.write(
                self.style.ERROR("As requested, an exception will be raised.")
            )
            raise RuntimeError("User Requested Exception")
        self.stdout.write(self.style.SUCCESS("pong"))
