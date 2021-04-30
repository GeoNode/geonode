# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from django.utils import timezone
from django.core.management.base import BaseCommand
from geonode.layers.utils import upload
from geonode.people.utils import get_valid_user
import traceback
import datetime


class Command(BaseCommand):
    help = ("Brings a data file or a directory full of data files into a"
            " GeoNode site.  Layers are added to the Django database, the"
            " GeoServer configuration, and the pycsw metadata index.")

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('path', nargs='*', help='path [path...]')

        # Named (optional) arguments
        parser.add_argument(
            '-u',
            '--user',
            dest="user",
            default=None,
            help="Name of the user account which should own the imported layers")

        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.')

        parser.add_argument(
            '-o',
            '--overwrite',
            dest='overwrite',
            default=False,
            action="store_true",
            help="Overwrite existing layers if discovered (defaults False)")

        parser.add_argument(
            '-k',
            '--keywords',
            dest='keywords',
            default="",
            help=("The default keywords, separated by comma, for the imported"
                  " layer(s). Will be the same for all imported layers"
                  " if multiple imports are done in one command"))

        parser.add_argument(
            '-l',
            '--license',
            dest='license',
            default=None,
            help=("The license for the imported layer(s). Will be the same for"
                  " all imported layers if multiple imports are done"
                  " in one command"))

        parser.add_argument(
            '-c',
            '--category',
            dest='category',
            default=None,
            help=("The category for the imported layer(s). Will be the same"
                  " for all imported layers if multiple imports are done"
                  " in one command"))

        parser.add_argument(
            '-r',
            '--regions',
            dest='regions',
            default="",
            help=("The default regions, separated by comma, for the imported"
                  " layer(s). Will be the same for all imported layers if"
                  " multiple imports are done in one command"))

        parser.add_argument(
            '-n',
            '--name',
            dest='layername',
            default=None,
            help="The name for the imported layer(s). Can not be used with multiple imports")

        parser.add_argument(
            '-t',
            '--title',
            dest='title',
            default=None,
            help=("The title for the imported layer(s). Will be the same for"
                  " all imported layers if multiple imports are done"
                  " in one command"))

        parser.add_argument(
            '-a',
            '--abstract',
            dest='abstract',
            default=None,
            help=("The abstract for the imported layer(s). Will be the same for"
                  "all imported layers if multiple imports are done"
                  "in one command"))

        parser.add_argument(
            '-d',
            '--date',
            dest='date',
            default=None,
            help=('The date and time for the imported layer(s). Will be the '
                  'same for all imported layers if multiple imports are done '
                  'in one command. Use quotes to specify both the date and '
                  'time in the format \'YYYY-MM-DD HH:MM:SS\'.'))

        parser.add_argument(
            '-p',
            '--private',
            dest='private',
            default=False,
            action="store_true",
            help="Make layer viewable only to owner")

        parser.add_argument(
            '-m',
            '--metadata_uploaded_preserve',
            dest='metadata_uploaded_preserve',
            default=False,
            action="store_true",
            help="Force metadata XML to be preserved")

        parser.add_argument(
            '-C',
            '--charset',
            dest='charset',
            default='UTF-8',
            help=("Specify the charset of the data"))

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        # ignore_errors = options.get('ignore_errors')
        username = options.get('user')
        user = get_valid_user(username)
        overwrite = options.get('overwrite')
        name = options.get('layername', None)
        title = options.get('title', None)
        abstract = options.get('abstract', None)
        date = options.get('date', None)
        license = options.get('license', None)
        category = options.get('category', None)
        private = options.get('private', False)
        metadata_uploaded_preserve = options.get('metadata_uploaded_preserve',
                                                 False)
        charset = options.get('charset', 'UTF-8')

        if verbosity > 0:
            console = self.stdout
        else:
            console = None

        skip = not overwrite

        keywords = options.get('keywords').split(',')
        if len(keywords) == 1 and keywords[0] == '':
            keywords = []
        else:
            keywords = [k.strip() for k in keywords]
        regions = options.get('regions').split(',')
        if len(regions) == 1 and regions[0] == '':
            regions = []
        else:
            regions = [r.strip() for r in regions]
        start = datetime.datetime.now(timezone.get_current_timezone())
        output = []

        for path in options['path']:
            out = upload(
                path,
                user=user,
                overwrite=overwrite,
                skip=skip,
                name=name,
                title=title,
                abstract=abstract,
                date=date,
                keywords=keywords,
                verbosity=verbosity,
                console=console,
                license=license,
                category=category,
                regions=regions,
                private=private,
                metadata_uploaded_preserve=metadata_uploaded_preserve,
                charset=charset)

            output.extend(out)

        updated = [dict_['file']
                   for dict_ in output if dict_['status'] == 'updated']
        created = [dict_['file']
                   for dict_ in output if dict_['status'] == 'created']
        skipped = [dict_['file']
                   for dict_ in output if dict_['status'] == 'skipped']
        failed = [dict_['file']
                  for dict_ in output if dict_['status'] == 'failed']

        finish = datetime.datetime.now(timezone.get_current_timezone())
        td = finish - start
        duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
        duration_rounded = round(duration, 2)

        if verbosity > 1:
            print("\nDetailed report of failures:")
            for dict_ in output:
                if dict_['status'] == 'failed':
                    print("\n\n", dict_['file'], "\n================")
                    traceback.print_exception(dict_['exception_type'],
                                              dict_['error'],
                                              dict_['traceback'])

        if verbosity > 0:
            print("\n\nFinished processing {} layers in {} seconds.\n".format(
                len(output), duration_rounded))
            print("{} Created layers".format(len(created)))
            print("{} Updated layers".format(len(updated)))
            print("{} Skipped layers".format(len(skipped)))
            print("{} Failed layers".format(len(failed)))

            if len(output) > 0:
                print(f"{duration * 1.0 / len(output)} seconds per layer")
