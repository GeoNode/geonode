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
    """
    This, 'sample_command', is just a fixture command to run tests.

    It needs one args, 'type', and 2 kwargs: cpair, ppair
    'type' can't be empty, while 'cpair' and 'ppair' can have max two optional
    elements.

    # TODO!! After we add commands.models.job's status update logic we should
    add code here to demonstrate how a command can ideally log commands.job
    reference or how commands.job status will be updated.
    """

    help = "A fixture command for basic tests"

    def add_arguments(self, parser):
        parser.add_argument("--cpair", nargs=2)
        parser.add_argument("--ppair", nargs=2)
        parser.add_argument("type")

    def handle(self, *args, **options):

        # Just some command process, for the sake of process/test
        if not all(isinstance(x, int) for x in options["cpair"]):
            raise CommandError("All cpair elements should be integer")

        # To test blocking/async nature.
        time.sleep(5)
