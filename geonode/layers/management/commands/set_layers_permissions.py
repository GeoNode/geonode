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

import copy
import logging
from argparse import RawTextHelpFormatter

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from geonode.layers.models import Dataset
from geonode.resource.manager import resource_manager
from geonode.security.permissions import PermSpec, PermSpecCompact

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

        not_found = []
        final_perms_payload = {}

        for rpk in resources_pk:
            resource = Dataset.objects.filter(pk=rpk)
            if not resource.exists():
                not_found.append(rpk)
                logger.error(f"Resource named: {rpk} not found, skipping....")
                continue
            else:
                # creating the payload from the CompactPermissions like we do in the UI.
                # the result will be a payload with the compact permissions list required
                # for the selected resource
                resource = resource.first()
                # getting the actual permissions available for the dataset
                original_perms = PermSpec(resource.get_all_level_info(), resource)
                new_perms_payload = {"organizations": [], "users": [], "groups": []}
                # if the username is specified, we add them to the payload with the compact
                # perm value
                if users_usernames:
                    User = get_user_model()
                    for _user in users_usernames:
                        try:
                            new_perms_payload["users"].append(
                                {"id": User.objects.get(username=_user).pk, "permissions": permissions_name}
                            )
                        except User.DoesNotExist:
                            logger.warning(f"The user {_user} does not exists. " "It has been skipped.")
                # GROUPS
                # if the group is specified, we add them to the payload with the compact
                # perm value
                if groups_names:
                    for group_name in groups_names:
                        try:
                            new_perms_payload["groups"].append(
                                {"id": Group.objects.get(name=group_name).pk, "permissions": permissions_name}
                            )
                        except Group.DoesNotExist:
                            logger.warning(f"The group {group_name} does not exists. " "It has been skipped.")
                # Using the compact permissions payload to calculate the permissions
                # that we want to give for each user/group
                # This part is in common with the permissions API
                new_compact_perms = PermSpecCompact(new_perms_payload, resource)
                copy_compact_perms = copy.deepcopy(new_compact_perms)

                perms_spec_compact_resource = PermSpecCompact(original_perms.compact, resource)
                perms_spec_compact_resource.merge(new_compact_perms)

                final_perms_payload = perms_spec_compact_resource.extended
                # if the delete flag is set, we must delete the permissions for the input user/group
                if delete_flag:
                    # since is a delete operation, we must remove the users/group from the resource
                    # so this will return the updated dict without the user/groups to be removed
                    final_perms_payload["users"] = {
                        _user: _perms
                        for _user, _perms in perms_spec_compact_resource.extended["users"].items()
                        if _user not in copy_compact_perms.extended["users"]
                    }
                    final_perms_payload["groups"] = {
                        _group: _perms
                        for _group, _perms in perms_spec_compact_resource.extended["groups"].items()
                        if _user not in copy_compact_perms.extended["groups"]
                    }

                # calling the resource manager to set the permissions
                resource_manager.set_permissions(resource.uuid, instance=resource, permissions=final_perms_payload)
