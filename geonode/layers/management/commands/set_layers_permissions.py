#########################################################################
#
# Copyright (C) 2019 OSGeo
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
from argparse import RawTextHelpFormatter
from geonode.layers.utils import set_layers_permissions


class Command(BaseCommand):

    help = """
    Set/Unset permissions on layers for users and groups.
    Arguments:
        - users (-u, --users)
        - groups (-g, --groups)
        - resources (-r, --resources)
        - permissions (-p, --permissions)
        - delete (-d, --delete)
    At least one user or one group is required.
    If no resources are typed all the layers will be considered.
    At least one permission must be typed.
    Multiple inputs can be typed with white space separator.
    To unset permissions use the '--delete (-d)' option.
    To assign permissions to everyone (anonymous users), you will need to
    add the following options: '-u AnonymousUser -g anonymous'
    """

    def create_parser(self, *args, **kwargs):
        parser = super().create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--resources',
            dest='resources',
            nargs='*',
            type=str,
            default=None,
            help='Resources names for which permissions will be assigned to. '
                 'Default value: None (all the layers will be considered). '
                 'Multiple choices can be typed with white space separator.'
                 'A Note: names with white spaces must be typed inside quotation marks.'
        )
        parser.add_argument(
            '-p',
            '--permission',
            dest='permission',
            type=str,
            default=None,
            help='Permissions to be assigned. '
                 'Allowed values are: read (r), write (w), download (d) and owner (o).'
        )
        parser.add_argument(
            '-u',
            '--users',
            dest='users',
            nargs='*',
            type=str,
            default=None,
            help='Users for which permissions will be assigned to. '
                 'Multiple choices can be typed with white space separator.'
        )
        parser.add_argument(
            '-g',
            '--groups',
            dest='groups',
            nargs='*',
            type=str,
            default=None,
            help='Groups for which permissions will be assigned to. '
                 'Multiple choices can be typed with white space separator.'
        )
        parser.add_argument(
            '-d',
            '--delete',
            dest='delete_flag',
            action='store_true',
            default=False,
            help='Delete permission if it exists.'
        )

    def handle(self, *args, **options):
        # Retrieving the arguments
        resources_names = options.get('resources')
        permissions_name = options.get('permission')
        users_usernames = options.get('users')
        groups_names = options.get('groups')
        delete_flag = options.get('delete_flag')
        set_layers_permissions(
            permissions_name,
            resources_names,
            users_usernames,
            groups_names,
            delete_flag,
            verbose=True
        )
