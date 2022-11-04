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

import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand
from geonode.layers.models import Dataset
from geonode.layers.utils import set_datasets_permissions

logger = logging.getLogger("geonode.layers.management.set_layers_permissions")


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
            "-r",
            "--resources",
            dest="resources",
            nargs="*",
            type=str,
            default=[],
            help="Resources IDs for which permissions will be assigned to. Default value: [] (all the layers will be considered). "
        )
        parser.add_argument(
            "-p",
            "--permission",
            dest="permission",
            type=str,
            default=None,
            help="Permissions to be assigned. " "Allowed values are: view, download, edit and manage.",
        )
        parser.add_argument(
            "-u",
            "--users",
            dest="users",
            nargs="*",
            type=str,
            default=[],
            help="Users for which permissions will be assigned to. "
            "Multiple choices can be typed with comma separator.",
        )
        parser.add_argument(
            "-g",
            "--groups",
            dest="groups",
            nargs="*",
            type=str,
            default=[],
            help="Groups for which permissions will be assigned to. "
            "Multiple choices can be typed with comma separator.",
        )
        parser.add_argument(
            "-d",
            "--delete",
            dest="delete_flag",
            action="store_true",
            default=False,
            help="Delete permission if it exists.",
        )

    def handle(self, *args, **options):
        # Retrieving the arguments
        permissions_name = options.get("permission").replace(" ", "")

        resources_pk = [x.replace(" ", "") for x in options.get("resources", [])]
        if resources_pk:
            resources_pk = resources_pk[0].split(",")
        else:
            resources_pk = [x for x in Dataset.objects.values_list('pk', flat=True)]

        users_usernames = [x.replace(" ", "") for x in options.get("users", [])]
        if users_usernames:
            users_usernames = users_usernames[0].split(",")

        groups_names = [x.replace(" ", "") for x in options.get("groups", [])]
        if groups_names:
            groups_names = groups_names[0].split(",")

        delete_flag = options.get("delete_flag")

        if isinstance(permissions_name, list):
            # it accept one kind of permission per request
            raise Exception("Only one permission name must be specified")

        if not users_usernames and not groups_names:
            raise Exception("Groups or Usernames must be specified")

        set_datasets_permissions(
            permissions_name,
            resources_names=resources_pk,
            users_usernames=users_usernames,
            groups_names=groups_names,
            delete_flag=delete_flag
        )
