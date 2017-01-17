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
from optparse import make_option
from geonode.people.utils import get_valid_user
from geonode.geoserver.helpers import gs_slurp
import traceback
import sys
import ast


class Command(BaseCommand):
    help = 'Update the GeoNode application with data from GeoServer'
    option_list = BaseCommand.option_list + (
        make_option(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        make_option(
            '--skip-unadvertised',
            action='store_true',
            dest='skip_unadvertised',
            default=False,
            help='Skip processing unadvertised layers from GeoSever.'),
        make_option(
            '--skip-geonode-registered',
            action='store_true',
            dest='skip_geonode_registered',
            default=False,
            help='Just processing GeoServer layers still not registered in GeoNode.'),
        make_option(
            '--remove-deleted',
            action='store_true',
            dest='remove_deleted',
            default=False,
            help='Remove GeoNode layers that have been deleted from GeoSever.'),
        make_option(
            '-u',
            '--user',
            dest="user",
            default=None,
            help="Name of the user account which should own the imported layers"),
        make_option(
            '-f',
            '--filter',
            dest="filter",
            default=None,
            help="Only update data the layers that match the given filter"),
        make_option(
            '-s',
            '--store',
            dest="store",
            default=None,
            help="Only update data the layers for the given geoserver store name"),
        make_option(
            '-w',
            '--workspace',
            dest="workspace",
            default=None,
            help="Only update data on specified workspace"),
        make_option(
            '-p',
            '--permissions',
            dest="permissions",
            default="None",
            help="Permissions to apply to each layer"))

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
            print "\nDetailed report of failures:"
            for dict_ in output['layers']:
                if dict_['status'] == 'failed':
                    print "\n\n", dict_['name'], "\n================"
                    traceback.print_exception(dict_['exception_type'],
                                              dict_['error'],
                                              dict_['traceback'])
            if remove_deleted:
                print "Detailed report of layers to be deleted from GeoNode that failed:"
                for dict_ in output['deleted_layers']:
                    if dict_['status'] == 'delete_failed':
                        print "\n\n", dict_['name'], "\n================"
                        traceback.print_exception(dict_['exception_type'],
                                                  dict_['error'],
                                                  dict_['traceback'])

        if verbosity > 0:
            print "\n\nFinished processing %d layers in %s seconds.\n" % (
                len(output['layers']), round(output['stats']['duration_sec'], 2))
            print "%d Created layers" % output['stats']['created']
            print "%d Updated layers" % output['stats']['updated']
            print "%d Failed layers" % output['stats']['failed']
            try:
                duration_layer = round(
                    output['stats']['duration_sec'] * 1.0 / len(output['layers']), 2)
            except ZeroDivisionError:
                duration_layer = 0
            if len(output) > 0:
                print "%f seconds per layer" % duration_layer
            if remove_deleted:
                print "\n%d Deleted layers" % output['stats']['deleted']
