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
from geonode.layers.utils import upload

class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            "GeoNode site.  Layers are added to the Django database, the"
            "GeoServer configuration, and the GeoNetwork metadata index.")
            
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
