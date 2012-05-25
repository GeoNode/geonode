from django.core.management.base import BaseCommand
from optparse import make_option
from geonode.maps.utils import upload

class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            "GeoNode site.  Layers are added to the Django database, the"
            "GeoServer configuration, and the Catalogue metadata repository.")
            
    args = 'path [path...]'

    option_list = BaseCommand.option_list + (
            make_option('--user', dest="user", default=None,
                help="Name of the user account which should own the imported layers"),
            make_option('--overwrite', dest='overwrite', default=True, action="store_false",
                help="Overwrite existing layers if discovered (defaults True)"),
            make_option('--quiet', dest='quiet', default=False, action="store_true",
                help="Don't print out a help message if invoked with an empty path list"),
            make_option('--keywords', dest='keywords', default="", 
                help="The default keywords for the imported layer(s). Will be the same for all imported layers if multiple imports are done in one command")
        )

    def handle(self, *args, **opts):
        if not opts['quiet'] and len(args) == 0:
            print "No files passed to import command... Is that what you meant to do?"
        for path in args:
            upload(path, opts['user'], opts['overwrite'], opts['keywords'].split())
