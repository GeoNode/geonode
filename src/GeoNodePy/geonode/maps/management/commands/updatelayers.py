from django.core.management.base import BaseCommand
from optparse import make_option
from geonode.maps.models import Layer
from geonode.maps.utils import get_valid_user
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
        make_option('-n', '--new_only', action='store_true', dest="new_only", default=False,
            help="Only new data: no update the data already imported"),
        make_option('-w', '--workspace', dest="workspace", default=None,
            help="Only update data on specified workspace"),
        )

    args = '[layername layername ...]'

    def handle(self, *lnames, **options):
        ignore_errors = options.get('ignore_errors')
        verbosity = int(options.get('verbosity'))
        user = options.get('user')
        owner = get_valid_user(user)
        new_only = options.get('new_only')
        workspace = options.get('workspace')

        if len(lnames) == 0:
            lnames = None
            
        start = datetime.datetime.now()
        output = Layer.objects.slurp(ignore_errors, verbosity=verbosity, owner=owner, new_only=new_only, lnames=lnames, workspace=workspace)
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

