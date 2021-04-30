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

from django.core.management.base import BaseCommand
from geonode.people.utils import get_valid_user
from geonode.geoserver.helpers import gs_slurp
import traceback
import sys
import ast


class Command(BaseCommand):
    help = 'Update the GeoNode application with data from GeoServer'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'
        )
        parser.add_argument(
            '--skip-unadvertised',
            action='store_true',
            dest='skip_unadvertised',
            default=False,
            help='Skip processing unadvertised layers from GeoSever.'),
        parser.add_argument(
            '--skip-geonode-registered',
            action='store_true',
            dest='skip_geonode_registered',
            default=False,
            help='Just processing GeoServer layers still not registered in GeoNode.'),
        parser.add_argument(
            '--remove-deleted',
            action='store_true',
            dest='remove_deleted',
            default=False,
            help='Remove GeoNode layers that have been deleted from GeoSever.'),
        parser.add_argument(
            '-u',
            '--user',
            dest="user",
            default=None,
            help="Name of the user account which should own the imported layers"),
        parser.add_argument(
            '-f',
            '--filter',
            dest="filter",
            default=None,
            help="Only update data the layers that match the given filter"),
        parser.add_argument(
            '-s',
            '--store',
            dest="store",
            default=None,
            help="Only update data the layers for the given geoserver store name"),
        parser.add_argument(
            '-w',
            '--workspace',
            dest="workspace",
            default=None,
            help="Only update data on specified workspace"),
        parser.add_argument(
            '-p',
            '--permissions',
            dest="permissions",
            default=None,
            help="Permissions to apply to each layer")

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        skip_unadvertised = options.get('skip_unadvertised')
        skip_geonode_registered = options.get('skip_geonode_registered')
        remove_deleted = options.get('remove_deleted')
        verbosity = int(options.get('verbosity'))
        user = options.get('user')
        owner = get_valid_user(user)
        workspace = options.get('workspace')
        filter = options.get('filter')
        store = options.get('store')
        if not options.get('permissions'):
            permissions = None
        else:
            permissions = ast.literal_eval(options.get('permissions'))

        if verbosity > 0:
            console = sys.stdout
        else:
            console = None

        output = gs_slurp(
            ignore_errors,
            verbosity=verbosity,
            owner=owner,
            console=console,
            workspace=workspace,
            store=store,
            filter=filter,
            skip_unadvertised=skip_unadvertised,
            skip_geonode_registered=skip_geonode_registered,
            remove_deleted=remove_deleted,
            permissions=permissions,
            execute_signals=True)

        if verbosity > 1:
            print("\nDetailed report of failures:")
            for dict_ in output['layers']:
                if dict_['status'] == 'failed':
                    print("\n\n", dict_['name'], "\n================")
                    traceback.print_exception(dict_['exception_type'],
                                              dict_['error'],
                                              dict_['traceback'])
            if remove_deleted:
                print("Detailed report of layers to be deleted from GeoNode that failed:")
                for dict_ in output['deleted_layers']:
                    if dict_['status'] == 'delete_failed':
                        print("\n\n", dict_['name'], "\n================")
                        traceback.print_exception(dict_['exception_type'],
                                                  dict_['error'],
                                                  dict_['traceback'])

        if verbosity > 0:
            print("\n\nFinished processing {} layers in {} seconds.\n".format(
                len(output['layers']), round(output['stats']['duration_sec'], 2)))
            print(f"{output['stats']['created']} Created layers")
            print(f"{output['stats']['updated']} Updated layers")
            print(f"{output['stats']['failed']} Failed layers")
            try:
                duration_layer = round(
                    output['stats']['duration_sec'] * 1.0 / len(output['layers']), 2)
            except ZeroDivisionError:
                duration_layer = 0
            if len(output) > 0:
                print(f"{duration_layer} seconds per layer")
            if remove_deleted:
                print(f"\n{output['stats']['deleted']} Deleted layers")
