#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from abc import ABC
from django.conf import settings


class BasePermissionsHandler(ABC):
    """
    Abstract permissions handler.
    This is the base class, all the permissions instances should
    inherit from this class.
    All the flows that touches the permissions will use this class
    (example advanced workflow)
    """

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def fixup_perms(instance, perms_payload, include_virtual, *args, **kwargs):
        return perms_payload

    @staticmethod
    def get_perms(instance, perms_payload, user, include_virtual, *args, **kwargs):
        """
        By default we dont provide any additional perms
        """
        return perms_payload


class SpecialGroupsPermissionsHandler(BasePermissionsHandler):
    """
    Adds two computed permissions to the user's permissions list for a resource:
    - can_manage_anonymous_permissions
    - can_manage_registered_member_permissions
    """

    @staticmethod
    def get_perms(instance, perms_payload, user=None, include_virtual=True, *args, **kwargs):
        from geonode.security.permissions import EDIT_PERMISSIONS

        if not include_virtual:
            return perms_payload

        perms_copy = perms_payload.copy()
        users = perms_payload.get("users", {})

        def _has_edit(perms_list, u):
            if not perms_list:
                return False
            # Basic check via explicit change permissions or ownership
            if u == instance.owner:
                return True
            edit_markers = EDIT_PERMISSIONS
            return any(p in edit_markers for p in perms_list)

        for u, perms in users.items():
            updated = set(perms or [])
            # CONDITIONS
            allow_editors_anonymous = getattr(settings, "EDITORS_CAN_MANAGE_ANONYMOUS_PERMISSIONS", True)
            allow_editors_registered = getattr(settings, "EDITORS_CAN_MANAGE_REGISTERED_MEMBERS_PERMISSIONS", True)
            is_admin_or_staff = getattr(u, "is_superuser", False) or getattr(u, "is_staff", False)
            can_edit = _has_edit(perms, u)

            grant_anonymous = is_admin_or_staff or (allow_editors_anonymous and can_edit)
            grant_registered = is_admin_or_staff or (allow_editors_registered and can_edit)

            if grant_anonymous:
                updated.add("can_manage_anonymous_permissions")
            if grant_registered:
                updated.add("can_manage_registered_member_permissions")

            perms_copy["users"][u] = list(updated)

        return perms_copy


class AdvancedWorkflowPermissionsHandler(BasePermissionsHandler):
    """
    Handler that takes care of adjusting the permissions for the advanced workflow
    """

    @staticmethod
    def fixup_perms(instance, perms_payload, include_virtual=True, *args, **kwargs):
        from geonode.security.utils import AdvancedSecurityWorkflowManager

        # Fixup Advanced Workflow permissions
        return AdvancedSecurityWorkflowManager.get_permissions(
            instance.uuid,
            instance=instance,
            permissions=perms_payload,
            created=kwargs.get("created"),
            approval_status_changed=kwargs.get("approval_status_changed"),
            group_status_changed=kwargs.get("group_status_changed"),
        )


class GroupManagersPermissionsHandler(BasePermissionsHandler):
    """
    Grants 'edit' permissions to group managers if the resource is in a group
    """

    # Define the extra permissions granted to group managers
    EXTRA_MANAGER_PERMS = [
        "change_resourcebase",
        "change_resourcebase_metadata",
        "change_dataset_data",
        "change_dataset_style",
        "change_resourcebase_permissions",
    ]

    @staticmethod
    def get_perms(instance, perms_payload, user=None, include_virtual=True, *args, **kwargs):

        from geonode.people.utils import user_is_manager_of_group

        if include_virtual:
            perms_copy = perms_payload.copy()
            users = perms_payload.get("users", {})

            for user, perms in users.items():
                # add the permissions if user is the resource's group manager and the permissions list is not empty
                if perms and user_is_manager_of_group(user, instance.group):
                    perms_copy["users"][user] = list(set(perms + GroupManagersPermissionsHandler.EXTRA_MANAGER_PERMS))

            return perms_copy

        return perms_payload
