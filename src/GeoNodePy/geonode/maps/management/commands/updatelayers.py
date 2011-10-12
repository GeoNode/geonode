from django.core.management.base import BaseCommand
from optparse import make_option
from geonode.maps.models import Layer


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
        output = slurp(ignore_errors, verbosity)
        updated = [dict_['name'] for dict_ in output if dict_['status']=='updated']
        created = [dict_['name'] for dict_ in output if dict_['status']=='created']
        failed = [dict_['name'] for dict_ in output if dict_['status']=='failed']
        if verbosity > 0:
            print "\n\nFinished processing.\n"
            print "%d Available layers" % len(output)
            print "%d Created layers" % len(created)
            print "%d Updated layers" % len(updated)
            print "%d Failed layers" % len(failed)
        if verbosity > 1:
            print "\nDetailed report of failures:"
            for dict_ in output:
                if dict_['status'] == 'failed':
                    print "\n=========\n"
                    print dict_['name'], dict_['error']
                    print dict_['traceback']
