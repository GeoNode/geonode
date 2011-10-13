from django.core.management.base import BaseCommand
from optparse import make_option
from geonode.maps.models import Layer
import traceback
import datetime

class Command(BaseCommand):
    help = 'Update the GeoNode application with data from GeoServer'
    option_list = BaseCommand.option_list + (
        make_option('--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        )

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        verbosity = options.get('verbosity')
        start = datetime.datetime.now()
        output = Layer.objects.slurp(ignore_errors, verbosity)
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
            print "%f seconds per layer" % (duration * 1.0 / len(output))

