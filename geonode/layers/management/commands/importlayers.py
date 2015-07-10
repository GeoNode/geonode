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
from geonode.people.utils import get_valid_user
import traceback
import datetime


class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            " GeoNode site.  Layers are added to the Django database, the"
            " GeoServer configuration, and the GeoNetwork metadata index.")

    args = 'path [path...]'

    option_list = BaseCommand.option_list + (
        make_option(
            '-u',
            '--user',
            dest="user",
            default=None,
            help="Name of the user account which should own the imported layers"),
        make_option(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        make_option(
            '-o',
            '--overwrite',
            dest='overwrite',
            default=False,
            action="store_true",
            help="Overwrite existing layers if discovered (defaults False)"),
        make_option(
            '-k',
            '--keywords',
            dest='keywords',
            default="",
            help="""The default keywords, separated by comma, for the
                    imported layer(s). Will be the same for all imported layers
                    if multiple imports are done in one command"""
        ),
        make_option(
            '-c',
            '--category',
            dest='category',
            default=None,
            help="""The category for the
                    imported layer(s). Will be the same for all imported layers
                    if multiple imports are done in one command"""
        ),
        make_option(
            '-r',
            '--regions',
            dest='regions',
            default="",
            help="""The default regions, separated by comma, for the
                    imported layer(s). Will be the same for all imported layers
                    if multiple imports are done in one command"""
        ),
        make_option(
            '-t',
            '--title',
            dest='title',
            default=None,
            help="""The title for the
                    imported layer(s). Will be the same for all imported layers
                    if multiple imports are done in one command"""
        ),
        make_option(
            '-p',
            '--private',
            dest='private',
            default=False,
            action="store_true",
            help="Make layer viewable only to owner"
        )
    )

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        # ignore_errors = options.get('ignore_errors')
        username = options.get('user')
        user = get_valid_user(username)
        overwrite = options.get('overwrite')
        category = options.get('category', None)
        private = options.get('private', False)
        title = options.get('title', None)

        if verbosity > 0:
            console = self.stdout
        else:
            console = None

        if overwrite:
            skip = False
        else:
            skip = True

        keywords = options.get('keywords').split(',')
        if len(keywords) == 1 and keywords[0] == '':
            keywords = []
        else:
            keywords = map(str.strip, keywords)
        regions = options.get('regions').split(',')
        if len(regions) == 1 and regions[0] == '':
            regions = []
        else:
            regions = map(str.strip, regions)
        start = datetime.datetime.now()
        output = []
        for path in args:
            out = upload(
                path,
                user=user,
                overwrite=overwrite,
                skip=skip,
                keywords=keywords,
                verbosity=verbosity,
                console=console,
                category=category,
                regions=regions,
                title=title,
                private=private)
            output.extend(out)

        updated = [dict_['file']
                   for dict_ in output if dict_['status'] == 'updated']
        created = [dict_['file']
                   for dict_ in output if dict_['status'] == 'created']
        skipped = [dict_['file']
                   for dict_ in output if dict_['status'] == 'skipped']
        failed = [dict_['file']
                  for dict_ in output if dict_['status'] == 'failed']

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
