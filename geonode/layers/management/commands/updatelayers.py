#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from optparse import make_option
from geonode.layers.models import Layer
from geonode.people.utils import get_valid_user
import traceback
import datetime

class Command(BaseCommand):
    help = 'Update the GeoNode application with data from GeoServer'
    option_list = BaseCommand.option_list + (
        make_option('-i', '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        make_option('-u', '--user', dest="user", default=None,
            help="Name of the user account which should own the imported layers"),
        )

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        verbosity = int(options.get('verbosity'))
        user = options.get('user')
        owner = get_valid_user(user)

        start = datetime.datetime.now()
        output = Layer.objects.slurp(ignore_errors, verbosity=verbosity, owner=owner)
        updated = [dict_['name'] for dict_ in output if dict_['status']=='updated']
        created = [dict_['name'] for dict_ in output if dict_['status']=='created']
        failed = [dict_['name'] for dict_ in output if dict_['status']=='failed']
        finish = datetime.datetime.now()
        td = finish - start
        duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
        duration_rounded = round(duration, 2)

        if verbosity > 1:
            print "\nDetailed report of failures:"
            for dict_ in output:
                if dict_['status'] == 'failed':
                    print "\n\n", dict_['name'], "\n================"
                    traceback.print_exception(dict_['exception_type'],
                                              dict_['error'],
                                              dict_['traceback'])

        if verbosity > 0:
            print "\n\nFinished processing %d layers in %s seconds.\n" % (
                                              len(output), duration_rounded)
            print "%d Created layers" % len(created)
            print "%d Updated layers" % len(updated)
            print "%d Failed layers" % len(failed)
            if len(output) > 0:
                print "%f seconds per layer" % (duration * 1.0 / len(output))

