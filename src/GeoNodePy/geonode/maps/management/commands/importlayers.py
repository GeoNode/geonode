from django.core.management.base import BaseCommand
from optparse import make_option
from geonode.maps.utils import upload
import traceback
import datetime

class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            "GeoNode site.  Layers are added to the Django database, the"
            "GeoServer configuration, and the GeoNetwork metadata index.")
            
    args = 'path [path...]'

    option_list = BaseCommand.option_list + (
            make_option('--user', dest="user", default=None,
                help="Name of the user account which should own the imported layers"),
            make_option('--ignore-errors',
                action='store_true',
                dest='ignore_errors',
                default=True,
                help='Stop after any errors are encountered.'),
            make_option('--overwrite', dest='overwrite', default=True, action="store_false",
                help="Overwrite existing layers if discovered (defaults True)"),
            make_option('--keywords', dest='keywords', default="", 
                help="The default keywords for the imported layer(s). Will be the same for all imported layers if multiple imports are done in one command")
        )

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        ignore_errors = options.get('ignore_errors')
        user = options.get('user')
        overwrite = options.get('overwrite')
        keywords = options.get('keywords').split()
        start = datetime.datetime.now()
        output = []
        for path in args:
            out = upload(path, user=user, overwrite=overwrite, keywords=keywords, verbosity=verbosity)
            output.extend(out)

        updated = [dict_['file'] for dict_ in output if dict_['status']=='updated']
        created = [dict_['file'] for dict_ in output if dict_['status']=='created']
        skipped = [dict_['file'] for dict_ in output if dict_['status']=='skipped']
        failed = [dict_['file'] for dict_ in output if dict_['status']=='failed']

        finish = datetime.datetime.now()
        td = finish - start
        duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
        duration_rounded = round(duration, 2)

        if verbosity > 1:
            print "\nDetailed report of failures:"
            for dict_ in output:
                if dict_['status'] == 'failed':
                    print "\n\n", dict_['file'], "\n================"
                    traceback.print_exception(dict_['exception_type'],
                                              dict_['error'],
                                              dict_['traceback'])

        if verbosity > 0:
            print "\n\nFinished processing %d layers in %s seconds.\n" % (
                                              len(output), duration_rounded)
            print "%d Created layers" % len(created)
            print "%d Updated layers" % len(updated)
            print "%d Skipped layers" % len(skipped)
            print "%d Failed layers" % len(failed)

            if len(output) > 0:
                print "%f seconds per layer" % (duration * 1.0 / len(output))
